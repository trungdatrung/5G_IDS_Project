"""Step 2 — Train notebook 07's binary RF and multiclass RF on 5G-NIDD, evaluate, and cross-validate against UNSW-NB15.

Run :  python -I -X utf8 experiment_5gnidd/src/02_train_evaluate.py <project_dir>      (QUICK=1 to run 40 trees)
In  :  experiment_5gnidd/data/cleaned/5gnidd_unsw31.parquet   (produced by step 1)
       data/cleaned/UNSW_NB15_{training,testing}-set.parquet, data/cleaned/test_split_v3.csv   (READ-ONLY)
Out :  experiment_5gnidd/results/*   (json, csv, png),  experiment_5gnidd/models/*.joblib

Model, hyperparameters, metrics, and thresholding rule are taken AS-IS from notebooks/07_Consolidated_Rerun.ipynb (Cells 0, 1.2, 6.1):
  RF 300 trees, max_depth=20, max_features=0.5, max_samples=0.7, seed 42; OneHot for proto/service/state
  Binary RF: trained on `label`;  multiclass RF: trained on `attack_cat`, binary score = 1 - P(benign class)
  Operating threshold: maximize Recall with FPR <= 0.10, chosen on test-dev, reported on test-final.
Experiments:
  E1  In-domain on 5G-NIDD (split into 4 sets as in NB07)
  E2  Sensitivity: drop ct_src_ltm / ct_src_dport_ltm (2 features that depend on row order)
  E3  Cross-station: train BS1 -> test BS2 and vice versa
  E4  Cross-dataset: UNSW model -> 5G test-final, 5G model -> UNSW test-final
"""
import os, sys, json, time, warnings
from pathlib import Path
import numpy as np, pandas as pd, joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, average_precision_score, confusion_matrix, matthews_corrcoef,
                             roc_curve, precision_recall_fscore_support)
warnings.filterwarnings('ignore')

BASE = Path(sys.argv[1])
EXP = BASE / 'experiment_5gnidd'
RES, MOD, FIG = EXP / 'results', EXP / 'models', EXP / 'results/figures'
for p in (RES, MOD, FIG):
    p.mkdir(parents=True, exist_ok=True)

QUICK = os.environ.get('QUICK') == '1'
RS = 42
N_TREES = 40 if QUICK else 300
RF_PARAMS = dict(n_estimators=N_TREES, max_depth=20, max_features=0.5, max_samples=0.7,
                 min_samples_leaf=1, class_weight=None, random_state=RS, n_jobs=-1)
CATS = ['proto', 'service', 'state']
FPR_MAX = 0.10
CT = ['ct_src_ltm', 'ct_src_dport_ltm']
R = {'mode': f'{"QUICK" if QUICK else "FULL"} | {N_TREES} trees | seed {RS}'}

def log(k, v):
    R[k] = v
    print(f'[{time.strftime("%H:%M:%S")}] {k}')
    return v

# ---------------------------------------------------------------- functions from NB07 (Cell 1.2), unchanged
def X_of(df, cols):
    return df[cols].astype({c: str for c in CATS if c in cols})

def rf_pipe(cols):
    pre = ColumnTransformer([('cat', OneHotEncoder(handle_unknown='ignore'), [c for c in CATS if c in cols])],
                            remainder='passthrough', verbose_feature_names_out=False, sparse_threshold=0.3)
    return Pipeline([('pre', pre), ('clf', RandomForestClassifier(**RF_PARAMS))])

def ev(y, proba, thr=0.5):
    y = np.asarray(y)
    pred = (proba >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    one = len(np.unique(y)) > 1
    return dict(threshold=round(float(thr), 4), n=int(len(y)), attack_rate_test=round(float(y.mean()), 4),
                accuracy=accuracy_score(y, pred), balanced_acc=balanced_accuracy_score(y, pred),
                mcc=matthews_corrcoef(y, pred), precision=precision_score(y, pred, zero_division=0),
                recall=recall_score(y, pred, zero_division=0), f1=f1_score(y, pred, zero_division=0),
                fpr=fp / max(fp + tn, 1),
                roc_auc=roc_auc_score(y, proba) if one else np.nan,
                pr_auc=average_precision_score(y, proba) if one else np.nan,
                TN=int(tn), FP=int(fp), FN=int(fn), TP=int(tp))

def thr_fpr(y, proba, fmax=FPR_MAX):
    fpr, tpr, th = roc_curve(y, proba)
    j = int(np.argmax(np.where(fpr <= fmax, tpr, -1.0)))
    return float(min(th[j], 1.0))

# ---------------------------------------------------------------- multiclass metrics + confusion matrix
def ev_multi(y, pred, classes):
    p, r, f, s = precision_recall_fscore_support(y, pred, labels=classes, zero_division=0)
    per = pd.DataFrame({'precision': p, 'recall': r, 'f1': f, 'support': s}, index=classes)
    summary = dict(n=int(len(y)), accuracy=accuracy_score(y, pred), balanced_acc=balanced_accuracy_score(y, pred),
                mcc=matthews_corrcoef(y, pred),
                macro_precision=float(p.mean()), macro_recall=float(r.mean()), macro_f1=float(f.mean()),
                weighted_f1=f1_score(y, pred, labels=classes, average='weighted', zero_division=0))
    return summary, per

def save_cm(cm_df, name, title):
    cm_df.to_csv(RES / f'{name}.csv', encoding='utf-8-sig')
    cm = cm_df.values.astype(float)
    rown = cm / np.maximum(cm.sum(1, keepdims=True), 1)
    k = max(len(cm_df.columns), len(cm_df.index))
    fig, ax = plt.subplots(figsize=(1.1 * len(cm_df.columns) + 3, 0.75 * len(cm_df.index) + 2.2))
    ax.imshow(rown, cmap='Blues', vmin=0, vmax=1, aspect='auto')
    ax.set_xticks(range(cm.shape[1])); ax.set_xticklabels(cm_df.columns, rotation=40, ha='right', fontsize=9)
    ax.set_yticks(range(cm.shape[0])); ax.set_yticklabels(cm_df.index, fontsize=9)
    ax.set_xlabel(cm_df.columns.name or 'Predicted'); ax.set_ylabel(cm_df.index.name or 'Actual')
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, f'{int(cm[i, j]):,}\n{rown[i, j]:.1%}'.replace(',', '.'), ha='center', va='center',
                    fontsize=7 if k > 6 else 9, color='white' if rown[i, j] > 0.55 else 'black')
    ax.set_title(title, fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / f'{name}.png', dpi=130); plt.close(fig)

def cm_bin(y, proba, thr, name, title):
    pred = (proba >= thr).astype(int)
    cm = pd.DataFrame(confusion_matrix(y, pred, labels=[0, 1]),
                      index=pd.Index(['Benign/Normal', 'Attack'], name='Actual'),
                      columns=pd.Index(['Benign/Normal', 'Attack'], name='Predicted'))
    save_cm(cm, name, title)
    return cm.values.tolist()

def cm_multi(y, pred, rows, cols, name, title):
    cm = pd.crosstab(pd.Series(y, name='Actual'), pd.Series(pred, name='Predicted')).reindex(index=rows, columns=cols, fill_value=0)
    save_cm(cm, name, title)
    return cm

def recall_by_cat(cat, proba, thr):
    s = pd.Series(proba >= thr).groupby(np.asarray(cat)).agg(['mean', 'size'])
    return {k: {'attack_rate': round(float(v['mean']), 4), 'n': int(v['size'])} for k, v in s.iterrows()}

def importance(pipe, cols):
    names = pipe.named_steps['pre'].get_feature_names_out()
    imp = pd.Series(pipe.named_steps['clf'].feature_importances_, index=names)
    grp = {n: next((c for c in CATS if n.startswith(c + '_')), n) for n in names}
    return imp.groupby(grp).sum().reindex(cols).sort_values(ascending=False)

def fit(df, cols, target):
    t = time.time()
    m = rf_pipe(cols).fit(X_of(df, cols), df[target].astype(str).values if target == 'attack_cat' else df[target].values)
    print(f'    fit {time.time() - t:5.0f}s | {target} | {len(df):,} rows | {len(cols)} feature')
    return m

def score_attack(mc, df, cols, benign):
    i = list(mc.classes_).index(benign)
    return 1.0 - mc.predict_proba(X_of(df, cols))[:, i]

# ================================================================ data
g = pd.read_parquet(EXP / 'data/cleaned/5gnidd_unsw31.parquet')
tr_u = pd.read_parquet(BASE / 'data/cleaned/UNSW_NB15_training-set.parquet')
te_u = pd.read_parquet(BASE / 'data/cleaned/UNSW_NB15_testing-set.parquet')
FEATS = [c for c in tr_u.columns if c not in ('label', 'attack_cat')]
assert list(g.columns[:31]) == FEATS
for c in CATS:
    g[c] = g[c].astype(str)
NO_CT = [c for c in FEATS if c not in CT]
C5 = sorted(g.attack_cat.unique(), key=lambda c: (c != 'Benign', c))          # Benign first
CU = ['Normal'] + sorted(c for c in tr_u.attack_cat.astype(str).unique() if c != 'Normal')

# 5G: split into 4 sets following NB07's exact structure (train-fit / validation / test-dev / test-final), stratified by attack_cat
i_tr, i_te = train_test_split(g.index, test_size=0.30, stratify=g.attack_cat, random_state=RS)
i_fit, i_val = train_test_split(i_tr, test_size=0.20, stratify=g.attack_cat[i_tr], random_state=RS)
i_dev, i_fin = train_test_split(i_te, test_size=0.50, stratify=g.attack_cat[i_te], random_state=RS)
split = pd.Series('', index=g.index)
split[i_fit], split[i_val], split[i_dev], split[i_fin] = 'train-fit', 'validation', 'test-dev', 'test-final'
pd.DataFrame({'row': g.index, 'split': split.values, 'bs': g.bs, 'attack_cat': g.attack_cat}).to_csv(
    RES / 'split_5g.csv', index=False)
TR, VAL, DEV, FIN = (g.loc[i] for i in (i_fit, i_val, i_dev, i_fin))
log('split_5g', {k: {'n': len(d), 'attack_ratio': round(float(d.label.mean()), 4)}
                    for k, d in [('train-fit', TR), ('validation', VAL), ('test-dev', DEV), ('test-final', FIN)]})

# UNSW: reproduce NB07's exact 4 sets (Cell 1.1)
smap = pd.read_csv(BASE / 'data/cleaned/test_split_v3.csv').sort_values('test_index')
is_dev = (smap['split'].values == 'test_dev')
U_DEV, U_FIN = te_u[is_dev].copy(), te_u[~is_dev].copy()
u_fit, u_val = train_test_split(tr_u.index, test_size=0.2, stratify=tr_u['label'], random_state=RS)
U_TR = tr_u.loc[u_fit].copy()
for d in (U_TR, U_DEV, U_FIN):
    for c in CATS + ['attack_cat']:
        d[c] = d[c].astype(str)
assert [len(U_TR), len(U_DEV), len(U_FIN)] == [79147, 25283, 25284]

# ================================================================ E1. in-domain 5G-NIDD
print('E1 — in-domain 5G-NIDD')
rf_b = fit(TR, FEATS, 'label')
P = {k: rf_b.predict_proba(X_of(d, FEATS))[:, 1] for k, d in [('val', VAL), ('dev', DEV), ('fin', FIN)]}
thr_b = thr_fpr(DEV.label.values, P['dev'])
E1b = {'validation@0.5': ev(VAL.label, P['val']), 'test-dev@0.5': ev(DEV.label, P['dev']),
       'test-final@0.5': ev(FIN.label, P['fin']), f'test-final@dev_threshold': ev(FIN.label, P['fin'], thr_b),
       'dev_threshold_FPR<=0.10': thr_b,
       'attack_rate_by_class_test-final@0.5': recall_by_cat(FIN.attack_cat, P['fin'], .5),
       'cm_test-final@0.5': cm_bin(FIN.label.values, P['fin'], .5, 'cm_E1_rf_binary_5g_test-final',
                                   'E1 · binary RF · 5G-NIDD test-final @0.5'),
       'importance': importance(rf_b, FEATS).round(5).to_dict()}
log('E1_rf_binary', E1b)

rf_m = fit(TR, FEATS, 'attack_cat')
PM = {k: rf_m.predict(X_of(d, FEATS)) for k, d in [('val', VAL), ('dev', DEV), ('fin', FIN)]}
SM = {k: score_attack(rf_m, d, FEATS, 'Benign') for k, d in [('dev', DEV), ('fin', FIN)]}
thr_m = thr_fpr(DEV.label.values, SM['dev'])
summary_val, _ = ev_multi(VAL.attack_cat.values, PM['val'], C5)
summary_fin, per_fin = ev_multi(FIN.attack_cat.values, PM['fin'], C5)
per_fin.to_csv(RES / 'E1_rf_multiclass_5g_test-final_by_class.csv', encoding='utf-8-sig')
cmm = cm_multi(FIN.attack_cat.values, PM['fin'], C5, C5, 'cm_E1_rf_multiclass_5g_test-final',
               'E1 · multiclass RF · 5G-NIDD test-final (9 classes)')
E1m = {'validation_multiclass': summary_val, 'test-final_multiclass': summary_fin, 'test-final_by_class': per_fin.round(4).to_dict('index'),
       'binary_1-P(Benign)_test-final@0.5': ev(FIN.label, SM['fin']),
       'binary_1-P(Benign)_test-final@dev_threshold': ev(FIN.label, SM['fin'], thr_m), 'dev_threshold_FPR<=0.10': thr_m,
       'cm_test-final': cmm.values.tolist(), 'cm_classes': C5,
       'cm_binary_test-final@0.5': cm_bin(FIN.label.values, SM['fin'], .5, 'cm_E1_rf_multiclass_binary_5g_test-final',
                                            'E1 · multiclass RF → binary 1−P(Benign) · test-final @0.5')}
log('E1_rf_multiclass', E1m)
joblib.dump(rf_b, MOD / 'rf_binary_5g.joblib', compress=3)
joblib.dump(rf_m, MOD / 'rf_multiclass_5g.joblib', compress=3)

# ================================================================ E2. sensitivity: drop the 2 ct_* features (depend on row order within the file)
print('E2 — dropping ct_src_ltm, ct_src_dport_ltm')
rf_b2 = fit(TR, NO_CT, 'label')
p2d, p2f = (rf_b2.predict_proba(X_of(d, NO_CT))[:, 1] for d in (DEV, FIN))
t2 = thr_fpr(DEV.label.values, p2d)
rf_m2 = fit(TR, NO_CT, 'attack_cat')
summary2, per2 = ev_multi(FIN.attack_cat.values, rf_m2.predict(X_of(FIN, NO_CT)), C5)
log('E2_no_ct', {'rf_binary_test-final@0.5': ev(FIN.label, p2f), 'rf_binary_test-final@dev_threshold': ev(FIN.label, p2f, t2),
                    'rf_multiclass_test-final': summary2, 'rf_multiclass_by_class': per2.round(4).to_dict('index')})

# ================================================================ E3. cross-station
print('E3 — cross-station BS1 ↔ BS2')
E3 = {}
for a, b in (('BS1', 'BS2'), ('BS2', 'BS1')):
    src, dst = g[g.bs == a], g[g.bs == b]
    s_fit, s_hold = train_test_split(src.index, test_size=0.20, stratify=src.attack_cat, random_state=RS)
    for tag, cols in (('31f', FEATS), ('no_ct', NO_CT)):
        mb = fit(g.loc[s_fit], cols, 'label')
        ph, pt = mb.predict_proba(X_of(g.loc[s_hold], cols))[:, 1], mb.predict_proba(X_of(dst, cols))[:, 1]
        t = thr_fpr(g.loc[s_hold, 'label'].values, ph)
        mm = fit(g.loc[s_fit], cols, 'attack_cat')
        pm = mm.predict(X_of(dst, cols))
        summary, per = ev_multi(dst.attack_cat.values, pm, C5)
        r = {'rf_binary@0.5': ev(dst.label, pt), 'rf_binary@source_station_threshold': ev(dst.label, pt, t),
             'source_station_threshold': t, 'attack_rate_by_class@0.5': recall_by_cat(dst.attack_cat, pt, .5),
             'rf_multiclass': summary, 'rf_multiclass_by_class': per.round(4).to_dict('index'),
             'classes_in_target_missing_from_source': sorted(set(dst.attack_cat) - set(src.attack_cat))}
        if tag == '31f':
            r['cm_binary@0.5'] = cm_bin(dst.label.values, pt, .5, f'cm_E3_rf_binary_{a}_to_{b}',
                                          f'E3 · binary RF · train {a} → test {b} @0.5')
            cm_multi(dst.attack_cat.values, pm, C5, C5, f'cm_E3_rf_multiclass_{a}_to_{b}', f'E3 · multiclass RF · train {a} → test {b}')
        E3[f'{a}->{b}|{tag}'] = r
log('E3_cross_station', E3)

# ================================================================ E4. cross-dataset
print('E4 — cross-dataset UNSW ↔ 5G')
u_b = fit(U_TR, FEATS, 'label')
acc0 = accuracy_score(U_FIN.label, u_b.predict_proba(X_of(U_FIN, FEATS))[:, 1] >= .5)
if not QUICK:
    assert abs(acc0 - 0.818620) < 5e-4, acc0                                      # matches NB07's 31-feature RF model
u_thr = thr_fpr(U_DEV.label.values, u_b.predict_proba(X_of(U_DEV, FEATS))[:, 1])
u_m = fit(U_TR, FEATS, 'attack_cat')
u_mthr = thr_fpr(U_DEV.label.values, score_attack(u_m, U_DEV, FEATS, 'Normal'))
E4 = {'NB07_replication_check_accuracy_UNSW_test-final': round(float(acc0), 6),
      'UNSW_dev_threshold_rf_binary': u_thr, 'UNSW_dev_threshold_rf_multiclass': u_mthr}

# UNSW → 5G test-final
pb = u_b.predict_proba(X_of(FIN, FEATS))[:, 1]
pm_s = score_attack(u_m, FIN, FEATS, 'Normal'); pm_c = u_m.predict(X_of(FIN, FEATS))
E4['UNSW->5G'] = {
    'rf_binary@0.5': ev(FIN.label, pb), 'rf_binary@UNSW_dev_threshold': ev(FIN.label, pb, u_thr),
    'rf_binary_attack_rate_by_class@0.5': recall_by_cat(FIN.attack_cat, pb, .5),
    'rf_multiclass_1-P(Normal)@0.5': ev(FIN.label, pm_s), 'rf_multiclass_1-P(Normal)@UNSW_dev_threshold': ev(FIN.label, pm_s, u_mthr),
    'cm_rf_binary@0.5': cm_bin(FIN.label.values, pb, .5, 'cm_E4_rf_binary_UNSW_to_5G',
                                 'E4 · binary RF train UNSW → 5G-NIDD test-final @0.5'),
    'cm_rf_binary@UNSW_dev_threshold': cm_bin(FIN.label.values, pb, u_thr, 'cm_E4_rf_binary_UNSW_to_5G_devthreshold',
                                             f'E4 · binary RF train UNSW → 5G test-final @{u_thr:.4f}')}
cm_multi(FIN.attack_cat.values, pm_c, C5, CU, 'cm_E4_rf_multiclass_UNSW_to_5G',
         'E4 · multiclass RF train UNSW (10 classes) → 5G-NIDD test-final (9 types)')
# 5G → UNSW test-final
qb = rf_b.predict_proba(X_of(U_FIN, FEATS))[:, 1]
qm_s = score_attack(rf_m, U_FIN, FEATS, 'Benign'); qm_c = rf_m.predict(X_of(U_FIN, FEATS))
E4['5G->UNSW'] = {
    'rf_binary@0.5': ev(U_FIN.label, qb), 'rf_binary@5G_dev_threshold': ev(U_FIN.label, qb, thr_b),
    'rf_binary_attack_rate_by_class@0.5': recall_by_cat(U_FIN.attack_cat, qb, .5),
    'rf_multiclass_1-P(Benign)@0.5': ev(U_FIN.label, qm_s),
    'cm_rf_binary@0.5': cm_bin(U_FIN.label.values, qb, .5, 'cm_E4_rf_binary_5G_to_UNSW',
                                 'E4 · binary RF train 5G → UNSW test-final @0.5')}
cm_multi(U_FIN.attack_cat.values, qm_c, CU, C5, 'cm_E4_rf_multiclass_5G_to_UNSW',
         'E4 · multiclass RF train 5G (9 classes) → UNSW test-final (10 classes)')
# baseline: UNSW model on UNSW's own test-final (for side-by-side comparison)
E4['UNSW->UNSW_baseline'] = {'rf_binary@0.5': ev(U_FIN.label, u_b.predict_proba(X_of(U_FIN, FEATS))[:, 1]),
                        'rf_multiclass': ev_multi(U_FIN.attack_cat.values, u_m.predict(X_of(U_FIN, FEATS)), CU)[0]}
log('E4_cross_dataset', E4)

# ================================================================ summary table
def row(name, r):
    return {'experiment': name, **{k: r[k] for k in ['n', 'attack_rate_test', 'threshold', 'accuracy', 'balanced_acc', 'mcc',
                                                    'precision', 'recall', 'f1', 'fpr', 'roc_auc', 'pr_auc',
                                                    'TN', 'FP', 'FN', 'TP']}}
rows = [row('E1 binary RF · 5G test-final @0.5', E1b['test-final@0.5']),
        row('E1 binary RF · 5G test-final @dev threshold', E1b['test-final@dev_threshold']),
        row('E1 multiclass RF→binary · 5G test-final @0.5', E1m['binary_1-P(Benign)_test-final@0.5']),
        row('E2 binary RF without ct_* · 5G test-final @0.5', R['E2_no_ct']['rf_binary_test-final@0.5'])]
for k, v in E3.items():
    rows.append(row(f'E3 binary RF · {k} @0.5', v['rf_binary@0.5']))
    rows.append(row(f'E3 binary RF · {k} @source-station threshold', v['rf_binary@source_station_threshold']))
rows += [row('E4 binary RF · UNSW→5G @0.5', E4['UNSW->5G']['rf_binary@0.5']),
         row('E4 binary RF · UNSW→5G @UNSW dev threshold', E4['UNSW->5G']['rf_binary@UNSW_dev_threshold']),
         row('E4 multiclass RF→binary · UNSW→5G @0.5', E4['UNSW->5G']['rf_multiclass_1-P(Normal)@0.5']),
         row('E4 binary RF · 5G→UNSW @0.5', E4['5G->UNSW']['rf_binary@0.5']),
         row('E4 binary RF · UNSW→UNSW (NB07 baseline) @0.5', E4['UNSW->UNSW_baseline']['rf_binary@0.5'])]
pd.DataFrame(rows).round(4).to_csv(RES / 'summary_binary.csv', index=False, encoding='utf-8-sig')
mrows = [{'experiment': 'E1 multiclass RF · 5G test-final', **E1m['test-final_multiclass']},
         {'experiment': 'E2 multiclass RF without ct_* · 5G test-final', **R['E2_no_ct']['rf_multiclass_test-final']}]
mrows += [{'experiment': f'E3 multiclass RF · {k}', **v['rf_multiclass']} for k, v in E3.items()]
mrows += [{'experiment': 'E4 multiclass RF · UNSW→UNSW (NB07 baseline)', **E4['UNSW->UNSW_baseline']['rf_multiclass']}]
pd.DataFrame(mrows).round(4).to_csv(RES / 'summary_multiclass.csv', index=False, encoding='utf-8-sig')

json.dump(R, open(RES / '02_results.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
print(pd.DataFrame(rows).round(4).to_string()); print(pd.DataFrame(mrows).round(4).to_string())
