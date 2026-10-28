"""Chuyển 5G-NIDD (Argus, 113 trường) sang đúng 31 feature của model RF UNSW-NB15.

Chạy:  python -I -X utf8 reports/5gnidd/build_5gnidd_unsw31.py <thư mục dự án>
Vào :  data/5gnidd/extracted/BTS1_BTS2_fields_preserved/BTS1_BTS2_fields_preserved.csv
       data/5gnidd/extracted/BTS_1/BTS_1.csv (chỉ để lấy số dòng BS1)
       data/cleaned/UNSW_NB15_training-set.parquet (bảng tra sloss/dloss, model sjit/djit)
Ra  :  data/5gnidd/cleaned/5gnidd_unsw31_full.parquet   mọi dòng, 31 feature + cột meta
       data/5gnidd/cleaned/5gnidd_unsw31.parquet        tập dùng để validate (nhãn đã sửa, khử trùng lặp như NB01)
       data/5gnidd/cleaned/5gnidd_unsw31_raw.parquet    biến thể "ánh xạ thô" (không hiệu chỉnh), cùng các dòng
       reports/5gnidd/build_stats.json
"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

BASE = Path(sys.argv[1])
SRC = BASE / 'data/5gnidd/extracted'
OUT = BASE / 'data/5gnidd/cleaned'; OUT.mkdir(parents=True, exist_ok=True)
REP = BASE / 'reports/5gnidd'
TARGET_IP = '10.41.150.68'          # server nạn nhân trong MEC
ETH = 14                            # byte header Ethernet mỗi gói (UNSW đếm từ lớp IP)
FEATS = ['dur', 'proto', 'service', 'state', 'spkts', 'dpkts', 'sbytes', 'dbytes', 'rate', 'sload', 'dload',
         'sloss', 'dloss', 'sinpkt', 'dinpkt', 'sjit', 'djit', 'swin', 'stcpb', 'dtcpb', 'dwin', 'tcprtt',
         'synack', 'ackdat', 'smean', 'dmean', 'trans_depth', 'response_body_len', 'ct_src_dport_ltm',
         'ct_flw_http_mthd', 'ct_src_ltm']
CATS = ['proto', 'service', 'state']
# tên cổng (Argus đã phân giải theo /etc/services) -> giá trị `service` của Bro trong UNSW
PORT2SERVICE = {'http': 'http', 'https': 'ssl', 'domain': 'dns', 'ssh': 'ssh', 'ftp': 'ftp', 'ftp-data': 'ftp-data',
                'smtp': 'smtp', 'pop3': 'pop3', 'snmp': 'snmp', 'bootps': 'dhcp', 'bootpc': 'dhcp',
                'ircd': 'irc', 'irc': 'irc', 'radius': 'radius'}
S = {}

# ---------------------------------------------------------------- 1. nạp
USE = ['SrcAddr', 'DstAddr', 'Sport', 'Dport', 'Proto', 'State', 'Dur', 'SrcPkts', 'DstPkts', 'SrcBytes', 'DstBytes',
       'SAppBytes', 'DAppBytes', 'Rate', 'SrcLoss', 'DstLoss', 'SrcWin', 'DstWin', 'SrcTCPBase', 'DstTCPBase',
       'TcpRtt', 'SynAck', 'AckDat', 'sMeanPktSz', 'dMeanPktSz', 'SrcLoad', 'DstLoad', 'Label', 'Attack Type', 'Attack Tool']
g = pd.read_csv(SRC / 'BTS1_BTS2_fields_preserved/BTS1_BTS2_fields_preserved.csv', usecols=USE, low_memory=False)
n_bs1 = sum(1 for _ in open(SRC / 'BTS_1/BTS_1.csv', 'rb')) - 1
g['bs'] = np.where(np.arange(len(g)) < n_bs1, 'BS1', 'BS2')
S['n_raw'] = len(g); S['n_bs'] = g.bs.value_counts().to_dict()

# ---------------------------------------------------------------- 2. lỗi nhãn: bản sao flood của kẻ tấn công BS2 nằm trong file BS1, nhãn Benign
attackers = {bs: set(g[(g.bs == bs) & (g.Label == 'Malicious')].SrcAddr) for bs in ('BS1', 'BS2')}
other = {'BS1': attackers['BS2'] - attackers['BS1'], 'BS2': attackers['BS1'] - attackers['BS2']}
dup_cap = np.zeros(len(g), bool)
for bs in ('BS1', 'BS2'):
    dup_cap |= ((g.bs == bs) & (g.Label == 'Benign') & g.SrcAddr.isin(other[bs]) & (g.DstAddr == TARGET_IP)).values
g['dup_capture'] = dup_cap
S['dup_capture'] = g[dup_cap].groupby(['bs', 'SrcAddr', 'Proto']).size().rename('n').reset_index().to_dict('records')
g['label_published'] = (g.Label == 'Malicious').astype('int8')
g['attack_cat'] = g['Attack Type'].astype(str)

# ---------------------------------------------------------------- 3. ánh xạ trực tiếp / công thức đã kiểm chứng
f = pd.DataFrame(index=g.index)
f['dur'] = g.Dur.astype('float64')
f['proto'] = g.Proto.astype(str)
f['state'] = g.State.astype(str)
# Argus của 5G-NIDD tách UDP một chiều thành REQ/INT; Argus của UNSW gần như luôn ghi INT (8.900 INT vs 118 REQ)
f.loc[(f.proto == 'udp') & (f.state == 'REQ'), 'state'] = 'INT'
f['spkts'] = g.SrcPkts.astype('float64'); f['dpkts'] = g.DstPkts.astype('float64')
f['sbytes'] = (g.SrcBytes - ETH * g.SrcPkts).clip(lower=0).astype('float64')      # bỏ header Ethernet
f['dbytes'] = (g.DstBytes - ETH * g.DstPkts).clip(lower=0).astype('float64')
f['rate'] = g.Rate.astype('float64')                                              # (Tot-1)/Dur, giống UNSW
pos = (f.dur > 0)
f['sload'] = np.where(pos & (f.spkts > 1), 8 * f.sbytes * (f.spkts - 1) / f.spkts.clip(lower=1) / f.dur.where(pos, 1), 0.0)
f['dload'] = np.where(pos & (f.dpkts > 1), 8 * f.dbytes * (f.dpkts - 1) / f.dpkts.clip(lower=1) / f.dur.where(pos, 1), 0.0)
f['smean'] = np.where(f.spkts > 0, np.round(f.sbytes / f.spkts.clip(lower=1)), 0.0)
f['dmean'] = np.where(f.dpkts > 0, np.round(f.dbytes / f.dpkts.clip(lower=1)), 0.0)
f['tcprtt'] = g.TcpRtt.astype('float64'); f['synack'] = g.SynAck.astype('float64'); f['ackdat'] = g.AckDat.astype('float64')
f['stcpb'] = g.SrcTCPBase.fillna(0).astype('float64'); f['dtcpb'] = g.DstTCPBase.fillna(0).astype('float64')
tcp = (f.proto == 'tcp')
f['swin'] = np.where(tcp, 255.0, 0.0)                                             # UNSW: tcp -> 255, còn lại 0
f['dwin'] = np.where(tcp & (f.dpkts > 0), 255.0, 0.0)

# ---------------------------------------------------------------- 4. inter-packet: xấp xỉ từ Dur (SIntPkt/DIntPkt rỗng 100% trong 5G-NIDD)
def inpkt(dur, n):
    dur, n = np.asarray(dur, 'float64'), np.asarray(n, 'float64')
    return np.where((n > 1) & (dur > 0), dur * 1000.0 / np.maximum(n - 1, 1), 0.0)
f['sinpkt'] = inpkt(f.dur.values, f.spkts.values); f['dinpkt'] = inpkt(f.dur.values, f.dpkts.values)

# ---------------------------------------------------------------- 5. bảng tra / model học từ UNSW-train (không dùng nhãn)
u = pd.read_parquet(BASE / 'data/cleaned/UNSW_NB15_training-set.parquet')
for c in u.columns:
    if c not in CATS + ['attack_cat']: u[c] = u[c].astype('float64')
u['proto'] = u.proto.astype(str); u['state'] = u.state.astype(str)

def loss_lookup(df, side):
    n, l = ('spkts', 'sloss') if side == 's' else ('dpkts', 'dloss')
    t = u.assign(k=u[n].clip(upper=40))
    m3 = t.groupby(['proto', 'state', 'k'])[l].median(); m2 = t.groupby(['proto', 'state'])[l].median(); m1 = t.groupby('proto')[l].median()
    k = df[n].clip(upper=40)
    v = pd.Series(pd.MultiIndex.from_arrays([df.proto, df.state, k]).map(m3.to_dict()), index=df.index, dtype='float64')
    v = v.fillna(pd.Series(pd.MultiIndex.from_arrays([df.proto, df.state]).map(m2.to_dict()), index=df.index, dtype='float64'))
    v = v.fillna(df.proto.map(m1)).fillna(0.0)
    return v.where(df[n] > 0, 0.0)
f['sloss'] = loss_lookup(f, 's'); f['dloss'] = loss_lookup(f, 'd')

def jit_features(d, sinp, n, side):
    return np.c_[np.log1p(sinp), np.log1p(d[n]), np.log1p(d['dur']), np.log1p(d['sbytes' if side == 's' else 'dbytes']),
                 (d['proto'] == 'tcp').astype(float), (d['proto'] == 'udp').astype(float)]
JIT = {}
for side, n, j in [('s', 'spkts', 'sjit'), ('d', 'dpkts', 'djit')]:
    u_inp = inpkt(u.dur.values, u[n].values)          # huấn luyện trên đúng phép xấp xỉ sẽ dùng cho 5G
    X = jit_features(u, u_inp, n, side)
    reg = HistGradientBoostingRegressor(max_iter=300, random_state=42).fit(X, np.log1p(u[j]))
    JIT[side] = reg
    pred = np.expm1(reg.predict(jit_features(f, f['sinpkt' if side == 's' else 'dinpkt'].values, n, side))).clip(min=0)
    f[j] = np.where(f[n] > 2, pred, 0.0)              # UNSW: jitter = 0 với 98% flow <= 2 gói

# ---------------------------------------------------------------- 6. feature Bro: suy từ cổng
# SAppBytes/DAppBytes = 0 ở mọi dòng 5G-NIDD (Argus không bật -A) nên không dùng được để biết có payload.
# UNSW: tcp chưa xong bắt tay (ackdat = 0) -> service '-' ở 96,4% dòng; UDP gán theo cổng (dns).
dport = g.Dport.astype(str)
svc = dport.map(PORT2SERVICE).fillna('-')
f['service'] = np.where((f.proto != 'tcp') | (f.ackdat > 0), svc, '-')
http_req = (f.service == 'http')                       # UNSW: http + bắt tay xong -> trans_depth = 1 ở 91%
f['trans_depth'] = http_req.astype('float64')
f['ct_flw_http_mthd'] = http_req.astype('float64')
f['response_body_len'] = 0.0                                                        # không tách được body khỏi header HTTP

# ---------------------------------------------------------------- 7. ct_*: cửa sổ 100 bản ghi gần nhất, theo thứ tự trong từng file BS
def ct_window(keys, w=100):
    out = np.empty(len(keys), dtype='float64')
    codes = pd.factorize(keys)[0]
    order = np.argsort(codes, kind='stable')
    sc = codes[order]; bounds = np.flatnonzero(np.r_[True, sc[1:] != sc[:-1], True])
    for a, b in zip(bounds[:-1], bounds[1:]):
        p = order[a:b]                                 # vị trí (đã tăng dần) của một khoá
        out[p] = np.arange(len(p)) - np.searchsorted(p, p - (w - 1)) + 1
    return out
f['ct_src_ltm'] = 0.0; f['ct_src_dport_ltm'] = 0.0
for bs in ('BS1', 'BS2'):
    m = (g.bs == bs).values
    f.loc[m, 'ct_src_ltm'] = ct_window(g.SrcAddr[m].astype(str).values)
    f.loc[m, 'ct_src_dport_ltm'] = ct_window((g.SrcAddr[m].astype(str) + '|' + dport[m]).values)

f = f[FEATS]
assert not f.isna().any().any(), f.columns[f.isna().any()].tolist()
meta = pd.DataFrame({'bs': g.bs, 'attack_cat': g.attack_cat, 'attack_tool': g['Attack Tool'].astype(str),
                     'label_published': g.label_published, 'dup_capture': g.dup_capture,
                     'src_addr': g.SrcAddr.astype(str)})
full = pd.concat([f, meta], axis=1)
full.to_parquet(OUT / '5gnidd_unsw31_full.parquet')

# ---------------------------------------------------------------- 8. biến thể ánh xạ thô (không hiệu chỉnh) để đo độ nhạy
raw = f.copy()
raw['sbytes'] = g.SrcBytes.astype('float64'); raw['dbytes'] = g.DstBytes.astype('float64')
raw['sload'] = g.SrcLoad.astype('float64'); raw['dload'] = g.DstLoad.astype('float64')
raw['smean'] = g.sMeanPktSz.astype('float64'); raw['dmean'] = g.dMeanPktSz.astype('float64')
raw['sloss'] = g.SrcLoss.astype('float64'); raw['dloss'] = g.DstLoss.astype('float64')
raw['swin'] = g.SrcWin.fillna(0).astype('float64'); raw['dwin'] = g.DstWin.fillna(0).astype('float64')
raw[['sinpkt', 'dinpkt', 'sjit', 'djit', 'trans_depth', 'response_body_len', 'ct_flw_http_mthd']] = 0.0
raw['service'] = '-'; raw[['ct_src_ltm', 'ct_src_dport_ltm']] = 1.0; raw['state'] = g.State.astype(str)

# ---------------------------------------------------------------- 9. tập validate: bỏ bản sao bắt nhầm, khử trùng lặp như NB01
keep = ~g.dup_capture.values
d = full[keep].copy(); d['label'] = d.label_published
S['after_drop_dup_capture'] = int(keep.sum())
n0 = len(d)
d = d.drop_duplicates(subset=FEATS + ['label'])
S['nb01_duplicates_removed'] = n0 - len(d)
nl = d.groupby(FEATS, observed=True, dropna=False)['label'].transform('nunique')
S['nb01_contradictory_removed'] = int((nl > 1).sum())
d = d[nl == 1]
S['n_final'] = len(d)
S['final_by_class'] = d.attack_cat.value_counts().to_dict()
S['final_by_bs_class'] = {bs: d[d.bs == bs].attack_cat.value_counts().to_dict() for bs in ('BS1', 'BS2')}
d.to_parquet(OUT / '5gnidd_unsw31.parquet')
r = raw.loc[d.index].copy(); r[['bs', 'attack_cat', 'label']] = d[['bs', 'attack_cat', 'label']]
r.to_parquet(OUT / '5gnidd_unsw31_raw.parquet')

# ---------------------------------------------------------------- 10. kiểm chứng phép xấp xỉ trên chính UNSW-test (round-trip)
te = pd.read_parquet(BASE / 'data/cleaned/UNSW_NB15_testing-set.parquet')
for c in te.columns:
    if c not in CATS + ['attack_cat']: te[c] = te[c].astype('float64')
rt = {}
for side, n, i, j in [('s', 'spkts', 'sinpkt', 'sjit'), ('d', 'dpkts', 'dinpkt', 'djit')]:
    ap = inpkt(te.dur.values, te[n].values)
    jp = np.where(te[n] > 2, np.expm1(JIT[side].predict(jit_features(te.assign(proto=te.proto.astype(str)), ap, n, side))).clip(min=0), 0.0)
    rt[i] = {'spearman': float(pd.Series(ap).corr(te[i].reset_index(drop=True), method='spearman')),
             'within_20pct': float(np.mean(np.abs(ap - te[i].values) <= 0.2 * np.maximum(te[i].values, 1e-9)))}
    rt[j] = {'spearman': float(pd.Series(jp).corr(te[j].reset_index(drop=True), method='spearman'))}
    te[i], te[j] = ap, jp                              # thay bằng đúng giá trị xấp xỉ sẽ dùng cho 5G
te['proto'] = te.proto.astype(str); te['state'] = te.state.astype(str)
for side, l in [('s', 'sloss'), ('d', 'dloss')]:
    est = loss_lookup(te, side)
    rt[l] = {'exact_match': float((est.values == te[l].values).mean()),
             'spearman': float(pd.Series(est.values).corr(pd.Series(te[l].values), method='spearman'))}
    te[l] = est
te['swin'] = np.where(te.proto == 'tcp', 255.0, 0.0); te['dwin'] = np.where((te.proto == 'tcp') & (te.dpkts > 0), 255.0, 0.0)
http_req = (te.service.astype(str) == 'http') & (te.sbytes > 0) & (te.dbytes > 0)
rt['trans_depth_agree'] = float((http_req.astype(float).values == te.trans_depth.values).mean())
te['trans_depth'] = http_req.astype(float); te['ct_flw_http_mthd'] = http_req.astype(float); te['response_body_len'] = 0.0
te.to_parquet(OUT / 'unsw_test_roundtrip.parquet')     # UNSW-test sau đúng các phép xấp xỉ của 5G -> đo model tụt bao nhiêu
S['roundtrip_feature_fidelity_unsw_test'] = rt
json.dump(S, open(REP / 'build_stats.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print(json.dumps(S, ensure_ascii=False, indent=1, default=str))
