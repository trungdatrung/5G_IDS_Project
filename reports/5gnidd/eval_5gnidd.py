"""Cross-validate the RF 31-feature model (UNSW-NB15) on the mapped 5G-NIDD data.

Run after build_5gnidd_unsw31.py:  python -I -X utf8 reports/5gnidd/eval_5gnidd.py <project directory>
Output: reports/5gnidd/results_5gnidd.json, feature_comparison.csv
"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd, joblib
from scipy.stats import ks_2samp
from sklearn.metrics import (roc_auc_score, average_precision_score, balanced_accuracy_score, matthews_corrcoef,
                             confusion_matrix, roc_curve)

BASE = Path(sys.argv[1]); REP = BASE / 'reports/5gnidd'; D = BASE / 'data/5gnidd/cleaned'
CATS = ['proto', 'service', 'state']
model = joblib.load(BASE / 'reports/exp05/rf_A_trainfit.joblib')
tr = pd.read_parquet(BASE / 'data/cleaned/UNSW_NB15_training-set.parquet')
te = pd.read_parquet(BASE / 'data/cleaned/UNSW_NB15_testing-set.parquet')
FEATS = [c for c in tr.columns if c not in ('label', 'attack_cat')]
X_of = lambda d: d[FEATS].astype({c: str for c in CATS}).astype({c: 'float64' for c in FEATS if c not in CATS})
proba = lambda d: model.predict_proba(X_of(d))[:, 1]
THR_DEV = 0.6949                     # RF 31f threshold chosen on UNSW test-dev, FPR <= 0.10 (NB07)
PI_TRAIN = 0.4964
R = {}

def ev(y, p, thr):
    y = np.asarray(y); pr = (p >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pr, labels=[0, 1]).ravel()
    return {'threshold': round(float(thr), 4), 'n': int(len(y)), 'pi': round(float(y.mean()), 4),
            'roc_auc': round(roc_auc_score(y, p), 4), 'pr_auc': round(average_precision_score(y, p), 4),
            'accuracy': round((tp + tn) / len(y), 4), 'balanced_acc': round(balanced_accuracy_score(y, pr), 4),
            'mcc': round(matthews_corrcoef(y, pr), 4), 'precision': round(tp / max(tp + fp, 1), 4),
            'recall': round(tp / max(tp + fn, 1), 4), 'fpr': round(fp / max(fp + tn, 1), 4),
            'TN': int(tn), 'FP': int(fp), 'FN': int(fn), 'TP': int(tp)}

def thr_fpr(y, p, fmax=0.10):
    fpr, tpr, th = roc_curve(y, p)
    return float(min(th[int(np.argmax(np.where(fpr <= fmax, tpr, -1.0)))], 1.0))

def em_prior(p, pi_src=PI_TRAIN, iters=500):
    pi = pi_src
    for _ in range(iters):
        r = (p * pi / pi_src) / (p * pi / pi_src + (1 - p) * (1 - pi) / (1 - pi_src)); new = float(r.mean())
        if abs(new - pi) < 1e-10: break
        pi = new
    return pi

def shift(p, a, b):
    x, y = b / a, (1 - b) / (1 - a); return p * x / (p * x + (1 - p) * y)

def by_cat(d, p, thr):
    return {c: round(float((p[(d.attack_cat == c).values] >= thr).mean()), 4) for c in sorted(d.attack_cat.unique())}

# ---------------------------------------------------------------- A. round-trip on UNSW test-final
smap = pd.read_csv(BASE / 'data/cleaned/test_split_v3.csv').sort_values('test_index')
fin = (smap['split'].values != 'test_dev')
rt = pd.read_parquet(D / 'unsw_test_roundtrip.parquet')
yF = te.label.values[fin]; p_org = proba(te[fin]); p_rt = proba(rt[fin])
R['A_roundtrip_unsw_test_final'] = {'original@0.5': ev(yF, p_org, .5), 'approx@0.5': ev(yF, p_rt, .5),
                                     'original@dev': ev(yF, p_org, THR_DEV), 'approx@dev': ev(yF, p_rt, THR_DEV)}

# ---------------------------------------------------------------- B. main 5G-NIDD: labels fixed, deduplicated
g = pd.read_parquet(D / '5gnidd_unsw31.parquet'); y = g.label.values; p = proba(g)
pi_em = em_prior(p); p_em = shift(p, PI_TRAIN, pi_em)
B = {'@0.5': ev(y, p, .5), f'@{THR_DEV}': ev(y, p, THR_DEV), 'EM_prior@0.5': ev(y, p_em, .5), 'pi_em': round(pi_em, 4)}
for bs in ('BS1', 'BS2'):
    m = (g.bs == bs).values
    B[f'{bs}@0.5'] = ev(y[m], p[m], .5)
# few-shot: threshold tuned on one station (FPR <= 0.10), reported on the other
for a, b in (('BS1', 'BS2'), ('BS2', 'BS1')):
    ma, mb = (g.bs == a).values, (g.bs == b).values
    t = thr_fpr(y[ma], p[ma]); B[f'threshold_from_{a}->{b}'] = ev(y[mb], p[mb], t)
B['recall_by_category@0.5'] = by_cat(g, p, .5); B[f'recall_by_category@{THR_DEV}'] = by_cat(g, p, THR_DEV)
t12 = thr_fpr(y[(g.bs == 'BS1').values], p[(g.bs == 'BS1').values])
B['recall_by_category@threshold_BS1'] = by_cat(g[(g.bs == 'BS2').values], p[(g.bs == 'BS2').values], t12)
ben = g[y == 0]; pb = p[y == 0]
B['FPR_benign_by_proto@0.5'] = {k: {'n': int(v.size), 'fpr': round(float((v >= .5).mean()), 4)}
                                  for k, v in pd.Series(pb, index=ben.index).groupby(ben.proto).agg(list).map(np.array).items()}
tcpb = (ben.proto == 'tcp').values
B['FPR_benign_tcp_by_ackdat@0.5'] = {k: round(float((pb[tcpb][(cut == k).values] >= .5).mean()), 4)
                                       for cut in [pd.cut(ben.ackdat[tcpb], [-1, 0, .01, .05, 10], labels=['0', '<10ms', '10-50ms', '>50ms'])]
                                       for k in ['0', '<10ms', '10-50ms', '>50ms'] if (cut == k).any()}
R['B_5gnidd_main'] = B

# ---------------------------------------------------------------- C. raw mapping variant (same rows)
r = pd.read_parquet(D / '5gnidd_unsw31_raw.parquet'); pr_ = proba(r)
R['C_raw_mapping'] = {'@0.5': ev(r.label.values, pr_, .5), f'@{THR_DEV}': ev(r.label.values, pr_, THR_DEV)}

# ---------------------------------------------------------------- D. published labels, not deduplicated (as in the paper)
full = pd.read_parquet(D / '5gnidd_unsw31_full.parquet'); pf = proba(full)
R['D_published_labels_no_dedup'] = {'@0.5': ev(full.label_published.values, pf, .5),
                                       'only_281529_mislabeled_benign_duplicates': {
                                           'model_attack_rate@0.5': round(float((pf[full.dup_capture.values] >= .5).mean()), 4)}}

# ---------------------------------------------------------------- F. diagnosis: which feature breaks transfer
# Replace ONE feature with the median (numeric) / mode (categorical) of UNSW-train, without using labels; 60k sample stratified by category.
smp = g.groupby('attack_cat', group_keys=False).apply(lambda d: d.sample(min(len(d), 8000), random_state=42))
ys = smp.label.values; base_auc = roc_auc_score(ys, proba(smp))
diag = []
for c in FEATS:
    v = tr[c].astype(str).mode()[0] if c in CATS else float(tr[c].astype('float64').median())
    ps = proba(smp.assign(**{c: v}))
    diag.append({'feature': c, 'replacement_value': v, 'roc_auc_after_replace': round(roc_auc_score(ys, ps), 4),
                 'delta_roc_auc': round(roc_auc_score(ys, ps) - base_auc, 4)})
diag = pd.DataFrame(diag).sort_values('delta_roc_auc', ascending=False)
diag.to_csv(REP / 'diagnose_feature.csv', index=False, encoding='utf-8-sig')
R['F_diagnosis'] = {'roc_auc_sample': round(base_auc, 4), 'by_feature': diag.to_dict('records')}
ct1 = proba(smp.assign(ct_src_ltm=1.0, ct_src_dport_ltm=1.0))
R['F_diagnosis']['ct_both_set_to_1'] = round(roc_auc_score(ys, ct1), 4)

# ---------------------------------------------------------------- E. compare the distribution of each feature
U = pd.concat([tr, te], ignore_index=True)
rows = []
for c in FEATS:
    if c in CATS:
        seen = set(tr[c].astype(str))
        rows.append({'feature': c, 'type': 'categorical',
                     'UNSW_top': str(U[c].astype(str).value_counts(normalize=True).head(4).round(3).to_dict()),
                     '5G_top': str(g[c].astype(str).value_counts(normalize=True).head(4).round(3).to_dict()),
                     'pct_5g_values_unseen_in_unsw': round(float((~g[c].astype(str).isin(seen)).mean()), 4)})
        continue
    un, ua = U.loc[U.label == 0, c].astype('float64'), U.loc[U.label == 1, c].astype('float64')
    gn, ga = g.loc[g.label == 0, c].astype('float64'), g.loc[g.label == 1, c].astype('float64')
    q = lambda s: f'{s.median():.4g} / {s.quantile(.9):.4g}'
    rows.append({'feature': c, 'type': 'numeric', 'UNSW_Normal_q50/q90': q(un), 'UNSW_Attack_q50/q90': q(ua),
                 '5G_Benign_q50/q90': q(gn), '5G_Attack_q50/q90': q(ga),
                 'KS_Normal_UNSW_vs_Benign_5G': round(ks_2samp(un, gn).statistic, 4),
                 'KS_Attack_UNSW_vs_Attack_5G': round(ks_2samp(ua, ga).statistic, 4),
                 'pct_5g_outside_unsw_range': round(float(((g[c] < U[c].min()) | (g[c] > U[c].max())).mean()), 4)})
cmp = pd.DataFrame(rows); cmp.to_csv(REP / 'feature_comparison.csv', index=False, encoding='utf-8-sig')
R['E_feature_comparison'] = cmp.to_dict('records')
json.dump(R, open(REP / 'results_5gnidd.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in R.items() if k != 'E_feature_comparison'}, ensure_ascii=False, indent=1))
print(cmp.to_string())
