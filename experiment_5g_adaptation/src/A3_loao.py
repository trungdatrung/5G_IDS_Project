"""A3 — Leave-one-attack-out on 5G using the A1-1 / A1-2 recipe (plan: docs/Plan_A_5G_Supervised_Adaptation.md §4).

Run :  python -I -X utf8 experiment_5g_adaptation/src/A3_loao.py <project dir>      (QUICK=1: 40 trees)
In  :  experiment_5gnidd/data/cleaned/5gnidd_unsw31.parquet
       data/cleaned/UNSW_NB15_training-set.parquet   — READ-ONLY
Out :  experiment_5g_adaptation/results/A3_loao/{tables,figures}/*

For each 5G attack class T:
  A3-a train on 5G-train minus T                  (A1-1 recipe)
  A3-b train on UNSW train-fit + 5G-train minus T  (A1-2 recipe)
  threshold: 5G-val minus T, FPR ≤ 0.10 · test: BS2 (T, Benign, already-seen attacks)
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
from sklearn.metrics import roc_auc_score, roc_curve
warnings.filterwarnings('ignore')

BASE = Path(sys.argv[1])
EXP = BASE / 'experiment_5g_adaptation'
TAB, FIG = EXP / 'results/A3_loao/tables', EXP / 'results/A3_loao/figures'
for p in (TAB, FIG):
    p.mkdir(parents=True, exist_ok=True)

QUICK = os.environ.get('QUICK') == '1'
RS = 42
N_TREES = 40 if QUICK else 300
RF_PARAMS = dict(n_estimators=N_TREES, max_depth=20, max_features=0.5, max_samples=0.7,
                 min_samples_leaf=1, class_weight=None, random_state=RS, n_jobs=-1)
CATS = ['proto', 'service', 'state']
FPR_MAX = 0.10
LOI18 = ['dur', 'proto', 'state', 'spkts', 'dpkts', 'sbytes', 'dbytes', 'rate', 'sload', 'dload', 'smean', 'dmean',
         'sinpkt', 'dinpkt', 'sjit', 'djit', 'sloss', 'dloss']
# pre-registered expectations from the plan §4, recorded before running
EXPECTED = {'HTTPFlood': 'High', 'SlowrateDoS': 'High', 'UDPFlood': 'Medium-High', 'SYNFlood': 'Medium-High',
           'SYNScan': 'Medium', 'TCPConnectScan': 'Low-Medium', 'UDPScan': 'Low', 'ICMPFlood': 'Low'}
RANGE = {'High': (0.9, 1.0), 'Medium-High': (0.6, 0.95), 'Medium': (0.4, 0.8), 'Low-Medium': (0.2, 0.6),
          'Low': (0.0, 0.4)}
R = {'mode': f'{"QUICK" if QUICK else "FULL"} | {N_TREES} trees | seed {RS}'}

def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)

# ---------------------------------------------------------------- helpers (shared with src/A1_merged_model.py)
def X_of(df, cols):
    return df[cols].astype({c: str for c in CATS if c in cols})

def fit(df):
    t = time.time()
    pre = ColumnTransformer([('cat', OneHotEncoder(handle_unknown='ignore'), [c for c in CATS if c in LOI18])],
                            remainder='passthrough', verbose_feature_names_out=False, sparse_threshold=0.3)
    m = Pipeline([('pre', pre), ('clf', RandomForestClassifier(**RF_PARAMS))]).fit(X_of(df, LOI18), df.label.values)
    log(f'    fit {time.time() - t:5.0f}s | {len(df):,} rows')
    return m

def thr_fpr(y, p, fmax=FPR_MAX):
    fpr, tpr, th = roc_curve(y, p)
    j = int(np.argmax(np.where(fpr <= fmax, tpr, -1.0)))
    return float(min(th[j], 1.0))

# ---------------------------------------------------------------- data (split identical to A1)
g = pd.read_parquet(BASE / 'experiment_5gnidd/data/cleaned/5gnidd_unsw31.parquet')
tr_u = pd.read_parquet(BASE / 'data/cleaned/UNSW_NB15_training-set.parquet')
for d in (g, tr_u):
    for c in CATS + ['attack_cat']:
        d[c] = d[c].astype(str).str.strip()
    d['label'] = d['label'].astype(int)
u_fit, _ = train_test_split(tr_u.index, test_size=0.2, stratify=tr_u['label'], random_state=RS)
U_TR = tr_u.loc[u_fit].copy()
BS1, BS2 = g[g.bs == 'BS1'].copy(), g[g.bs == 'BS2'].copy()
i_fit, i_val = train_test_split(BS1.index, test_size=0.2, stratify=BS1.attack_cat, random_state=RS)
G_TR, G_VAL = BS1.loc[i_fit], BS1.loc[i_val]
assert [len(U_TR), len(G_TR), len(G_VAL), len(BS2)] == [79147, 166411, 41603, 171542]
CLASSES = [c for c in G_TR.attack_cat.value_counts().index if c != 'Benign']   # 8 classes, largest -> smallest

# ---------------------------------------------------------------- run
rows = []
for T in CLASSES:
    log(f'Withholding {T}')
    tr5, va5 = G_TR[G_TR.attack_cat != T], G_VAL[G_VAL.attack_cat != T]
    for bt, trn in [('A3-a', tr5), ('A3-b', pd.concat([U_TR, tr5], ignore_index=True))]:
        m = fit(trn)
        t = thr_fpr(va5.label.values, m.predict_proba(X_of(va5, LOI18))[:, 1])
        p = m.predict_proba(X_of(BS2, LOI18))[:, 1]
        cat = BS2.attack_cat.values
        is_T, is_B = cat == T, cat == 'Benign'
        seen = (BS2.label.values == 1) & ~is_T
        bt_T = np.r_[np.zeros(is_B.sum()), np.ones(is_T.sum())]
        rows.append({'withheld_class': T, 'n_T_BS2': int(is_T.sum()), 'variant': bt, 'threshold': round(t, 4),
                     'recall_T': float((p[is_T] >= t).mean()), 'fpr_benign': float((p[is_B] >= t).mean()),
                     'roc_auc_benign_vs_T': roc_auc_score(bt_T, np.r_[p[is_B], p[is_T]]),
                     'recall_seen_attacks': float((p[seen] >= t).mean()),
                     'roc_auc_full_BS2': roc_auc_score(BS2.label.values, p),
                     'expected_A3-a': EXPECTED[T]})
    pd.DataFrame(rows).round(4).to_csv(TAB / 'A3_loao.csv', index=False, encoding='utf-8-sig')   # incremental write

# ---------------------------------------------------------------- conclusions against the plan's criteria
D = pd.DataFrame(rows)
A, B = D[D.variant == 'A3-a'].set_index('withheld_class'), D[D.variant == 'A3-b'].set_index('withheld_class')
gain = (B.recall_T - A.recall_T)
d_fpr = (B.fpr_benign - A.fpr_benign)
helped = [T for T in CLASSES if gain[T] >= 0.05 and d_fpr[T] <= 0.02]
R['H4'] = {'recall_T_b_minus_a': gain.round(4).to_dict(), 'fpr_benign_b_minus_a': d_fpr.round(4).to_dict(),
           'classes_UNSW_helped': helped, 'accepted': len(helped) >= 2}
R['expected_by_class'] = {T: {'expected': EXPECTED[T], 'range': RANGE[EXPECTED[T]], 'recall_A3-a': round(A.recall_T[T], 4),
                              'correct': bool(RANGE[EXPECTED[T]][0] <= A.recall_T[T] <= RANGE[EXPECTED[T]][1])} for T in CLASSES}
R['n_expectations_correct'] = int(sum(v['correct'] for v in R['expected_by_class'].values()))
R['stop_criteria'] = {'min_recall_seen_attacks': float(D.recall_seen_attacks.min()),
                  'below_0.99': D.loc[D.recall_seen_attacks < 0.99, ['withheld_class', 'variant',
                                                                              'recall_seen_attacks']].to_dict('records')}
a1 = pd.read_csv(EXP / 'results/A1_merged_model/tables/A1_recall_by_class.csv')
a1 = a1[a1.test_set == '5G BS2'].set_index('class')
R['A1_benchmark_recall_when_seen'] = {T: {'A1-1': a1.loc[T, 'A1-1'], 'A1-2': a1.loc[T, 'A1-2']} for T in CLASSES}
R['A1_benchmark_fpr_benign'] = {'A1-1': a1.loc['Benign', 'A1-1'], 'A1-2': a1.loc['Benign', 'A1-2']}

# ---------------------------------------------------------------- figure
x = np.arange(len(CLASSES)); w = 0.38
fig, ax = plt.subplots(figsize=(12, 4.8))
ax.bar(x - w / 2, A.recall_T[CLASSES], w, color='#1f77b4', label='A3-a Pure 5G: Withheld Attack Recall')
ax.bar(x + w / 2, B.recall_T[CLASSES], w, color='#d62728', label='A3-b UNSW+5G: Withheld Attack Recall')
ax.plot(x - w / 2, A.fpr_benign[CLASSES], 'kv', ms=7, label='FPR Benign (A3-a)')
ax.plot(x + w / 2, B.fpr_benign[CLASSES], 'k^', ms=7, label='FPR Benign (A3-b)')
for i, T in enumerate(CLASSES):
    lo, hi = RANGE[EXPECTED[T]]
    ax.add_patch(plt.Rectangle((i - 0.45, lo), 0.9, hi - lo, color='orange', alpha=0.12, lw=0))
    ax.text(i - w / 2, A.recall_T[T] + 0.02, f'{A.recall_T[T]:.2f}', ha='center', fontsize=7)
    ax.text(i + w / 2, B.recall_T[T] + 0.02, f'{B.recall_T[T]:.2f}', ha='center', fontsize=7)
ax.axhline(1.0, color='k', ls='--', lw=1, label='A1-2: Recall ≈ 1.0 when seen')
ax.axhline(FPR_MAX, color='gray', ls=':', lw=1, label='FPR constraint ≤ 0.10')
ax.set_xticks(x); ax.set_xticklabels([f'{T}\n(n={int(A.n_T_BS2[T]):,})' for T in CLASSES], fontsize=8)
ax.set_ylim(0, 1.12); ax.set_ylabel('Rate'); ax.grid(axis='y', alpha=0.3)
ax.set_title('A3 · Leave-One-Attack-Out on 5G BS2 (Orange shade = Pre-registered expected interval for A3-a)', fontsize=10)
ax.legend(fontsize=7, loc='upper center', bbox_to_anchor=(0.5, -0.17), ncol=3)
fig.tight_layout(); fig.savefig(FIG / 'A3_loao.png', dpi=130); plt.close(fig)

json.dump(R, open(TAB / 'A3_results.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
print(D.round(4).to_string())
print(json.dumps({k: R[k] for k in ('H4', 'expected_by_class', 'n_expectations_correct', 'stop_criteria')}, ensure_ascii=False,
                 indent=1, default=float))
