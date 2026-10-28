"""Bước 1 — Giải nén và làm sạch 5G-NIDD về đúng 31 feature của UNSW-NB15 đã làm sạch (data/cleaned).

Chạy:  python -I -X utf8 experiment_5gnidd/src/01_lam_sach_5gnidd.py <thư mục dự án>
Vào :  experiment_5gnidd/data/raw/BTS1_BTS2_fields_preserved.zip, BTS_1.zip   (tải từ Fairdata)
       data/cleaned/UNSW_NB15_training-set.parquet   (CHỈ ĐỌC: bảng tra sloss/dloss, model jitter)
Ra  :  experiment_5gnidd/data/cleaned/5gnidd_unsw31.parquet       tập dùng để train/test
       experiment_5gnidd/data/cleaned/5gnidd_unsw31_full.parquet  mọi dòng, kèm nhãn công bố + cờ lỗi nhãn
       experiment_5gnidd/results/01_thong_ke_lam_sach.json

Mọi thứ ghi ra đều nằm trong experiment_5gnidd/. Không file nào ngoài thư mục này bị ghi.
Quy tắc ánh xạ giống reports/5gnidd/build_5gnidd_unsw31.py (xem Bao_cao_doi_chieu_5G-NIDD.md §3).
"""
import sys, json, zipfile
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

BASE = Path(sys.argv[1])
EXP = BASE / 'experiment_5gnidd'
RAW, EXT, OUT, RES = EXP / 'data/raw', EXP / 'data/extracted', EXP / 'data/cleaned', EXP / 'results'
for p in (EXT, OUT, RES):
    p.mkdir(parents=True, exist_ok=True)
TARGET_IP = '10.41.150.68'          # server nạn nhân trong MEC
ETH = 14                            # byte header Ethernet mỗi gói (UNSW đếm từ lớp IP)
FEATS = ['dur', 'proto', 'service', 'state', 'spkts', 'dpkts', 'sbytes', 'dbytes', 'rate', 'sload', 'dload',
         'sloss', 'dloss', 'sinpkt', 'dinpkt', 'sjit', 'djit', 'swin', 'stcpb', 'dtcpb', 'dwin', 'tcprtt',
         'synack', 'ackdat', 'smean', 'dmean', 'trans_depth', 'response_body_len', 'ct_src_dport_ltm',
         'ct_flw_http_mthd', 'ct_src_ltm']
CATS = ['proto', 'service', 'state']
PORT2SERVICE = {'http': 'http', 'https': 'ssl', 'domain': 'dns', 'ssh': 'ssh', 'ftp': 'ftp', 'ftp-data': 'ftp-data',
                'smtp': 'smtp', 'pop3': 'pop3', 'snmp': 'snmp', 'bootps': 'dhcp', 'bootpc': 'dhcp',
                'ircd': 'irc', 'irc': 'irc', 'radius': 'radius'}
S = {}

# ---------------------------------------------------------------- 0. giải nén (chỉ đọc file .csv trong zip, không chạy gì)
for z in ('BTS1_BTS2_fields_preserved.zip', 'BTS_1.zip'):
    with zipfile.ZipFile(RAW / z) as zf:
        for m in zf.namelist():
            if m.lower().endswith('.csv') and '..' not in m and not m.startswith(('/', '\\')):
                dst = EXT / Path(m).name
                if not dst.exists():
                    dst.write_bytes(zf.read(m))
SRC_ALL = next(EXT.glob('BTS1_BTS2_fields_preserved*.csv'))
SRC_BS1 = next(EXT.glob('BTS_1*.csv'))

# ---------------------------------------------------------------- 1. nạp
USE = ['SrcAddr', 'DstAddr', 'Sport', 'Dport', 'Proto', 'State', 'Dur', 'SrcPkts', 'DstPkts', 'SrcBytes', 'DstBytes',
       'Rate', 'SrcTCPBase', 'DstTCPBase', 'TcpRtt', 'SynAck', 'AckDat', 'Label', 'Attack Type', 'Attack Tool']
g = pd.read_csv(SRC_ALL, usecols=USE, low_memory=False)
n_bs1 = sum(1 for _ in open(SRC_BS1, 'rb')) - 1
g['bs'] = np.where(np.arange(len(g)) < n_bs1, 'BS1', 'BS2')
S['n_tho'] = len(g); S['n_theo_tram'] = g.bs.value_counts().to_dict()
S['nhan_cong_bo'] = g['Attack Type'].astype(str).value_counts().to_dict()

# ---------------------------------------------------------------- 2. lỗi nhãn: bản sao flood của kẻ tấn công trạm kia, nhãn Benign
attackers = {bs: set(g[(g.bs == bs) & (g.Label == 'Malicious')].SrcAddr) for bs in ('BS1', 'BS2')}
other = {'BS1': attackers['BS2'] - attackers['BS1'], 'BS2': attackers['BS1'] - attackers['BS2']}
dup_cap = np.zeros(len(g), bool)
for bs in ('BS1', 'BS2'):
    dup_cap |= ((g.bs == bs) & (g.Label == 'Benign') & g.SrcAddr.isin(other[bs]) & (g.DstAddr == TARGET_IP)).values
g['dup_capture'] = dup_cap
S['loi_nhan_ban_sao_bat_nham'] = int(dup_cap.sum())
g['label_published'] = (g.Label == 'Malicious').astype('int8')
g['attack_cat'] = g['Attack Type'].astype(str)

# ---------------------------------------------------------------- 3. ánh xạ trực tiếp / công thức Argus đã kiểm chứng
f = pd.DataFrame(index=g.index)
f['dur'] = g.Dur.astype('float64')
f['proto'] = g.Proto.astype(str)
f['state'] = g.State.astype(str)
f.loc[(f.proto == 'udp') & (f.state == 'REQ'), 'state'] = 'INT'                   # UNSW: UDP một chiều = INT
f['spkts'] = g.SrcPkts.astype('float64'); f['dpkts'] = g.DstPkts.astype('float64')
f['sbytes'] = (g.SrcBytes - ETH * g.SrcPkts).clip(lower=0).astype('float64')      # bỏ header Ethernet
f['dbytes'] = (g.DstBytes - ETH * g.DstPkts).clip(lower=0).astype('float64')
f['rate'] = g.Rate.astype('float64')
pos = (f.dur > 0)
f['sload'] = np.where(pos & (f.spkts > 1), 8 * f.sbytes * (f.spkts - 1) / f.spkts.clip(lower=1) / f.dur.where(pos, 1), 0.0)
f['dload'] = np.where(pos & (f.dpkts > 1), 8 * f.dbytes * (f.dpkts - 1) / f.dpkts.clip(lower=1) / f.dur.where(pos, 1), 0.0)
f['smean'] = np.where(f.spkts > 0, np.round(f.sbytes / f.spkts.clip(lower=1)), 0.0)
f['dmean'] = np.where(f.dpkts > 0, np.round(f.dbytes / f.dpkts.clip(lower=1)), 0.0)
f['tcprtt'] = g.TcpRtt.astype('float64'); f['synack'] = g.SynAck.astype('float64'); f['ackdat'] = g.AckDat.astype('float64')
f['stcpb'] = g.SrcTCPBase.fillna(0).astype('float64'); f['dtcpb'] = g.DstTCPBase.fillna(0).astype('float64')
tcp = (f.proto == 'tcp')
f['swin'] = np.where(tcp, 255.0, 0.0)                                             # UNSW chỉ có 0/255
f['dwin'] = np.where(tcp & (f.dpkts > 0), 255.0, 0.0)

# ---------------------------------------------------------------- 4. inter-packet: xấp xỉ từ Dur (SIntPkt/DIntPkt rỗng 100%)
def inpkt(dur, n):
    dur, n = np.asarray(dur, 'float64'), np.asarray(n, 'float64')
    return np.where((n > 1) & (dur > 0), dur * 1000.0 / np.maximum(n - 1, 1), 0.0)
f['sinpkt'] = inpkt(f.dur.values, f.spkts.values); f['dinpkt'] = inpkt(f.dur.values, f.dpkts.values)

# ---------------------------------------------------------------- 5. bảng tra / model học từ UNSW-train (không dùng nhãn)
u = pd.read_parquet(BASE / 'data/cleaned/UNSW_NB15_training-set.parquet')
for c in u.columns:
    if c not in CATS + ['attack_cat']:
        u[c] = u[c].astype('float64')
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
for side, n, j in [('s', 'spkts', 'sjit'), ('d', 'dpkts', 'djit')]:
    X = jit_features(u, inpkt(u.dur.values, u[n].values), n, side)
    reg = HistGradientBoostingRegressor(max_iter=300, random_state=42).fit(X, np.log1p(u[j]))
    pred = np.expm1(reg.predict(jit_features(f, f['sinpkt' if side == 's' else 'dinpkt'].values, n, side))).clip(min=0)
    f[j] = np.where(f[n] > 2, pred, 0.0)                                         # UNSW: jitter = 0 với 98% flow <= 2 gói

# ---------------------------------------------------------------- 6. feature của Bro: suy từ cổng (SAppBytes/DAppBytes = 0 mọi dòng)
dport = g.Dport.astype(str)
svc = dport.map(PORT2SERVICE).fillna('-')
f['service'] = np.where((f.proto != 'tcp') | (f.ackdat > 0), svc, '-')           # UNSW: tcp ackdat=0 -> '-' ở 96,4%
http_req = (f.service == 'http')
f['trans_depth'] = http_req.astype('float64')
f['ct_flw_http_mthd'] = http_req.astype('float64')
f['response_body_len'] = 0.0

# ---------------------------------------------------------------- 7. ct_*: cửa sổ 100 bản ghi gần nhất, theo thứ tự trong từng file BS
def ct_window(keys, w=100):
    out = np.empty(len(keys), dtype='float64')
    codes = pd.factorize(keys)[0]
    order = np.argsort(codes, kind='stable')
    sc = codes[order]; bounds = np.flatnonzero(np.r_[True, sc[1:] != sc[:-1], True])
    for a, b in zip(bounds[:-1], bounds[1:]):
        p = order[a:b]
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
                     'label_published': g.label_published, 'dup_capture': g.dup_capture})
full = pd.concat([f, meta], axis=1)
full.to_parquet(OUT / '5gnidd_unsw31_full.parquet')

# ---------------------------------------------------------------- 8. làm sạch như NB01: bỏ bản sao bắt nhầm, khử trùng lặp, bỏ nhóm mâu thuẫn nhãn
d = full[~g.dup_capture.values].copy()
d['label'] = d.label_published.astype('int64')
S['sau_bo_ban_sao_bat_nham'] = len(d)
n0 = len(d)
d = d.drop_duplicates(subset=FEATS + ['attack_cat'])
S['nb01_bo_trung_lap'] = n0 - len(d)
# mâu thuẫn: cùng 31 feature nhưng khác attack_cat (bao trùm cả khác label) -> bỏ, vì model đa lớp cũng học trên tập này
nl = d.groupby(FEATS, observed=True, dropna=False)['attack_cat'].transform('nunique')
S['nb01_bo_mau_thuan_nhan'] = int((nl > 1).sum())
d = d[nl == 1].drop(columns=['label_published', 'dup_capture'])
S['n_cuoi'] = len(d)
S['ty_le_attack'] = round(float(d.label.mean()), 4)
S['theo_loai'] = d.attack_cat.value_counts().to_dict()
S['theo_tram_loai'] = {bs: d[d.bs == bs].attack_cat.value_counts().to_dict() for bs in ('BS1', 'BS2')}

# kiểm tra schema khớp UNSW đã làm sạch: cùng tên, cùng thứ tự cột feature
assert list(d.columns[:31]) == [c for c in u.columns if c not in ('label', 'attack_cat')], 'schema lệch UNSW'
d.reset_index(drop=True).to_parquet(OUT / '5gnidd_unsw31.parquet')
json.dump(S, open(RES / '01_thong_ke_lam_sach.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print(json.dumps(S, ensure_ascii=False, indent=1, default=str))
