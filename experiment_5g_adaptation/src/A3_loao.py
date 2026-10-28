"""A3 — Leave-one-attack-out trên 5G với công thức A1-1 / A1-2 (kế hoạch: docs/Ke_hoach_A_hoc_co_nhan_5G.md §4).

Chạy:  python -I -X utf8 experiment_5g_adaptation/src/A3_loao.py <thư mục dự án>      (QUICK=1: 40 cây)
Vào :  experiment_5gnidd/data/cleaned/5gnidd_unsw31.parquet
       data/cleaned/UNSW_NB15_training-set.parquet   — CHỈ ĐỌC
Ra  :  experiment_5g_adaptation/results/A3_loao/{tables,figures}/*

Với mỗi loại tấn công T của 5G:
  A3-a train 5G-train bỏ T                 (công thức A1-1)
  A3-b train UNSW train-fit + 5G-train bỏ T (công thức A1-2)
  ngưỡng: 5G-val bỏ T, FPR ≤ 0,10 · test: BS2 (T, Benign, các tấn công đã thấy)
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
# dự đoán ghi trong kế hoạch §4, trước khi chạy
DU_DOAN = {'HTTPFlood': 'Cao', 'SlowrateDoS': 'Cao', 'UDPFlood': 'Trung bình–cao', 'SYNFlood': 'Trung bình–cao',
           'SYNScan': 'Trung bình', 'TCPConnectScan': 'Thấp–trung bình', 'UDPScan': 'Thấp', 'ICMPFlood': 'Thấp'}
KHOANG = {'Cao': (0.9, 1.0), 'Trung bình–cao': (0.6, 0.95), 'Trung bình': (0.4, 0.8), 'Thấp–trung bình': (0.2, 0.6),
          'Thấp': (0.0, 0.4)}
R = {'che_do': f'{"QUICK" if QUICK else "FULL"} | {N_TREES} cây | seed {RS}'}

def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)

# ---------------------------------------------------------------- hàm (giống src/A1_model_gop.py)
def X_of(df, cols):
    return df[cols].astype({c: str for c in CATS if c in cols})

def fit(df):
    t = time.time()
    pre = ColumnTransformer([('cat', OneHotEncoder(handle_unknown='ignore'), [c for c in CATS if c in LOI18])],
                            remainder='passthrough', verbose_feature_names_out=False, sparse_threshold=0.3)
    m = Pipeline([('pre', pre), ('clf', RandomForestClassifier(**RF_PARAMS))]).fit(X_of(df, LOI18), df.label.values)
    log(f'    fit {time.time() - t:5.0f}s | {len(df):,} dòng')
    return m

def thr_fpr(y, p, fmax=FPR_MAX):
    fpr, tpr, th = roc_curve(y, p)
    j = int(np.argmax(np.where(fpr <= fmax, tpr, -1.0)))
    return float(min(th[j], 1.0))

# ---------------------------------------------------------------- dữ liệu (chia giống A1)
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
LOAI = [c for c in G_TR.attack_cat.value_counts().index if c != 'Benign']   # 8 loại, lớn → nhỏ

# ---------------------------------------------------------------- chạy
rows = []
for T in LOAI:
    log(f'Giấu {T}')
    tr5, va5 = G_TR[G_TR.attack_cat != T], G_VAL[G_VAL.attack_cat != T]
    for bt, trn in [('A3-a', tr5), ('A3-b', pd.concat([U_TR, tr5], ignore_index=True))]:
        m = fit(trn)
        t = thr_fpr(va5.label.values, m.predict_proba(X_of(va5, LOI18))[:, 1])
        p = m.predict_proba(X_of(BS2, LOI18))[:, 1]
        cat = BS2.attack_cat.values
        is_T, is_B = cat == T, cat == 'Benign'
        seen = (BS2.label.values == 1) & ~is_T
        bt_T = np.r_[np.zeros(is_B.sum()), np.ones(is_T.sum())]
        rows.append({'loai_giau': T, 'n_T_BS2': int(is_T.sum()), 'bien_the': bt, 'nguong': round(t, 4),
                     'recall_T': float((p[is_T] >= t).mean()), 'fpr_benign': float((p[is_B] >= t).mean()),
                     'roc_auc_benign_vs_T': roc_auc_score(bt_T, np.r_[p[is_B], p[is_T]]),
                     'recall_tan_cong_da_thay': float((p[seen] >= t).mean()),
                     'roc_auc_toan_BS2': roc_auc_score(BS2.label.values, p),
                     'du_doan_A3-a': DU_DOAN[T]})
    pd.DataFrame(rows).round(4).to_csv(TAB / 'A3_loao.csv', index=False, encoding='utf-8-sig')   # ghi dần

# ---------------------------------------------------------------- kết luận theo tiêu chí kế hoạch
D = pd.DataFrame(rows)
A, B = D[D.bien_the == 'A3-a'].set_index('loai_giau'), D[D.bien_the == 'A3-b'].set_index('loai_giau')
gain = (B.recall_T - A.recall_T)
d_fpr = (B.fpr_benign - A.fpr_benign)
giup = [T for T in LOAI if gain[T] >= 0.05 and d_fpr[T] <= 0.02]
R['H4'] = {'recall_T_b_tru_a': gain.round(4).to_dict(), 'fpr_benign_b_tru_a': d_fpr.round(4).to_dict(),
           'loai_UNSW_giup': giup, 'dung': len(giup) >= 2}
R['du_doan_theo_loai'] = {T: {'du_doan': DU_DOAN[T], 'khoang': KHOANG[DU_DOAN[T]], 'recall_A3-a': round(A.recall_T[T], 4),
                              'dung': bool(KHOANG[DU_DOAN[T]][0] <= A.recall_T[T] <= KHOANG[DU_DOAN[T]][1])} for T in LOAI}
R['so_du_doan_dung'] = int(sum(v['dung'] for v in R['du_doan_theo_loai'].values()))
R['diem_dung'] = {'recall_tan_cong_da_thay_min': float(D.recall_tan_cong_da_thay.min()),
                  'lan_duoi_0.99': D.loc[D.recall_tan_cong_da_thay < 0.99, ['loai_giau', 'bien_the',
                                                                              'recall_tan_cong_da_thay']].to_dict('records')}
a1 = pd.read_csv(EXP / 'results/A1_model_gop/tables/A1_recall_theo_loai.csv')
a1 = a1[a1.tap_test == '5G BS2'].set_index('loai')
R['moc_A1_recall_khi_da_thay'] = {T: {'A1-1': a1.loc[T, 'A1-1'], 'A1-2': a1.loc[T, 'A1-2']} for T in LOAI}
R['moc_A1_fpr_benign'] = {'A1-1': a1.loc['Benign', 'A1-1'], 'A1-2': a1.loc['Benign', 'A1-2']}

# ---------------------------------------------------------------- hình
x = np.arange(len(LOAI)); w = 0.38
fig, ax = plt.subplots(figsize=(12, 4.8))
ax.bar(x - w / 2, A.recall_T[LOAI], w, color='#1f77b4', label='A3-a Pure 5G: Withheld Attack Recall')
ax.bar(x + w / 2, B.recall_T[LOAI], w, color='#d62728', label='A3-b UNSW+5G: Withheld Attack Recall')
ax.plot(x - w / 2, A.fpr_benign[LOAI], 'kv', ms=7, label='FPR Benign (A3-a)')
ax.plot(x + w / 2, B.fpr_benign[LOAI], 'k^', ms=7, label='FPR Benign (A3-b)')
for i, T in enumerate(LOAI):
    lo, hi = KHOANG[DU_DOAN[T]]
    ax.add_patch(plt.Rectangle((i - 0.45, lo), 0.9, hi - lo, color='orange', alpha=0.12, lw=0))
    ax.text(i - w / 2, A.recall_T[T] + 0.02, f'{A.recall_T[T]:.2f}', ha='center', fontsize=7)
    ax.text(i + w / 2, B.recall_T[T] + 0.02, f'{B.recall_T[T]:.2f}', ha='center', fontsize=7)
ax.axhline(1.0, color='k', ls='--', lw=1, label='A1-2: Recall ≈ 1.0 when seen')
ax.axhline(FPR_MAX, color='gray', ls=':', lw=1, label='FPR constraint ≤ 0.10')
ax.set_xticks(x); ax.set_xticklabels([f'{T}\n(n={int(A.n_T_BS2[T]):,})' for T in LOAI], fontsize=8)
ax.set_ylim(0, 1.12); ax.set_ylabel('Rate'); ax.grid(axis='y', alpha=0.3)
ax.set_title('A3 · Leave-One-Attack-Out on 5G BS2 (Orange shade = Pre-registered expected interval for A3-a)', fontsize=10)
ax.legend(fontsize=7, loc='upper center', bbox_to_anchor=(0.5, -0.17), ncol=3)
fig.tight_layout(); fig.savefig(FIG / 'A3_loao.png', dpi=130); plt.close(fig)

json.dump(R, open(TAB / 'A3_ket_qua.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
print(D.round(4).to_string())
print(json.dumps({k: R[k] for k in ('H4', 'du_doan_theo_loai', 'so_du_doan_dung', 'diem_dung')}, ensure_ascii=False,
                 indent=1, default=float))
