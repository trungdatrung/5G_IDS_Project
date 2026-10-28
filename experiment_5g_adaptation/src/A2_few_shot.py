"""A2 — 5G label-count learning curve using the A1-2 recipe (plan: docs/Plan_A_5G_Supervised_Adaptation.md §3).

Run :  python -I -X utf8 experiment_5g_adaptation/src/A2_few_shot.py <project dir>      (QUICK=1: 40 trees, 2 seeds)
In  :  experiment_5gnidd/data/cleaned/5gnidd_unsw31.parquet
       data/cleaned/UNSW_NB15_{training,testing}-set.parquet, data/cleaned/test_split_v3.csv
       experiment_5g_adaptation/results/A1_merged_model/tables/A1_summary.csv   (A1-1/A1-2 benchmark)  — all READ-ONLY
Out :  experiment_5g_adaptation/results/A2_few_shot/{tables,figures}/*

Variants (same recipe for every n, seed pair):
  A2-a n 5G labels only                           5G threshold: n/4 sample of 5G-val
  A2-b UNSW + n 5G labels, equal weighting (A1-2)  5G threshold: 5G-val sample · UNSW threshold: test-dev
  A2-c UNSW + n 5G labels, 50/50 domain balance    same as A2-b
  A2-d model A2-b, 5G threshold chosen on UNSW test-dev + 5G-val sample combined
"""
import os, sys, json, time, warnings
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (balanced_accuracy_score, recall_score, roc_auc_score, average_precision_score,
                             confusion_matrix, matthews_corrcoef, roc_curve)
warnings.filterwarnings('ignore')

BASE = Path(sys.argv[1])
EXP = BASE / 'experiment_5g_adaptation'
TAB, FIG = EXP / 'results/A2_few_shot/tables', EXP / 'results/A2_few_shot/figures'
for p in (TAB, FIG):
    p.mkdir(parents=True, exist_ok=True)

QUICK = os.environ.get('QUICK') == '1'
RS = 42
N_TREES = 40 if QUICK else 300
SEEDS = [0, 1] if QUICK else [0, 1, 2, 3, 4]
N_LIST = [50, 100, 200, 500, 1000, 2000, 5000, 20000]
RF_PARAMS = dict(n_estimators=N_TREES, max_depth=20, max_features=0.5, max_samples=0.7,
                 min_samples_leaf=1, class_weight=None, n_jobs=-1)
CATS = ['proto', 'service', 'state']
FPR_MAX = 0.10
LOI18 = ['dur', 'proto', 'state', 'spkts', 'dpkts', 'sbytes', 'dbytes', 'rate', 'sload', 'dload', 'smean', 'dmean',
         'sinpkt', 'dinpkt', 'sjit', 'djit', 'sloss', 'dloss']
R = {'mode': f'{"QUICK" if QUICK else "FULL"} | {N_TREES} trees | seeds {SEEDS}'}

def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)

# ---------------------------------------------------------------- helpers (shared with src/A1_merged_model.py)
def X_of(df, cols):
    return df[cols].astype({c: str for c in CATS if c in cols})

def fit(df, y, seed, w=None):
    pre = ColumnTransformer([('cat', OneHotEncoder(handle_unknown='ignore'), [c for c in CATS if c in LOI18])],
                            remainder='passthrough', verbose_feature_names_out=False, sparse_threshold=0.3)
    m = Pipeline([('pre', pre), ('clf', RandomForestClassifier(**RF_PARAMS, random_state=seed))])
    return m.fit(X_of(df, LOI18), y, **({} if w is None else {'clf__sample_weight': w}))

def proba(m, df):
    return m.predict_proba(X_of(df, LOI18))[:, 1]

def thr_fpr(y, p, fmax=FPR_MAX):
    fpr, tpr, th = roc_curve(y, p)
    j = int(np.argmax(np.where(fpr <= fmax, tpr, -1.0)))
    return float(min(th[j], 1.0))

def ev(y, p, thr):
    y = np.asarray(y); pred = (p >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return dict(threshold=round(thr, 4), roc_auc=roc_auc_score(y, p), pr_auc=average_precision_score(y, p),
                balanced_acc=balanced_accuracy_score(y, pred), mcc=matthews_corrcoef(y, pred),
                recall=recall_score(y, pred, zero_division=0), fpr=fp / max(fp + tn, 1),
                TN=int(tn), FP=int(fp), FN=int(fn), TP=int(tp))

def sample(df, n, seed):
    """Draw n rows stratified by attack_cat, at least 1 per class."""
    k = (df.attack_cat.value_counts(normalize=True) * n).round().clip(lower=1).astype(int)
    return pd.concat([df[df.attack_cat == c].sample(int(k[c]), random_state=seed) for c in k.index])

# ---------------------------------------------------------------- data (split identical to A1)
g = pd.read_parquet(BASE / 'experiment_5gnidd/data/cleaned/5gnidd_unsw31.parquet')
tr_u = pd.read_parquet(BASE / 'data/cleaned/UNSW_NB15_training-set.parquet')
te_u = pd.read_parquet(BASE / 'data/cleaned/UNSW_NB15_testing-set.parquet')
for d in (g, tr_u, te_u):
    for c in CATS + ['attack_cat']:
        d[c] = d[c].astype(str).str.strip()
    d['label'] = d['label'].astype(int)
smap = pd.read_csv(BASE / 'data/cleaned/test_split_v3.csv').sort_values('test_index')
is_dev = (smap['split'].values == 'test_dev')
U_DEV, U_FIN = te_u[is_dev].copy(), te_u[~is_dev].copy()
u_fit, _ = train_test_split(tr_u.index, test_size=0.2, stratify=tr_u['label'], random_state=RS)
U_TR = tr_u.loc[u_fit].copy()
assert [len(U_TR), len(U_DEV), len(U_FIN)] == [79147, 25283, 25284]
BS1, BS2 = g[g.bs == 'BS1'].copy(), g[g.bs == 'BS2'].copy()
i_fit, i_val = train_test_split(BS1.index, test_size=0.2, stratify=BS1.attack_cat, random_state=RS)
G_TR, G_VAL = BS1.loc[i_fit], BS1.loc[i_val]
assert [len(G_TR), len(G_VAL), len(BS2)] == [166411, 41603, 171542]

# ---------------------------------------------------------------- run
rows, R['samples_per_class'] = [], {}
def add(n, s, bt, test_set, kind, y, p, t):
    rows.append({'n_5G_labels': n, 'seed': s, 'variant': bt, 'test_set': test_set, 'threshold_type': kind, **ev(y, p, t)})

for n in N_LIST:
    for s in SEEDS:
        t0 = time.time()
        tr5, va5 = sample(G_TR, n, s), sample(G_VAL, max(n // 4, 1), s)
        R['samples_per_class'][f'{n}|{s}'] = {'train': tr5.attack_cat.value_counts().to_dict(),
                                         'val': va5.attack_cat.value_counts().to_dict()}
        mix = pd.concat([U_TR, tr5], ignore_index=True)
        n_u, n_g = len(U_TR), len(tr5)
        w = np.r_[np.full(n_u, 0.5 * (n_u + n_g) / n_u), np.full(n_g, 0.5 * (n_u + n_g) / n_g)]
        ma = fit(tr5, tr5.label.values, s)
        mb = fit(mix, mix.label.values, s)
        mc = fit(mix, mix.label.values, s, w)
        for bt, m in [('A2-a', ma), ('A2-b', mb), ('A2-c', mc)]:
            p2 = proba(m, BS2)
            for kind, t in [('@0.5', 0.5), ('@domain_threshold', thr_fpr(va5.label.values, proba(m, va5)))]:
                add(n, s, bt, '5G BS2', kind, BS2.label, p2, t)
            if bt != 'A2-a':
                pu = proba(m, U_FIN)
                for kind, t in [('@0.5', 0.5), ('@domain_threshold', thr_fpr(U_DEV.label.values, proba(m, U_DEV)))]:
                    add(n, s, bt, 'UNSW test-final', kind, U_FIN.label, pu, t)
            if bt == 'A2-b':                                                # A2-d: same model, threshold from combined validation
                vg = pd.concat([U_DEV, va5])
                add(n, s, 'A2-d', '5G BS2', '@combined_threshold', BS2.label, p2, thr_fpr(vg.label.values, proba(m, vg)))
        log(f'n={n:>6} seed={s} | {time.time() - t0:5.0f}s')
    pd.DataFrame(rows).round(5).to_csv(TAB / 'A2_per_run.csv', index=False, encoding='utf-8-sig')   # incremental write

# ---------------------------------------------------------------- aggregate
D = pd.DataFrame(rows)
M = D[D.threshold_type != '@0.5'].groupby(['n_5G_labels', 'variant', 'test_set'])[
    ['threshold', 'roc_auc', 'pr_auc', 'balanced_acc', 'mcc', 'recall', 'fpr']].agg(['mean', 'std'])
M.columns = [f'{a}_{b}' for a, b in M.columns]
M = M.reset_index()
M.round(4).to_csv(TAB / 'A2_summary.csv', index=False, encoding='utf-8-sig')
G = M[M.test_set == '5G BS2'].set_index(['variant', 'n_5G_labels'])

def roc(bt, n): return G.loc[(bt, n), 'roc_auc_mean']
def fpr(bt, n): return G.loc[(bt, n), 'fpr_mean']
small = [50, 100, 200]
gap = {n: roc('A2-a', n) - roc('A2-b', n) for n in small}
h2_n = [n for n in small if gap[n] > 0]
R['H1'] = {'gap_a_minus_b': gap, 'accepted': bool(sum(v > 0 for v in gap.values()) >= 2)}
R['H2'] = {'closure_ratio': {n: (roc('A2-c', n) - roc('A2-b', n)) / gap[n] for n in h2_n},
           'accepted': bool(len(h2_n) > 0 and sum((roc('A2-c', n) - roc('A2-b', n)) / gap[n] >= 0.5 for n in h2_n) >= min(2, len(h2_n)))}
d_fpr = {n: fpr('A2-d', n) - fpr('A2-b', n) for n in N_LIST if n <= 1000}
R['H3'] = {'fpr_d_minus_b': d_fpr, 'accepted': bool(all(v >= 0.2 for v in d_fpr.values()))}
R['min_n_required'] = {bt: next((n for n in N_LIST if roc(bt, n) >= 0.99 and fpr(bt, n) <= 0.12), None)
                    for bt in ('A2-a', 'A2-b', 'A2-c', 'A2-d')}
R['stop_criteria'] = {'A2-b_n20000_roc_bs2': roc('A2-b', 20000), 'must_stop': bool(roc('A2-b', 20000) < 0.99)}
a1 = pd.read_csv(EXP / 'results/A1_merged_model/tables/A1_summary.csv')
a1 = a1[(a1.threshold_type == '@domain_threshold') & (a1.test_set == '5G BS2')].set_index('variant')
R['A1_benchmark_full_166411_labels'] = {k: a1.loc[k, ['roc_auc', 'fpr', 'recall']].to_dict() for k in ('A1-1', 'A1-2')}

# ---------------------------------------------------------------- figure
fig, axs = plt.subplots(1, 3, figsize=(15, 4.3))
color = {'A2-a': '#1f77b4', 'A2-b': '#d62728', 'A2-c': '#2ca02c', 'A2-d': '#7f7f7f'}
label = {'A2-a': 'A2-a Pure 5G', 'A2-b': 'A2-b Merged UNSW+5G (A1-2)', 'A2-c': 'A2-c Domain Balanced',
       'A2-d': 'A2-d Joint Validation Threshold'}
for ax, (col, name, target) in zip(axs, [('roc_auc', 'ROC-AUC on 5G BS2', 0.99), ('fpr', 'FPR on 5G BS2 (Benign)', 0.12),
                                       ('recall', 'Recall on 5G BS2', None)]):
    for bt in color:
        if col == 'roc_auc' and bt == 'A2-d':
            continue                                                        # A2-d shares A2-b's model -> same ROC-AUC
        d = G.loc[bt]
        ax.plot(d.index, d[f'{col}_mean'], 'o-', color=color[bt], label=label[bt], lw=1.6, ms=4)
        ax.fill_between(d.index, d[f'{col}_mean'] - d[f'{col}_std'], d[f'{col}_mean'] + d[f'{col}_std'],
                        color=color[bt], alpha=0.15)
    ax.axhline(a1.loc['A1-2', col], color='k', ls='--', lw=1, label='A1-2 (166,411 labels)')
    if target is not None:
        ax.axhline(target, color='orange', ls=':', lw=1.2, label=f'Target {target}')
    ax.set_xscale('log'); ax.set_xlabel('Number of 5G Training Labels (log scale)'); ax.set_title(name, fontsize=10)
    ax.grid(alpha=0.3)
axs[0].legend(fontsize=7, loc='lower right'); axs[1].legend(fontsize=7, loc='upper right')
fig.suptitle(f'A2 · 5G label-count learning curve (mean ± 1 SD, {len(SEEDS)} seeds) · 5G threshold chosen on n/4 sample of 5G-val',
             fontsize=10)
fig.tight_layout(); fig.savefig(FIG / 'A2_learning_curve.png', dpi=130); plt.close(fig)

json.dump(R, open(TAB / 'A2_results.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30); pd.set_option('display.max_rows', 200)
print(M[['n_5G_labels', 'variant', 'test_set', 'threshold_mean', 'roc_auc_mean', 'roc_auc_std', 'fpr_mean', 'fpr_std',
         'recall_mean', 'balanced_acc_mean']].round(4).to_string())
print(json.dumps({k: R[k] for k in ('H1', 'H2', 'H3', 'min_n_required', 'stop_criteria')}, ensure_ascii=False, indent=1,
                 default=float))
