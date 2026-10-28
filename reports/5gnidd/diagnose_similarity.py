import sys, numpy as np, pandas as pd, joblib
from pathlib import Path
B = Path(sys.argv[1]); CATS = ['proto', 'service', 'state']
model = joblib.load(B / 'reports/exp05/rf_A_trainfit.joblib')
tr = pd.read_parquet(B / 'data/cleaned/UNSW_NB15_training-set.parquet')
te = pd.read_parquet(B / 'data/cleaned/UNSW_NB15_testing-set.parquet')
U = pd.concat([tr, te], ignore_index=True)
FE = [c for c in tr.columns if c not in ('label', 'attack_cat')]
X = lambda d: d[FE].astype({c: str for c in CATS}).astype({c: 'float64' for c in FE if c not in CATS})
g = pd.read_parquet(B / 'data/5gnidd/cleaned/5gnidd_unsw31.parquet')
pd.set_option('display.width', 250)
cases = {
  'UDPFlood': (g[g.attack_cat == 'UDPFlood'], U[(U.label == 1) & (U.proto == 'udp') & (U.state == 'INT') & (U.spkts <= 2)]),
  'SYNScan': (g[g.attack_cat == 'SYNScan'], U[(U.attack_cat == 'Reconnaissance') & (U.proto == 'tcp')]),
  'TCPConnectScan': (g[g.attack_cat == 'TCPConnectScan'], U[(U.attack_cat == 'Reconnaissance') & (U.proto == 'tcp')]),
  'SYNFlood': (g[g.attack_cat == 'SYNFlood'], U[(U.label == 1) & (U.proto == 'tcp') & (U.ackdat == 0)]),
  'Benign_udp': (g[(g.label == 0) & (g.proto == 'udp')], U[(U.label == 0) & (U.proto == 'udp')]),
}
for name, (a, b) in cases.items():
    pa, pb = model.predict_proba(X(a))[:, 1], model.predict_proba(X(b))[:, 1]
    print(f'\n===== {name}: 5G n={len(a)} p(attack) median={np.median(pa):.3f} | UNSW analog n={len(b)} p median={np.median(pb):.3f}')
    cmp = pd.DataFrame({'5G_median': [a[c].astype(str).mode()[0] if c in CATS else a[c].median() for c in FE],
                        'UNSW_analog_median': [b[c].astype(str).mode()[0] if c in CATS else b[c].astype('float64').median() for c in FE]}, index=FE)
    # swap each feature of the 5G rows to the UNSW-analog median (diagnostic only)
    sm = a.sample(min(len(a), 3000), random_state=0); base = model.predict_proba(X(sm))[:, 1].mean()
    cmp['p_sau_khi_doi'] = [model.predict_proba(X(sm.assign(**{c: cmp.loc[c, 'UNSW_analog_median']})))[:, 1].mean() for c in FE]
    cmp['delta_p'] = cmp.p_sau_khi_doi - base
    print(cmp.sort_values('delta_p', ascending=False).head(10).to_string())
    print('p base', round(base, 3))

