"""A1 — Model gộp UNSW-NB15 + 5G-NIDD (kế hoạch: docs/Ke_hoach_A_hoc_co_nhan_5G.md §2).

Chạy:  python -I -X utf8 experiment_5g_adaptation/src/A1_model_gop.py <thư mục dự án>      (QUICK=1 để chạy 40 cây)
Vào :  experiment_5gnidd/data/cleaned/5gnidd_unsw31.parquet
       data/cleaned/UNSW_NB15_{training,testing}-set.parquet, data/cleaned/test_split_v3.csv
       reports/exp05/rf_A_trainfit.joblib   (model RF 31 feature của NB07)      — tất cả CHỈ ĐỌC
Ra  :  experiment_5g_adaptation/results/A1_model_gop/{tables,figures}/*
       experiment_5g_adaptation/models/A1_model_gop/rf_gop_loi18.joblib

Biến thể:
  A1-0 chỉ UNSW (LOI18)                  A1-1 chỉ 5G (LOI18)
  A1-2 UNSW + 5G, trọng số bằng nhau     A1-3 UNSW + 5G, cân miền 50/50
  A1-4 UNSW + 5G đa lớp (19 lớp), điểm = 1 − P(Normal) − P(Benign)
  A1-5 NB07 giữ 300 cây UNSW + thêm 300 cây học trên 5G (warm_start, F31)
  A1-6 định tuyến: NB07 cho UNSW, RF công thức NB07 học trên 5G cho 5G (F31)
Ngưỡng: mỗi miền một ngưỡng, FPR ≤ 0,10 — UNSW chọn trên test-dev, 5G chọn trên 5G-val (20% BS1). BS2 chỉ để báo cáo.
"""
import os, sys, json, time, copy, warnings
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
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, precision_score, recall_score,
                             roc_auc_score, average_precision_score, confusion_matrix, matthews_corrcoef, roc_curve)
warnings.filterwarnings('ignore')

BASE = Path(sys.argv[1])
EXP = BASE / 'experiment_5g_adaptation'
TAB, FIG = EXP / 'results/A1_model_gop/tables', EXP / 'results/A1_model_gop/figures'
MOD = EXP / 'models/A1_model_gop'
for p in (TAB, FIG, MOD):
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
R = {'che_do': f'{"QUICK" if QUICK else "FULL"} | {N_TREES} cây | seed {RS}'}

def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)

# ---------------------------------------------------------------- hàm (giống experiment_5gnidd/src/02, 03)
def X_of(df, cols):
    return df[cols].astype({c: str for c in CATS if c in cols})

def rf_pipe(cols):
    pre = ColumnTransformer([('cat', OneHotEncoder(handle_unknown='ignore'), [c for c in CATS if c in cols])],
                            remainder='passthrough', verbose_feature_names_out=False, sparse_threshold=0.3)
    return Pipeline([('pre', pre), ('clf', RandomForestClassifier(**RF_PARAMS))])

def fit(df, cols, y, w=None):
    t = time.time()
    m = rf_pipe(cols).fit(X_of(df, cols), y, **({} if w is None else {'clf__sample_weight': w}))
    log(f'    fit {time.time() - t:5.0f}s | {len(df):,} dòng | {len(cols)} feature')
    return m

def thr_fpr(y, p, fmax=FPR_MAX):
    fpr, tpr, th = roc_curve(y, p)
    j = int(np.argmax(np.where(fpr <= fmax, tpr, -1.0)))
    return float(min(th[j], 1.0))

def ev(y, p, thr):
    y = np.asarray(y); pred = (p >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return dict(nguong=round(thr, 4), roc_auc=roc_auc_score(y, p), pr_auc=average_precision_score(y, p),
                accuracy=accuracy_score(y, pred), balanced_acc=balanced_accuracy_score(y, pred),
                mcc=matthews_corrcoef(y, pred), precision=precision_score(y, pred, zero_division=0),
                recall=recall_score(y, pred, zero_division=0), fpr=fp / max(fp + tn, 1),
                TN=int(tn), FP=int(fp), FN=int(fn), TP=int(tp))

def importance(pipe, cols):
    names = pipe.named_steps['pre'].get_feature_names_out()
    imp = pd.Series(pipe.named_steps['clf'].feature_importances_, index=names)
    grp = {n: next((c for c in CATS if n.startswith(c + '_')), n) for n in names}
    return imp.groupby(grp).sum().reindex(cols)

def plot_cm(ax, cm, rows, cols, title):
    cm = np.asarray(cm, float); rown = cm / np.maximum(cm.sum(1, keepdims=True), 1)
    ax.imshow(rown, cmap='Blues', vmin=0, vmax=1, aspect='auto')
    ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, rotation=40, ha='right', fontsize=8)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels(rows, fontsize=8)
    ax.set_xlabel('Predicted'); ax.set_ylabel('True'); ax.set_title(title, fontsize=9)
    small = len(cols) > 6
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            txt = f'{int(cm[i, j]):,}'.replace(',', '.') + ('' if small else f'\n{rown[i, j]:.1%}')
            ax.text(j, i, txt, ha='center', va='center', fontsize=6 if small else 9,
                    color='white' if rown[i, j] > 0.55 else 'black')

# ---------------------------------------------------------------- dữ liệu (chia giống experiment_5gnidd/src/03)
g = pd.read_parquet(BASE / 'experiment_5gnidd/data/cleaned/5gnidd_unsw31.parquet')
tr_u = pd.read_parquet(BASE / 'data/cleaned/UNSW_NB15_training-set.parquet')
te_u = pd.read_parquet(BASE / 'data/cleaned/UNSW_NB15_testing-set.parquet')
F31 = [c for c in tr_u.columns if c not in ('label', 'attack_cat')]
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
MIX = pd.concat([U_TR, G_TR], ignore_index=True)
n_u, n_g = len(U_TR), len(G_TR)
W_CAN = np.r_[np.full(n_u, 0.5 * (n_u + n_g) / n_u), np.full(n_g, 0.5 * (n_u + n_g) / n_g)]   # mỗi miền 50% tổng trọng số
R['kich_thuoc'] = {'UNSW_train_fit': n_u, 'UNSW_test_dev': len(U_DEV), 'UNSW_test_final': len(U_FIN),
                   '5G_train': n_g, '5G_val': len(G_VAL), '5G_test_BS2': len(BS2)}
log(R['kich_thuoc'])

# ---------------------------------------------------------------- huấn luyện 7 biến thể
# mỗi biến thể = hàm điểm cho miền UNSW và cho miền 5G (A1-6 dùng hai model khác nhau)
S = {}
log('A1-0 chỉ UNSW');           m0 = fit(U_TR, LOI18, U_TR.label.values)
log('A1-1 chỉ 5G');             m1 = fit(G_TR, LOI18, G_TR.label.values)
log('A1-2 gộp, bằng nhau');     m2 = fit(MIX, LOI18, MIX.label.values)
log('A1-3 gộp, cân miền');      m3 = fit(MIX, LOI18, MIX.label.values, W_CAN)
log('A1-4 gộp, đa lớp');        m4 = fit(MIX, LOI18, MIX.attack_cat.values)
for k, m in [('A1-0', m0), ('A1-1', m1), ('A1-2', m2), ('A1-3', m3)]:
    S[k] = (lambda d, m=m: m.predict_proba(X_of(d, LOI18))[:, 1],) * 2
lanh = [list(m4.classes_).index(c) for c in ('Normal', 'Benign')]
S['A1-4'] = (lambda d: 1.0 - m4.predict_proba(X_of(d, LOI18))[:, lanh].sum(1),) * 2

nb07 = joblib.load(BASE / 'reports/exp05/rf_A_trainfit.joblib')            # bước: 'preprocess', 'rf'
acc0 = accuracy_score(U_FIN.label, (nb07.predict_proba(X_of(U_FIN, F31))[:, 1] >= .5).astype(int))
assert abs(acc0 - 0.818620) < 5e-4, acc0                                    # đúng model NB07
R['kiem_chung_NB07_accuracy_UNSW_test-final@0.5'] = round(float(acc0), 6)
log('A1-5 NB07 + warm_start')
m5 = copy.deepcopy(nb07)
m5.named_steps['rf'].set_params(warm_start=True, n_estimators=300 + N_TREES)
t = time.time()
m5.named_steps['rf'].fit(m5.named_steps['preprocess'].transform(X_of(G_TR, F31)), G_TR.label.values)
log(f'    fit {time.time() - t:5.0f}s | {n_g:,} dòng | thêm {N_TREES} cây vào 300 cây NB07')
S['A1-5'] = (lambda d: m5.predict_proba(X_of(d, F31))[:, 1],) * 2
log('A1-6 định tuyến');         m6 = fit(G_TR, F31, G_TR.label.values)
S['A1-6'] = (lambda d: nb07.predict_proba(X_of(d, F31))[:, 1], lambda d: m6.predict_proba(X_of(d, F31))[:, 1])

# ---------------------------------------------------------------- đánh giá: ngưỡng riêng từng miền
MIEN = {'UNSW': (U_DEV, U_FIN, 'UNSW test-final'), '5G': (G_VAL, BS2, '5G BS2')}
rows, rec, R['nguong'], P = [], [], {}, {}
for k, (f_u, f_g) in S.items():
    R['nguong'][k] = {}
    for mien, f in [('UNSW', f_u), ('5G', f_g)]:
        dv, ts, ten = MIEN[mien]
        t = thr_fpr(dv.label.values, f(dv)); p = f(ts)
        R['nguong'][k][mien] = t; P[(k, mien)] = (p, t)
        for kieu, tt in [('@0,5', 0.5), ('@nguong_mien', t)]:
            rows.append({'bien_the': k, 'tap_test': ten, 'n': len(ts), 'pi': round(float(ts.label.mean()), 4),
                         'kieu_nguong': kieu, **ev(ts.label, p, tt)})
        r = pd.Series(p >= t).groupby(ts.attack_cat.values).agg(['mean', 'size'])
        rec += [{'bien_the': k, 'tap_test': ten, 'loai': c, 'n': int(v['size']), 'ty_le_bao_attack': round(float(v['mean']), 4)}
                for c, v in r.iterrows()]
TH = pd.DataFrame(rows)
TH.round(4).to_csv(TAB / 'A1_tong_hop.csv', index=False, encoding='utf-8-sig')
RC = pd.DataFrame(rec)
RC.pivot_table(index=['tap_test', 'loai', 'n'], columns='bien_the', values='ty_le_bao_attack').reset_index().to_csv(
    TAB / 'A1_recall_theo_loai.csv', index=False, encoding='utf-8-sig')
pd.DataFrame({'A1-0': importance(m0, LOI18), 'A1-2': importance(m2, LOI18), 'A1-3': importance(m3, LOI18)}).sort_values(
    'A1-2', ascending=False).round(5).to_csv(TAB / 'A1_importance.csv', encoding='utf-8-sig')

# ---------------------------------------------------------------- hình: ma trận nhầm lẫn
for k in S:
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.6))
    for ax, mien in zip(axs, ('UNSW', '5G')):
        ts = MIEN[mien][1]; p, t = P[(k, mien)]
        cm = confusion_matrix(ts.label, (p >= t).astype(int), labels=[0, 1])
        plot_cm(ax, cm, ['Lành tính', 'Attack'], ['Lành tính', 'Attack'], f'{k} · {MIEN[mien][2]} @{t:.3f}')
    fig.tight_layout(); fig.savefig(FIG / f'cm_{k}_nhi_phan.png', dpi=130); plt.close(fig)
for mien in ('UNSW', '5G'):
    ts = MIEN[mien][1]
    pred = m4.predict(X_of(ts, LOI18))
    rows_ = sorted(ts.attack_cat.unique(), key=lambda c: (c not in ('Normal', 'Benign'), c))
    cols_ = sorted(m4.classes_, key=lambda c: (c not in ('Normal', 'Benign'), c))
    cm = pd.crosstab(ts.attack_cat.values, pred).reindex(index=rows_, columns=cols_, fill_value=0)
    fig, ax = plt.subplots(figsize=(0.55 * len(cols_) + 3, 0.5 * len(rows_) + 2.2))
    plot_cm(ax, cm.values, rows_, cols_, f'A1-4 đa lớp · {MIEN[mien][2]} (cột: 19 lớp model)')
    fig.tight_layout(); fig.savefig(FIG / f'cm_A1-4_da_lop_{mien}.png', dpi=130); plt.close(fig)
    cm.to_csv(TAB / f'A1-4_cm_da_lop_{mien}.csv', encoding='utf-8-sig')

# ---------------------------------------------------------------- điểm dừng + chọn model (kế hoạch §2, §7)
def get(k, mien, kieu='@nguong_mien'):
    ten = MIEN[mien][2]
    return TH[(TH.bien_the == k) & (TH.tap_test == ten) & (TH.kieu_nguong == kieu)].iloc[0]
roc_u0 = get('A1-0', 'UNSW').roc_auc
dung, dat = {}, {}
for k in ('A1-2', 'A1-3'):
    gg, uu = get(k, '5G'), get(k, 'UNSW')
    dung[k] = {'BS2_roc>=0.99': bool(gg.roc_auc >= 0.99), 'UNSW_giam<=0.01': bool(roc_u0 - uu.roc_auc <= 0.01)}
    dat[k] = {'BS2_roc>=0.995': bool(gg.roc_auc >= 0.995), 'BS2_fpr<=0.10': bool(gg.fpr <= 0.10),
              'BS2_recall>=0.99': bool(gg.recall >= 0.99), 'UNSW_giam<=0.005': bool(roc_u0 - uu.roc_auc <= 0.005),
              'UNSW_bal_acc>=0.865': bool(uu.balanced_acc >= 0.865),
              'diem_bal_acc_2_mien': float(gg.balanced_acc + uu.balanced_acc)}
R['diem_dung'] = {k: {**v, 'phai_dung': not all(v.values())} for k, v in dung.items()}
R['ky_vong_A1-2_A1-3'] = dat
hop_le = [k for k in ('A1-2', 'A1-3') if all(v for n, v in dat[k].items() if n != 'diem_bal_acc_2_mien')]
chon = None
if hop_le:
    chon = max(hop_le, key=lambda k: dat[k]['diem_bal_acc_2_mien'])
    if chon == 'A1-3' and 'A1-2' in hop_le and dat['A1-3']['diem_bal_acc_2_mien'] - dat['A1-2']['diem_bal_acc_2_mien'] <= 0.005:
        chon = 'A1-2'                                                       # gần bằng nhau → chọn bản đơn giản
R['model_chon'] = chon
if chon and not any(v['phai_dung'] for v in R['diem_dung'].values()):
    joblib.dump({'pipeline': {'A1-2': m2, 'A1-3': m3}[chon], 'features': LOI18, 'bien_the': chon,
                 'nguong': {'unsw': R['nguong'][chon]['UNSW'], '5g': R['nguong'][chon]['5G']},
                 'du_lieu_train': 'UNSW train-fit (79.147) + 5G-NIDD BS1 80% (166.411)', 'ngay': time.strftime('%Y-%m-%d'),
                 'che_do': R['che_do']}, MOD / 'rf_gop_loi18.joblib', compress=3)
    log(f'Đã lưu model {chon} → models/A1_model_gop/rf_gop_loi18.joblib')
else:
    log(f'KHÔNG lưu model: chọn={chon}, điểm dừng={R["diem_dung"]}')

json.dump(R, open(TAB / 'A1_ket_qua.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
print(TH[['bien_the', 'tap_test', 'kieu_nguong', 'nguong', 'roc_auc', 'pr_auc', 'balanced_acc', 'mcc', 'recall', 'fpr']]
      .round(4).to_string())
print(json.dumps({k: R[k] for k in ('diem_dung', 'ky_vong_A1-2_A1-3', 'model_chon')}, ensure_ascii=False, indent=1))
