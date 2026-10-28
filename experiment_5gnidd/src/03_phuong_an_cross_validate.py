"""Bước 3 — So sánh các phương án cross-validate UNSW-NB15 ↔ 5G-NIDD để chọn phương án khả thi nhất.

Chạy:  python -I -X utf8 experiment_5gnidd/src/03_phuong_an_cross_validate.py <thư mục dự án>   (QUICK=1 để chạy 40 cây)
Vào :  experiment_5gnidd/data/cleaned/5gnidd_unsw31.parquet   (do bước 1 sinh)
       data/cleaned/UNSW_NB15_{training,testing}-set.parquet, data/cleaned/test_split_v3.csv   (CHỈ ĐỌC)
Ra  :  experiment_5gnidd/results/03_*.csv, 03_ket_qua.json

Ba trục so sánh:
  Bộ feature  F31   : đủ 31 feature của model hiện tại
              LOI12 : lõi ổn định — lấy chính xác / công thức Argus đã kiểm, không phải dấu vân tay môi trường
              LOI18 : LOI12 + 6 feature xấp xỉ (sinpkt, dinpkt, sjit, djit, sloss, dloss)
  Căn nhãn    ALL   : mọi họ tấn công UNSW
              DR    : UNSW chỉ giữ Normal + DoS + Reconnaissance (cùng họ với 5G-NIDD: DoS + scan)
  Giao thức   P1 zero-shot UNSW → 5G         P2 ngược 5G-BS1 → UNSW test-final
              P3 train gộp UNSW + BS1 → BS2  P4 few-shot: UNSW + k% nhãn BS1 → BS2 (so với chỉ k% BS1)
              P5 mức trần trong miền: BS1 → BS2
Ngưỡng vận hành luôn chọn trên tập của MIỀN NGUỒN (FPR ≤ 0,10), không nhìn nhãn miền đích.
Tham số RF, OneHot, hàm đo giống notebook 07 / bước 2.
"""
import os, sys, json, time, warnings
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (balanced_accuracy_score, recall_score, roc_auc_score, average_precision_score,
                             confusion_matrix, matthews_corrcoef, roc_curve)
warnings.filterwarnings('ignore')

BASE = Path(sys.argv[1])
EXP = BASE / 'experiment_5gnidd'
RES = EXP / 'results'
RES.mkdir(parents=True, exist_ok=True)

QUICK = os.environ.get('QUICK') == '1'
RS = 42
N_TREES = 40 if QUICK else 300
RF_PARAMS = dict(n_estimators=N_TREES, max_depth=20, max_features=0.5, max_samples=0.7,
                 min_samples_leaf=1, class_weight=None, random_state=RS, n_jobs=-1)
CATS = ['proto', 'service', 'state']
FPR_MAX = 0.10
LOI12 = ['dur', 'proto', 'state', 'spkts', 'dpkts', 'sbytes', 'dbytes', 'rate', 'sload', 'dload', 'smean', 'dmean']
LOI18 = LOI12 + ['sinpkt', 'dinpkt', 'sjit', 'djit', 'sloss', 'dloss']
UNSW_DR = ['Normal', 'DoS', 'Reconnaissance']
FEW_K = [0.001, 0.01, 0.05, 0.20]
FEW_SEEDS = [0, 1, 2]
ROWS, R = [], {'che_do': f'{"QUICK" if QUICK else "FULL"} | {N_TREES} cây | seed {RS}'}

# ---------------------------------------------------------------- hàm (giống bước 2)
def X_of(df, cols):
    return df[cols].astype({c: str for c in CATS if c in cols})

def rf_pipe(cols, seed=RS):
    pre = ColumnTransformer([('cat', OneHotEncoder(handle_unknown='ignore'), [c for c in CATS if c in cols])],
                            remainder='passthrough', verbose_feature_names_out=False, sparse_threshold=0.3)
    return Pipeline([('pre', pre), ('clf', RandomForestClassifier(**{**RF_PARAMS, 'random_state': seed}))])

def fit(df, cols, seed=RS):
    t = time.time()
    m = rf_pipe(cols, seed).fit(X_of(df, cols), df.label.values)
    print(f'    fit {time.time() - t:5.0f}s | {len(df):,} dòng | {len(cols)} feature', flush=True)
    return m

def proba(m, df, cols):
    return m.predict_proba(X_of(df, cols))[:, 1]

def thr_fpr(y, p, fmax=FPR_MAX):
    fpr, tpr, th = roc_curve(y, p)
    j = int(np.argmax(np.where(fpr <= fmax, tpr, -1.0)))
    return float(min(th[j], 1.0))

def ev(y, p, thr):
    y = np.asarray(y); pred = (p >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return dict(nguong=round(thr, 4), roc_auc=roc_auc_score(y, p), pr_auc=average_precision_score(y, p),
                pi=float(y.mean()), balanced_acc=balanced_accuracy_score(y, pred), mcc=matthews_corrcoef(y, pred),
                recall=recall_score(y, pred, zero_division=0), fpr=fp / max(fp + tn, 1))

def recall_by_cat(cat, p, thr):
    return pd.Series(p >= thr).groupby(np.asarray(cat)).mean().round(4).to_dict()

def record(gt, ten, fs, nhan, dich, y, p, thr_src, extra=None):
    """Ghi 2 dòng: @0,5 và @ngưỡng chọn trên miền nguồn."""
    for kieu, t in [('@0,5', 0.5), ('@nguong_nguon', thr_src)]:
        ROWS.append({'giao_thuc': gt, 'phuong_an': ten, 'feature': fs, 'can_nhan': nhan, 'tap_dich': dich,
                     'n_dich': int(len(y)), 'kieu_nguong': kieu, **ev(y, p, t), **(extra or {})})

# ---------------------------------------------------------------- dữ liệu
g = pd.read_parquet(EXP / 'data/cleaned/5gnidd_unsw31.parquet')
tr_u = pd.read_parquet(BASE / 'data/cleaned/UNSW_NB15_training-set.parquet')
te_u = pd.read_parquet(BASE / 'data/cleaned/UNSW_NB15_testing-set.parquet')
F31 = [c for c in tr_u.columns if c not in ('label', 'attack_cat')]
FS = {'F31': F31, 'LOI12': LOI12, 'LOI18': LOI18}
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
dr = lambda d: d[d.attack_cat.isin(UNSW_DR)]
UN = {'ALL': (U_TR, U_DEV, U_FIN), 'DR': (dr(U_TR), dr(U_DEV), dr(U_FIN))}

BS1, BS2 = g[g.bs == 'BS1'].copy(), g[g.bs == 'BS2'].copy()
b1_fit_i, b1_val_i = train_test_split(BS1.index, test_size=0.2, stratify=BS1.attack_cat, random_state=RS)
B1_FIT, B1_VAL = BS1.loc[b1_fit_i], BS1.loc[b1_val_i]
R['kich_thuoc'] = {'UNSW_train_fit': len(U_TR), 'UNSW_train_fit_DR': len(UN['DR'][0]), 'UNSW_test_dev': len(U_DEV),
                   'UNSW_test_final': len(U_FIN), 'UNSW_test_final_DR': len(UN['DR'][2]),
                   '5G_toan_bo': len(g), 'BS1_fit': len(B1_FIT), 'BS1_val': len(B1_VAL), 'BS2': len(BS2)}
print(R['kich_thuoc'], flush=True)

# ================================================================ P1. zero-shot UNSW → 5G
print('P1 — zero-shot UNSW → 5G', flush=True)
R['P1_recall_theo_loai'] = {}
for nhan, (tr, dv, fn) in UN.items():
    for fs, cols in FS.items():
        m = fit(tr, cols)
        t = thr_fpr(dv.label.values, proba(m, dv, cols))
        pg, p2 = proba(m, g, cols), proba(m, BS2, cols)
        record('P1', 'zero-shot UNSW→5G', fs, nhan, '5G toàn bộ', g.label, pg, t)
        record('P1', 'zero-shot UNSW→5G', fs, nhan, '5G BS2', BS2.label, p2, t)
        record('P1', 'mốc UNSW→UNSW', fs, nhan, 'UNSW test-final' + ('' if nhan == 'ALL' else ' DR'), fn.label,
               proba(m, fn, cols), t)
        R['P1_recall_theo_loai'][f'{fs}|{nhan}'] = recall_by_cat(g.attack_cat, pg, t)

# ================================================================ P2. ngược: 5G-BS1 → UNSW
print('P2 — 5G-BS1 → UNSW', flush=True)
for fs, cols in FS.items():
    m = fit(B1_FIT, cols)
    t = thr_fpr(B1_VAL.label.values, proba(m, B1_VAL, cols))
    for nhan in ('ALL', 'DR'):
        fn = UN[nhan][2]
        record('P2', 'ngược 5G-BS1→UNSW', fs, nhan, 'UNSW test-final' + ('' if nhan == 'ALL' else ' DR'),
               fn.label, proba(m, fn, cols), t)

# ================================================================ P5. mức trần trong miền 5G: BS1 → BS2
print('P5 — BS1 → BS2', flush=True)
R['P5_recall_theo_loai'] = {}
for fs, cols in FS.items():
    m = fit(B1_FIT, cols)
    t = thr_fpr(B1_VAL.label.values, proba(m, B1_VAL, cols))
    p2 = proba(m, BS2, cols)
    record('P5', 'trong miền BS1→BS2', fs, '-', '5G BS2', BS2.label, p2, t)
    R['P5_recall_theo_loai'][fs] = recall_by_cat(BS2.attack_cat, p2, t)

# ================================================================ P3. train gộp UNSW + BS1 → BS2 (và vẫn giữ được UNSW?)
print('P3 — gộp UNSW + BS1', flush=True)
R['P3_recall_theo_loai'] = {}
for nhan in ('ALL', 'DR'):
    tr, dv, fn = UN[nhan]
    for fs, cols in FS.items():
        m = fit(pd.concat([tr, B1_FIT]), cols)
        val = pd.concat([dv, B1_VAL])                    # ngưỡng chọn trên validation của cả hai miền nguồn
        t = thr_fpr(val.label.values, proba(m, val, cols))
        p2 = proba(m, BS2, cols)
        record('P3', 'gộp UNSW+BS1', fs, nhan, '5G BS2', BS2.label, p2, t)
        record('P3', 'gộp UNSW+BS1', fs, nhan, 'UNSW test-final' + ('' if nhan == 'ALL' else ' DR'), fn.label,
               proba(m, fn, cols), t)
        R['P3_recall_theo_loai'][f'{fs}|{nhan}'] = recall_by_cat(BS2.attack_cat, p2, t)

# ================================================================ P4. few-shot: cần bao nhiêu nhãn 5G?
print('P4 — few-shot', flush=True)
cols = LOI18
tr, dv, fn = UN['DR']
for k in FEW_K:
    for s in FEW_SEEDS:
        # lấy k% BS1-fit, stratify theo attack_cat; bảo đảm có cả 2 lớp
        sub = B1_FIT.groupby('attack_cat', group_keys=False).apply(
            lambda d: d.sample(max(1, int(round(len(d) * k))), random_state=s))
        vsub = B1_VAL.groupby('attack_cat', group_keys=False).apply(
            lambda d: d.sample(max(1, int(round(len(d) * k))), random_state=s))
        for ten, trn, val in [('few-shot chỉ 5G', sub, vsub),
                              ('few-shot UNSW-DR + 5G', pd.concat([tr, sub]), pd.concat([dv, vsub]))]:
            m = fit(trn, cols, seed=s)
            t = thr_fpr(val.label.values, proba(m, val, cols))
            extra = {'k_ty_le_BS1': k, 'n_nhan_5G': int(len(sub)), 'seed': s}
            record('P4', ten, 'LOI18', 'DR', '5G BS2', BS2.label, proba(m, BS2, cols), t, extra)
            if ten.startswith('few-shot UNSW'):
                record('P4', ten, 'LOI18', 'DR', 'UNSW test-final DR', fn.label, proba(m, fn, cols), t, extra)

# ================================================================ ghi kết quả
df = pd.DataFrame(ROWS)
df.round(4).to_csv(RES / '03_tat_ca_phuong_an.csv', index=False, encoding='utf-8-sig')
p4 = df[df.giao_thuc == 'P4'].groupby(['phuong_an', 'tap_dich', 'kieu_nguong', 'k_ty_le_BS1'])[
    ['n_nhan_5G', 'roc_auc', 'pr_auc', 'balanced_acc', 'mcc', 'recall', 'fpr']].agg(['mean', 'std']).round(4)
p4.to_csv(RES / '03_few_shot_tong_hop.csv', encoding='utf-8-sig')
json.dump(R, open(RES / '03_ket_qua.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)

pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30); pd.set_option('display.max_rows', 300)
show = ['giao_thuc', 'phuong_an', 'feature', 'can_nhan', 'tap_dich', 'kieu_nguong', 'roc_auc', 'pr_auc', 'pi',
        'balanced_acc', 'mcc', 'recall', 'fpr']
print(df[df.giao_thuc != 'P4'][show].round(4).to_string())
print(p4.to_string())
