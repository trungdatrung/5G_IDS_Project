"""Stress test: RF 31f (rerun07 rf_A_trainfit) under 5G-NIDD-like perturbations.
Usage: python -I -X utf8 stress5g.py <project_dir>
"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd, joblib
from sklearn.metrics import roc_auc_score

BASE = Path(sys.argv[1])
CATS = ['proto', 'service', 'state']
te = pd.read_parquet(BASE / 'data/cleaned/UNSW_NB15_testing-set.parquet')
tr = pd.read_parquet(BASE / 'data/cleaned/UNSW_NB15_training-set.parquet')
smap = pd.read_csv(BASE / 'data/cleaned/test_split_v3.csv').sort_values('test_index')
FIN = te[(smap['split'].values != 'test_dev')].copy()
FEATS = [c for c in te.columns if c not in ('label', 'attack_cat')]
model = joblib.load(BASE / 'reports/exp05/rf_A_trainfit.joblib')
X_of = lambda d: d[FEATS].astype({c: str for c in CATS})
_acc = float(((model.predict_proba(X_of(FIN))[:, 1] >= 0.5) == FIN.label.values).mean())
print('acc test-final @0.5 =', round(_acc, 6), '(NB07: 0.818620)', file=sys.stderr)
THR = 0.6949  # RF 31f threshold chosen on test-dev (FPR<=0.10), NB07
out = {}

# ---- 1. importance coverage
imp = pd.read_csv(BASE / 'models/random_forest_v2_importance.csv', index_col=0)['perm_mean'].clip(lower=0)
groups = {
    'A_truc_tiep': ['dur','proto','state','spkts','dpkts','sbytes','dbytes','rate','sload','dload',
                    'sloss','dloss','swin','dwin','stcpb','dtcpb','tcprtt','synack','ackdat','smean','dmean'],
    'B_can_xac_minh': ['sinpkt','dinpkt','sjit','djit'],
    'C_tinh_lai': ['service','ct_src_dport_ltm','ct_src_ltm'],
    'D_thieu_Bro': ['trans_depth','response_body_len','ct_flw_http_mthd'],
}
assert sorted(sum(groups.values(), [])) == sorted(FEATS), set(FEATS) ^ set(sum(groups.values(), []))
out['coverage'] = {g: {'n': len(c), 'perm_share': float(imp[c].sum() / imp.sum())} for g, c in groups.items()}

# ---- 2. perturbations
rng = np.random.default_rng(42)
def zero_bro(d):
    d = d.copy(); d[['trans_depth','response_body_len','ct_flw_http_mthd']] = 0; d['service'] = '-'; return d
def add_5g_latency(d, lo=0.010, hi=0.040):
    d = d.copy(); tcp = (d['synack'] > 0) | (d['ackdat'] > 0)
    d = d.astype({c: 'float64' for c in ['ackdat', 'synack', 'tcprtt', 'dur']})
    radio = rng.uniform(lo, hi, len(d)); mec = rng.uniform(0.001, 0.005, len(d))
    d.loc[tcp, 'ackdat'] += radio[tcp.values]; d.loc[tcp, 'synack'] += mec[tcp.values]
    d.loc[tcp, 'tcprtt'] = d.loc[tcp, 'synack'] + d.loc[tcp, 'ackdat']
    d.loc[tcp, 'dur'] += radio[tcp.values]
    return d
scen = {
    '0_goc': lambda d: d,
    '1_thieu_Bro': zero_bro,
    '2_tre_5G_10_40ms': add_5g_latency,
    '3_thieu_Bro+tre_5G': lambda d: add_5g_latency(zero_bro(d)),
    '4_thieu_Bro+tre_5G_30_80ms': lambda d: add_5g_latency(zero_bro(d), 0.030, 0.080),
}
y = FIN.label.values
res = {}
for k, f in scen.items():
    p = model.predict_proba(X_of(f(FIN)))[:, 1]
    r = {}
    for thr in (0.5, THR):
        pr = p >= thr
        r[f'@{thr}'] = {'FPR': float(pr[y == 0].mean()), 'Recall': float(pr[y == 1].mean()),
                        'BalAcc': float((pr[y == 1].mean() + 1 - pr[y == 0].mean()) / 2)}
        r[f'@{thr}']['recall_theo_loai'] = {c: float(pr[(FIN.attack_cat == c).values].mean())
                                           for c in ['Reconnaissance', 'DoS', 'Exploits', 'Fuzzers', 'Generic']}
    r['ROC_AUC'] = float(roc_auc_score(y, p))
    # FPR on Normal TCP flows that completed a handshake (closest analogue of 5G benign HTTPS/SSH)
    m = (y == 0) & (FIN.ackdat.values > 0)
    r['FPR_Normal_TCP_handshake@0.5'] = float((p[m] >= 0.5).mean()); r['n_Normal_TCP_handshake'] = int(m.sum())
    res[k] = r
out['scenarios'] = res

# ---- 3. how does the model treat short / single-packet flows (hping3 floods, scans)?
p0 = model.predict_proba(X_of(FIN))[:, 1]
short = (FIN.spkts <= 2) & (FIN.dpkts <= 1)
out['short_flows'] = {
    lab: {'n': int((short & (FIN.label == lab)).sum()),
          'ty_le_bi_bao_attack@0.5': float((p0[(short & (FIN.label == lab)).values] >= 0.5).mean())}
    for lab in (0, 1)}
out['short_by_proto_state_attack'] = (FIN[short & (FIN.label == 1)].groupby(['proto', 'state'], observed=True)
                                      .size().sort_values(ascending=False).head(8).to_dict())
out['short_by_proto_state_normal'] = (FIN[short & (FIN.label == 0)].groupby(['proto', 'state'], observed=True)
                                      .size().sort_values(ascending=False).head(8).to_dict())
out['short_by_proto_state_attack'] = {str(k): v for k, v in out['short_by_proto_state_attack'].items()}
out['short_by_proto_state_normal'] = {str(k): v for k, v in out['short_by_proto_state_normal'].items()}

# ---- 4. latency range seen in UNSW training Normal (is 10-40 ms in-distribution?)
nt = tr[(tr.label == 0) & (tr.ackdat > 0)]
at = tr[(tr.label == 1) & (tr.ackdat > 0)]
out['ackdat_train'] = {
    'Normal_q50_q90_q99': [float(x) for x in nt.ackdat.quantile([.5, .9, .99])],
    'Attack_q50_q90_q99': [float(x) for x in at.ackdat.quantile([.5, .9, .99])],
    'Normal_ty_le_ackdat>=10ms': float((nt.ackdat >= 0.010).mean()),
    'Attack_ty_le_ackdat>=10ms': float((at.ackdat >= 0.010).mean()),
}
print(json.dumps(out, indent=1, ensure_ascii=False))
