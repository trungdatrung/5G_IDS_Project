"""Cross-validate model RF 31 feature (UNSW-NB15) trên 5G-NIDD đã ánh xạ.

Chạy sau build_5gnidd_unsw31.py:  python -I -X utf8 reports/5gnidd/eval_5gnidd.py <thư mục dự án>
Ra: reports/5gnidd/ket_qua_5gnidd.json, so_sanh_feature.csv
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
THR_DEV = 0.6949                     # ngưỡng RF 31f chọn trên UNSW test-dev, FPR <= 0,10 (NB07)
PI_TRAIN = 0.4964
R = {}

def ev(y, p, thr):
    y = np.asarray(y); pr = (p >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pr, labels=[0, 1]).ravel()
    return {'nguong': round(float(thr), 4), 'n': int(len(y)), 'pi': round(float(y.mean()), 4),
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

# ---------------------------------------------------------------- A. round-trip trên UNSW test-final
smap = pd.read_csv(BASE / 'data/cleaned/test_split_v3.csv').sort_values('test_index')
fin = (smap['split'].values != 'test_dev')
rt = pd.read_parquet(D / 'unsw_test_roundtrip.parquet')
yF = te.label.values[fin]; p_org = proba(te[fin]); p_rt = proba(rt[fin])
R['A_roundtrip_unsw_test_final'] = {'goc@0.5': ev(yF, p_org, .5), 'xap_xi@0.5': ev(yF, p_rt, .5),
                                     'goc@dev': ev(yF, p_org, THR_DEV), 'xap_xi@dev': ev(yF, p_rt, THR_DEV)}

# ---------------------------------------------------------------- B. 5G-NIDD chính: nhãn đã sửa, khử trùng lặp
g = pd.read_parquet(D / '5gnidd_unsw31.parquet'); y = g.label.values; p = proba(g)
pi_em = em_prior(p); p_em = shift(p, PI_TRAIN, pi_em)
B = {'@0.5': ev(y, p, .5), f'@{THR_DEV}': ev(y, p, THR_DEV), 'EM_prior@0.5': ev(y, p_em, .5), 'pi_em': round(pi_em, 4)}
for bs in ('BS1', 'BS2'):
    m = (g.bs == bs).values
    B[f'{bs}@0.5'] = ev(y[m], p[m], .5)
# few-shot: ngưỡng chọn trên một trạm (FPR <= 0,10), báo cáo trên trạm kia
for a, b in (('BS1', 'BS2'), ('BS2', 'BS1')):
    ma, mb = (g.bs == a).values, (g.bs == b).values
    t = thr_fpr(y[ma], p[ma]); B[f'nguong_tu_{a}->{b}'] = ev(y[mb], p[mb], t)
B['recall_theo_loai@0.5'] = by_cat(g, p, .5); B[f'recall_theo_loai@{THR_DEV}'] = by_cat(g, p, THR_DEV)
t12 = thr_fpr(y[(g.bs == 'BS1').values], p[(g.bs == 'BS1').values])
B['recall_theo_loai@nguong_BS1'] = by_cat(g[(g.bs == 'BS2').values], p[(g.bs == 'BS2').values], t12)
ben = g[y == 0]; pb = p[y == 0]
B['FPR_benign_theo_proto@0.5'] = {k: {'n': int(v.size), 'fpr': round(float((v >= .5).mean()), 4)}
                                  for k, v in pd.Series(pb, index=ben.index).groupby(ben.proto).agg(list).map(np.array).items()}
tcpb = (ben.proto == 'tcp').values
B['FPR_benign_tcp_theo_ackdat@0.5'] = {k: round(float((pb[tcpb][(cut == k).values] >= .5).mean()), 4)
                                       for cut in [pd.cut(ben.ackdat[tcpb], [-1, 0, .01, .05, 10], labels=['0', '<10ms', '10-50ms', '>50ms'])]
                                       for k in ['0', '<10ms', '10-50ms', '>50ms'] if (cut == k).any()}
R['B_5gnidd_chinh'] = B

# ---------------------------------------------------------------- C. biến thể ánh xạ thô (cùng các dòng)
r = pd.read_parquet(D / '5gnidd_unsw31_raw.parquet'); pr_ = proba(r)
R['C_anh_xa_tho'] = {'@0.5': ev(r.label.values, pr_, .5), f'@{THR_DEV}': ev(r.label.values, pr_, THR_DEV)}

# ---------------------------------------------------------------- D. nhãn công bố, không khử trùng lặp (giống bài báo)
full = pd.read_parquet(D / '5gnidd_unsw31_full.parquet'); pf = proba(full)
R['D_nhan_cong_bo_khong_khu_trung'] = {'@0.5': ev(full.label_published.values, pf, .5),
                                       'chi_rieng_281529_ban_sao_nhan_Benign': {
                                           'ty_le_model_bao_Attack@0.5': round(float((pf[full.dup_capture.values] >= .5).mean()), 4)}}

# ---------------------------------------------------------------- F. chẩn đoán: feature nào làm hỏng chuyển giao
# Thay MỘT feature bằng trung vị (số) / mode (phân loại) của UNSW-train, không dùng nhãn; mẫu 60k phân tầng theo loại.
smp = g.groupby('attack_cat', group_keys=False).apply(lambda d: d.sample(min(len(d), 8000), random_state=42))
ys = smp.label.values; base_auc = roc_auc_score(ys, proba(smp))
diag = []
for c in FEATS:
    v = tr[c].astype(str).mode()[0] if c in CATS else float(tr[c].astype('float64').median())
    ps = proba(smp.assign(**{c: v}))
    diag.append({'feature': c, 'gia_tri_thay': v, 'roc_auc_sau_thay': round(roc_auc_score(ys, ps), 4),
                 'delta_roc_auc': round(roc_auc_score(ys, ps) - base_auc, 4)})
diag = pd.DataFrame(diag).sort_values('delta_roc_auc', ascending=False)
diag.to_csv(REP / 'chan_doan_feature.csv', index=False, encoding='utf-8-sig')
R['F_chan_doan'] = {'roc_auc_mau': round(base_auc, 4), 'theo_feature': diag.to_dict('records')}
ct1 = proba(smp.assign(ct_src_ltm=1.0, ct_src_dport_ltm=1.0))
R['F_chan_doan']['ct_ca_hai_bang_1'] = round(roc_auc_score(ys, ct1), 4)

# ---------------------------------------------------------------- E. so sánh phân bố từng feature
U = pd.concat([tr, te], ignore_index=True)
rows = []
for c in FEATS:
    if c in CATS:
        seen = set(tr[c].astype(str))
        rows.append({'feature': c, 'loai': 'phan_loai',
                     'UNSW_top': str(U[c].astype(str).value_counts(normalize=True).head(4).round(3).to_dict()),
                     '5G_top': str(g[c].astype(str).value_counts(normalize=True).head(4).round(3).to_dict()),
                     'ty_le_5G_gia_tri_chua_gap_trong_UNSW': round(float((~g[c].astype(str).isin(seen)).mean()), 4)})
        continue
    un, ua = U.loc[U.label == 0, c].astype('float64'), U.loc[U.label == 1, c].astype('float64')
    gn, ga = g.loc[g.label == 0, c].astype('float64'), g.loc[g.label == 1, c].astype('float64')
    q = lambda s: f'{s.median():.4g} / {s.quantile(.9):.4g}'
    rows.append({'feature': c, 'loai': 'so', 'UNSW_Normal_q50/q90': q(un), 'UNSW_Attack_q50/q90': q(ua),
                 '5G_Benign_q50/q90': q(gn), '5G_Attack_q50/q90': q(ga),
                 'KS_Normal_UNSW_vs_Benign_5G': round(ks_2samp(un, gn).statistic, 4),
                 'KS_Attack_UNSW_vs_Attack_5G': round(ks_2samp(ua, ga).statistic, 4),
                 'ty_le_5G_ngoai_khoang_UNSW': round(float(((g[c] < U[c].min()) | (g[c] > U[c].max())).mean()), 4)})
cmp = pd.DataFrame(rows); cmp.to_csv(REP / 'so_sanh_feature.csv', index=False, encoding='utf-8-sig')
R['E_so_sanh_feature'] = cmp.to_dict('records')
json.dump(R, open(REP / 'ket_qua_5gnidd.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in R.items() if k != 'E_so_sanh_feature'}, ensure_ascii=False, indent=1))
print(cmp.to_string())
