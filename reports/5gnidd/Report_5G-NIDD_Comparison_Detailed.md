# Detailed Comparison of 5G-NIDD with UNSW-NB15 and Cross-Validation of the Current Model

**Project:** 5G IDS · model **RF 31-feature** (`reports/exp05/rf_A_trainfit.joblib`, reproducibility checked: test-final accuracy = 0.81862, same as NB07)
**Date:** 2026-10-26
**Target data:** 5G-NIDD, Fairdata release (CC BY 4.0, open access) — direct download, no IEEE account required
**Reproducible pipeline:**

| Step | Command | Output |
|---|---|---|
| 1. Mapping | `python -I -X utf8 reports/5gnidd/build_5gnidd_unsw31.py <project>` | `data/5gnidd/cleaned/*.parquet`, `build_stats.json` |
| 2. Cross-validate | `python -I -X utf8 reports/5gnidd/eval_5gnidd.py <project>` | `results_5gnidd.json`, `feature_comparison.csv`, `diagnose_feature.csv` |
| 3. Diagnosis | `python -I -X utf8 reports/5gnidd/diagnose_similarity.py <project>` | `diagnose_similarity_results.txt` |

**No file under `data/cleaned/`, `models/`, or `notebooks/` was modified.**

---

## 0. SUMMARY

| Question | Result |
|---|---|
| **Can 5G-NIDD be fed into the current model?** | **YES — already done.** The file `data/5gnidd/cleaned/5gnidd_unsw31.parquet` has **exactly 31 features, the same names, types, and units** as the cleaned UNSW data. The model's pipeline runs on this file with no modification. It contains 379,563 flows (63,283 Benign, 316,280 Attack), split into BS1/BS2. |
| **Is the mapping trustworthy?** | **Yes.** 19/31 features (83% of importance) are taken exactly, via Argus formulas verified to match 99.6–100% on both datasets, or via documented adjustments. A round-trip test (applying the exact same approximations to the UNSW test set) only drops ROC-AUC from **0.9594 to 0.9525** (−0.007). That means the mapping itself costs only about 0.7 points of ROC-AUC. |
| **Does the current model detect attacks on 5G traffic?** | **NO.** ROC-AUC = **0.399** (worse than random), balanced accuracy @0.5 = **0.446**, MCC = **−0.080**. The model assigns attack scores to **benign** 5G traffic (FPR 61%) and misses almost all **UDP flood, SYN flood, ICMP flood, and scan** attacks (recall ≈ 0). Recalibrating the threshold using labels from the other base station does not help either, because the ranking order itself is inverted. |
| **Why?** | Not because of the mapping, but because **the two datasets use the same attack name for very different behaviors** (§8). For example, UNSW's "Reconnaissance" is a complete connection (FIN, 8 reply packets, 354 reply bytes); an nmap SYN scan in 5G-NIDD is **a single bare SYN packet, 0 reply bytes**. The model has never seen this kind of flow labeled as an attack. |
| **Secondary finding — 5G-NIDD data quality** | **281,529 flows (59% of the Benign class) are mislabeled.** These are duplicates of a UDP flood from the BS2 attacking machine, recaptured at BS1 and labeled Benign (§5.1). In addition, `SIntPkt`/`DIntPkt`/jitter are **100% empty**, `SAppBytes`/`DAppBytes` are **always 0**, and `StartTime` only has `mm:ss.f` precision. |

**In one sentence:** 5G-NIDD **has been successfully cross-validated** against the current model; the cross-validation result is that the model **does not transfer** to 5G (ROC-AUC 0.40). This is a measured result using a verified mapping, not an artifact of missing data or unit mismatches.

> **Correction to the earlier plan's predictions** (`Plan_5G_NIDD_Cross_Validation.md`): I had predicted that floods and scans would be "caught well," with a zero-shot ROC-AUC of 0.70–0.90. **Both predictions were wrong.** The prediction of high FPR on Benign traffic due to radio latency was correct: FPR on Benign-TCP in the `ackdat` 10–50 ms range is **71.5%**. What I failed to anticipate was that the model **misses** floods and scans entirely, because their flow shape is completely unlike UNSW attacks.

---

## 1. DATA DOWNLOADED

Source: Fairdata/Etsin `9d13ef28-2ca7-44b0-9950-225359afac65`. Access **Open**, license **CC BY 4.0**. Citing the original paper is required (IEEE Xplore 11098458 / arXiv 2212.01298).

| File | Size | SHA-256 (first 12 chars) | Purpose |
|---|---|---|---|
| `README.pdf` | 147 KB | — | File description |
| `BTS1_BTS2_fields_preserved.zip` → `.csv` | 46.5 MB → 472 MB | `625F4D178C8A` | **Primary source**: 113 Argus fields, empty fields preserved |
| `Combined.zip` → `.csv` | 28.0 MB → 275 MB | `07531B251F3F` | Cross-check: 52 columns, 100% match on shared columns |
| `BTS_1.zip`, `BTS_2.zip` | 14.0 / 10.7 MB | `01E6C4669E64` / `6C420140E7DC` | Determine station boundary: first 728,316 rows = BS1 (100% match), remaining 487,574 rows = BS2 |

Location: `data/5gnidd/raw/` (zip), `data/5gnidd/extracted/` (extracted CSV, about 1 GB, can be deleted and re-extracted from zip).
The pcap files (≈7.8 GB) were not downloaded, since every needed feature is already available in the CSV or can be derived (§3).

---

## 2. THE TWO DATASETS — SIDE-BY-SIDE OVERVIEW

| | UNSW-NB15 (cleaned, `data/cleaned`) | 5G-NIDD |
|---|---|---|
| Flow generator | Argus + Bro (Zeek) | **Argus** (newer version), no Bro |
| Environment | Simulated LAN, IXIA PerfectStorm | Real NSA 5G network (5GTN Oulu), captured at S1-U, GTP decapsulated |
| Benign traffic | Generated by IXIA | Real phones: streaming, web, SSH, SFTP (90% UDP/QUIC) |
| Attacks | 9 families: Exploits, Fuzzers, Generic, DoS, Recon, Backdoor, Analysis, Shellcode, Worms | 8 types, **DoS and scans only**: UDP/SYN/ICMP/HTTP flood, Slowrate, SYN/TCP-Connect/UDP scan |
| Raw rows | 257,673 (official train + test) | 1,215,890 |
| After cleaning | 98,934 + 50,567 | **379,563** (§5) |
| Attack ratio | 0.50 (train) / 0.37 (test) | **0.833** |
| Number of features | 31 (after dropping 9 leaky columns + 3 useless columns in NB01) | 112 Argus fields (52 in `Combined.csv`) |

---

## 3. DETAILED MAPPING TABLE — THE MODEL'S 31 FEATURES

The **Level** column has five values:
- **CX** — exact: copy the field with the same Argus definition.
- **CT** — formula: recomputed using a formula verified to match on both datasets.
- **HC** — adjustment: unit or semantic change to match UNSW.
- **XX** — approximation: derived because the original field is empty.
- **SL** — substitution: stands in for a Bro feature.

The **Perm.imp** column is the feature's importance share in the model (`random_forest_v2_importance.csv`).

| # | UNSW feature | UNSW definition | 5G-NIDD source | Transformation | Level | Verification evidence | Perm.imp |
|---|---|---|---|---|---|---|---|
| 1 | `dur` | Flow duration (s) | `Dur` | copy | CX | same Argus field | 1.0% |
| 2 | `proto` | Protocol | `Proto` | copy (string) | CX | same Argus vocabulary; 0.03% unseen values (`llc`, `lldp`) | 1.6% |
| 3 | `service` | Service identified by Bro | `Dport` (port name) | http→http, https→ssl, domain→dns, ssh, ftp…; TCP without completed handshake (`AckDat`=0) → `-` | SL | UNSW: TCP with `ackdat`=0 → `-` in **96.4%** of rows | 5.5% |
| 4 | `state` | Argus state | `State` | copy; except **UDP `REQ` → `INT`** | HC | UNSW: one-way UDP is `INT` (8,900) and only 118 `REQ`; 5G: UDP `REQ` and `INT` both have `DstPkts`=0 in 100% of rows | 2.4% |
| 5 | `spkts` | src→dst packet count | `SrcPkts` | copy | CX | — | 1.0% |
| 6 | `dpkts` | dst→src packet count | `DstPkts` | copy | CX | — | 0.9% |
| 7 | `sbytes` | src→dst bytes | `SrcBytes` | **− 14 × SrcPkts** (strip Ethernet header) | HC | UNSW ARP = 46 bytes (min frame 60 − 14) and 28 bytes; 5G ARP/UDP-flood = 60/42 bytes (Ethernet included). hping3's empty UDP packet: 42 = 14 + 20 + 8 | 12.8% |
| 8 | `dbytes` | dst→src bytes | `DstBytes` | − 14 × DstPkts | HC | as above | 6.3% |
| 9 | `rate` | packets/s | `Rate` | copy | CT | UNSW: `rate = (spkts+dpkts−1)/dur` matches **100%** (q05–q95 = 1.0000); 5G: `Rate = (TotPkts−1)/Dur` matches **100%** | 2.2% |
| 10 | `sload` | bit/s src→dst | recomputed | `8·sbytes·(spkts−1)/spkts/dur` (0 if spkts ≤ 1) | CT | formula matches **99.6%** of UNSW rows and **100%** of 5G rows (`SrcLoad`). Recomputed after stripping Ethernet | 1.0% |
| 11 | `dload` | bit/s dst→src | recomputed | same as above with dbytes, dpkts | CT | same as above | 10.1% |
| 12 | `sloss` | "src packets lost/retransmitted" | lookup table from UNSW-train | median `sloss` of UNSW-train grouped by (proto, state, spkts); UDP = 0 | XX | UNSW `sloss` is **not** real packet loss: TCP 10 packets → 2, 14 packets → 6, UDP always 0. In 5G, `SrcLoss` > 0 in only 3.4% of TCP flows. Round-trip: Spearman 0.97, exact match 79.8% | 1.5% |
| 13 | `dloss` | as above, reverse direction | lookup table | same as above with dpkts | XX | Spearman 0.96, exact match 64.8% | 2.8% |
| 14 | `sinpkt` | src inter-packet gap (ms) | **`SIntPkt` 100% empty** → computed from `Dur` | `Dur·1000/(SrcPkts−1)` | XX | On UNSW: 89.4% deviation ≤ 20%, Spearman 0.95 | 0.9% |
| 15 | `dinpkt` | as above, reverse direction | `DIntPkt` empty → computed from `Dur` | `Dur·1000/(DstPkts−1)` | XX | 80.6% deviation ≤ 20%, Spearman 0.84 | 1.8% |
| 16 | `sjit` | src jitter (ms) | **jitter 100% empty** → regression model | HGB trained on UNSW-train (from approximated sinpkt, spkts, dur, sbytes, proto); = 0 if spkts ≤ 2 | XX | Spearman against true values on UNSW-test **0.98**. UNSW: jitter = 0 in 98% of flows with ≤ 2 packets | 0.8% |
| 17 | `djit` | dst jitter | as above | as above | XX | Spearman 0.98 | 0.6% |
| 18 | `swin` | src TCP window | `Proto` | **tcp → 255, else 0** | HC | UNSW only has 0/255: 99.98% of TCP = 255, 100% of non-TCP = 0. 5G `SrcWin` is a real value (64,256…), a different scale | 1.1% |
| 19 | `stcpb` | initial TCP sequence number | `SrcTCPBase` | copy, empty → 0 | CX | UNSW: non-TCP = 0 in 100% of rows | 0.2% |
| 20 | `dtcpb` | as above, reverse direction | `DstTCPBase` | same as above | CX | — | 0.8% |
| 21 | `dwin` | dst TCP window | `Proto`, `DstPkts` | tcp with reply packets → 255, else 0 | HC | UNSW: TCP with `dpkts`=0 → `dwin`=0 in 100% (813/813) | 0.0% |
| 22 | `tcprtt` | handshake RTT (s) | `TcpRtt` | copy | CX | `tcprtt = synack + ackdat` holds exactly in 100% of both datasets | 3.6% |
| 23 | `synack` | SYN → SYN/ACK (s) | `SynAck` | copy | CX | — | 4.2% |
| 24 | `ackdat` | SYN/ACK → ACK (s) | `AckDat` | copy | CX | — | **25.0%** |
| 25 | `smean` | mean src packet size | recomputed | `round(sbytes/spkts)` | CT | UNSW: matches **100%**. Computed after stripping Ethernet | 5.7% |
| 26 | `dmean` | mean dst packet size | recomputed | `round(dbytes/dpkts)`, 0 if no packets | CT | UNSW: matches **100%**; `dpkts`=0 → 0 in 100% of cases | 3.1% |
| 27 | `trans_depth` | HTTP pipeline depth (Bro) | `service` | `service == http` → 1, else 0 | SL | UNSW: http + completed handshake → 1 in **91%** of cases; round-trip matches 98.0% | 0.2% |
| 28 | `response_body_len` | HTTP body length (Bro) | not available | 0 | SL | `DAppBytes` = 0 in every row, so body length cannot be recovered | 0.4% |
| 29 | `ct_src_dport_ltm` | number of connections with the same src and dport among the 100 most recent connections | `SrcAddr`, `Dport` | 100-record sliding window, in the row order within each BS file | XX | `StartTime` only has `mm:ss.f` precision, so row order is used instead. Not round-trip verifiable because the cleaned UNSW data no longer has IPs/ports | 1.7% |
| 30 | `ct_flw_http_mthd` | number of flows with an HTTP command (Bro) | `service` | same as `trans_depth` | SL | UNSW http: = 1 in 88% of cases | 0.1% |
| 31 | `ct_src_ltm` | number of connections with the same src among the 100 most recent connections | `SrcAddr` | same as #29 | XX | same as #29 | 0.4% |

**Summary by level (by permutation importance):**

| Level | # features | Importance share |
|---|---|---|
| CX + CT (exact / verified formula) | 14 | **60.4%** |
| HC (adjustment with evidence) | 5 | 22.6% (`sbytes`, `dbytes` account for 19.1%) |
| XX (approximation / lookup / window) | 8 | 10.5% |
| SL (substitution for Bro) | 4 | 6.2% |

→ **83.0%** of importance sits on features that are exact, formula-based, or adjusted with evidence. The remaining 16.7% is approximation and substitution, verified via the round-trip test below.

**Round-trip — how much do the approximations cost?** Applying approximations #12–17, #18, #21, #27–28, #30 exactly to UNSW `test-final`, then re-scoring with the model:

| | ROC-AUC | PR-AUC | Bal acc @0.5 | MCC @0.5 | Recall @0.5 | FPR @0.5 |
|---|---|---|---|---|---|---|
| UNSW test-final, original | 0.9594 | 0.9414 | 0.8461 | 0.6672 | 0.9491 | 0.2569 |
| UNSW test-final, after approximation | **0.9525** | 0.9318 | 0.8318 | 0.6410 | 0.9539 | 0.2903 |
| Δ | **−0.0069** | −0.0096 | −0.0143 | −0.0262 | +0.0048 | +0.0334 |

The approximations only cost about **0.7 points of ROC-AUC**. The drop observed on 5G is **0.56 points** (0.96 → 0.40) — roughly **80 times larger**. The mapping does not explain the 5G result.

---

## 4. PER-FEATURE DISTRIBUTIONS — THE TWO DATASETS SIDE BY SIDE

Data: `feature_comparison.csv`. q50/q90 = median / 90th percentile. KS = Kolmogorov–Smirnov distance (0 = identical, 1 = fully separated).
**Diagnostic ΔROC** (§8.2): how much the ROC-AUC on 5G changes when that single feature is replaced by the UNSW median. A positive value means the feature is currently **pulling the model in the wrong direction**.

| Feature | UNSW Normal | UNSW Attack | 5G Benign | 5G Attack | KS Normal↔Benign | KS Attack↔Attack | % of 5G outside UNSW range | Diagnostic ΔROC |
|---|---|---|---|---|---|---|---|---|
| `dur` | 0.109 / 1.34 | 0.671 / 2.50 | 0.161 / 5.00 | 2.28 / 4.58 | 0.356 | 0.410 | 0 | −0.001 |
| `spkts` | 12 / 66 | 10 / 32 | 3 / 150 | 2 / 7 | 0.370 | **0.749** | 9.6% | −0.023 |
| `dpkts` | 10 / 66 | 8 / 24 | 3 / 24 | 1 / 9 | 0.353 | 0.604 | 0 | −0.004 |
| `sbytes` | 1,514 / 7,820 | 862 / 10,880 | 489 / 196,900 | **60 / 700** | 0.351 | 0.639 | 9.6% | +0.013 |
| `dbytes` | 1,092 / 45,700 | 354 / 5,262 | 161 / 6,085 | **52** / 11,700 | 0.413 | 0.512 | 0 | −0.089 |
| `rate` | 475 / 5,625 | 35.8 / 125,000 | 28.0 / 134 | **0.44** / 6.1 | 0.482 | **0.869** | 0.04% | −0.008 |
| `sload` | 274k / 1.9M | 14.6k / 133M | 14.4k / 360k | **87** / 1,601 | 0.390 | **0.884** | 0 | −0.002 |
| `dload` | 204k / 7.9M | 3,973 / 54.7k | 5,610 / 163k | 0 / 17.9k | 0.448 | 0.542 | 0.2% | −0.041 |
| `sloss` | 3 / 11 | 2 / 8 | 0 / 3 | 1 / 3 | 0.561 | 0.290 | 0 | +0.006 |
| `dloss` | 2 / 26 | 1 / 8 | 0 / 1 | 1 / 4 | 0.654 | 0.227 | 0 | −0.009 |
| `sinpkt` | 4.2 / 111 | 52.5 / 153 | 26.7 / 1,499 | 574 / 2,582 | 0.287 | 0.517 | 0 | −0.005 |
| `dinpkt` | 1.3 / 116 | 62.1 / 166 | 23.4 / 394 | 0 / 1,111 | 0.354 | 0.400 | 0 | −0.015 |
| `sjit` | 132 / 8,652 | 2,890 / 8,800 | 35.0 / 1,658 | 0 / 36,290 | 0.311 | 0.470 | 0 | +0.005 |
| `djit` | 30.6 / 709 | 123 / 1,738 | 20.4 / 810 | 0 / 28,170 | 0.261 | 0.446 | 0 | +0.013 |
| `swin` | 255 / 255 | 255 / 255 | 0 / 255 | 255 / 255 | 0.547 | 0.004 | 0 | +0.007 |
| `stcpb` | 1.5e9 / 3.7e9 | 1.5e9 / 3.7e9 | 0 / 2.4e9 | 1.5e9 / 3.7e9 | 0.537 | 0.017 | 0 | +0.009 |
| `dtcpb` | 1.5e9 / 3.7e9 | 1.5e9 / 3.7e9 | 0 / 7.6e8 | 1.2e9 / 3.7e9 | 0.644 | 0.068 | 0 | +0.007 |
| `dwin` | 255 / 255 | 255 / 255 | 0 / 255 | 255 / 255 | 0.645 | 0.120 | 0 | +0.002 |
| `tcprtt` | 0.0007 / 0.179 | 0.099 / 0.201 | 0 / 0 | 0.015 / 0.035 | **0.681** | **0.699** | 0 | +0.001 |
| `synack` | 0.0005 / 0.095 | 0.049 / 0.106 | 0 / 0 | 0.0016 / 0.0022 | **0.681** | **0.764** | 0 | +0.008 |
| `ackdat` | 0.0001 / 0.082 | 0.049 / 0.100 | 0 / 0 | 0.014 / 0.032 | **0.681** | 0.595 | 0 | −0.019 |
| `smean` | 73 / 252 | 88 / 680 | 162 / 1,326 | **52 / 105** | 0.327 | 0.541 | 9.6% | **+0.115** |
| `dmean` | 89 / 785 | 45 / 406 | 84 / 554 | 52 / 1,012 | 0.201 | 0.201 | 0 | +0.027 |
| `trans_depth` | 0 / 1 | 0 / 1 | 0 / 0 | 1 / 1 | 0.104 | 0.444 | 0 | −0.013 |
| `response_body_len` | 0 / 0 | 0 / 140 | 0 / 0 | 0 / 0 | 0.098 | 0.120 | 0 | 0 |
| `ct_src_dport_ltm` | 1 / 3 | 1 / 3 | 6 / 57 | **99 / 100** | 0.642 | **0.914** | **76.1%** | −0.035 |
| `ct_flw_http_mthd` | 0 / 1 | 0 / 1 | 0 / 0 | 1 / 1 | 0.104 | 0.444 | 0 | −0.001 |
| `ct_src_ltm` | 3 / 8 | 2 / 7 | 12 / 56 | **99 / 100** | 0.487 | **0.973** | **81.3%** | +0.001 |

| Categorical feature | UNSW (share) | 5G (share) | % of 5G unseen in UNSW-train |
|---|---|---|---|
| `proto` | tcp 0.775 · udp 0.161 · unas 0.013 · ospf 0.006 | tcp 0.683 · udp 0.290 · icmp 0.017 · **sctp 0.009** | 0.03% |
| `service` | - 0.624 · http 0.174 · dns 0.078 · smtp 0.045 | **http 0.564** · - 0.380 · ssl 0.052 · dns 0.004 | 0% |
| `state` | FIN 0.747 · CON 0.124 · INT 0.119 · REQ 0.008 | CON 0.345 · INT 0.206 · **RST 0.199** · FIN 0.152 | 0.36% (URP, RSP, TST, NRS) |

**How to read this:**
- **No unit errors remain.** Almost every 5G value falls within the UNSW value range. The exceptions are `ct_*` (76–81% of 5G rows exceed UNSW's max of 60) and `spkts`/`sbytes`/`smean` (9.6%, mostly large benign streaming flows).
- **The biggest shift is in the Attack class** (KS Attack↔Attack 0.6–0.97 for `rate`, `sload`, `spkts`, `ct_*`), not the Normal class. This is the opposite of NB07's UNSW train→test case, where the shift was concentrated in Normal. In other words, **5G attacks do not resemble UNSW attacks.**
- **5G Benign has `tcprtt`/`synack`/`ackdat` = 0 in over 90% of rows**, because 90% of Benign traffic is UDP. For the remaining TCP traffic, the prediction holds: FPR @0.5 in the `ackdat` 10–50 ms band is **71.5%**, and **86.3%** when > 50 ms, versus 6.5% when `ackdat` = 0.

---

## 5. 5G-NIDD DATA QUALITY — ISSUES FOUND DURING TESTING

### 5.1 Label error: 281,529 attack flows labeled Benign

| Check | Result |
|---|---|
| Flows from attacking machine `10.155.15.7` → victim server `10.41.150.68` | 281,529 `UDPFlood` labels (in the **BS2** file) + **281,529 `Benign` labels** (in the **BS1** file) |
| Row-by-row comparison in order | `Sport`, `Dur`, `SrcPkts`, `sIpId` (hping3's random IP-ID), `StartTime`… **match exactly**. Only `Seq`/`Offset` (row position) and the label differ |
| Packet size | 42 bytes in 100% of rows, exactly the hping3 `--udp` no-payload fingerprint |
| Interpretation | The BS2 attacker's flood passes through BS1's capture point as well. BS1's labeling script only flags BS1's own attacker, so this duplicate gets labeled Benign |
| Impact | **59%** of the published Benign class (281,529/477,737) is actually attack traffic, and there is also **leakage between the two stations**: the same flow appears in both BS1 and BS2 |
| Fix | **Remove** the 281,529 duplicates from BS1 (the `dup_capture` column in `_full.parquet` keeps a marker for later inspection) |

Detection rule using only non-label information: *Benign at station X, where the source is the other station's attacking IP and the destination is the victim server*. This rule correctly flags exactly 281,529 rows in BS1 and **0** rows in BS2.

### 5.2 Other issues

| Issue | Impact | Handling |
|---|---|---|
| `SIntPkt`, `DIntPkt`, `SrcJitAct`, `DstJitter`… **100% empty** (Argus jitter stats not enabled) | Missing 4 features `sinpkt`/`dinpkt`/`sjit`/`djit` | Approximated (§3 #14–17) |
| `SAppBytes`, `DAppBytes` **= 0 in every row** (Argus `-A` not enabled) | Cannot tell whether a flow has application payload | `service` inferred from port + handshake state |
| `StartTime`, `LastTime` only have `mm:ss.f` (no hour or date) | Cannot sort by absolute time | `ct_*` uses row order within each BS file |
| `Dport` empty in 100% of UDPFlood and 83.8% of Benign | `ct_src_dport_ltm` groups under an "empty" key | Kept as-is, noted |
| `Seq`, `Offset` top the ANOVA table in the original paper | They are just record position within the file, i.e., pure metadata | Not used (the model has no such columns) |
| `sTtl` ranked 3rd in ANOVA in the original paper | A leaky feature (D'hooge 2022), already removed from UNSW by NB01 | Not used |

### 5.3 Cleaning — following NB01's rules

| Step | Row count |
|---|---|
| Raw | 1,215,890 |
| − mis-captured duplicates (§5.1) | 934,361 |
| − exact duplicates across the 31 features + label | **−554,798** (hping3/nmap generate large numbers of identical flows) |
| − label-conflicting groups | −0 |
| **Remaining** | **379,563** |

| Class | BS1 | BS2 | Total |
|---|---|---|---|
| Benign | 40,267 | 23,016 | 63,283 |
| HTTPFlood | 76,120 | 64,691 | 140,811 |
| SlowrateDoS | 36,091 | 37,032 | 73,123 |
| UDPFlood | 39,265 | 30,656 | 69,921 |
| TCPConnectScan | 10,014 | 10,028 | 20,042 |
| SYNFlood | 4,792 | 4,929 | 9,721 |
| SYNScan | 529 | 519 | 1,048 |
| ICMPFlood | 568 | 462 | 1,030 |
| UDPScan | 375 | 209 | 584 |

---

## 6. GENERATED DATA FILES

| File | Contents | When to use |
|---|---|---|
| `data/5gnidd/cleaned/5gnidd_unsw31.parquet` | **Main validation set**: 31 features + `label`, `attack_cat`, `bs`, `attack_tool`, `src_addr`. Labels fixed, deduplicated | Any cross-validation |
| `data/5gnidd/cleaned/5gnidd_unsw31_full.parquet` | 1,215,890 rows, 31 features + `label_published`, `dup_capture` | Reproduce conditions as in the original paper |
| `data/5gnidd/cleaned/5gnidd_unsw31_raw.parquet` | Same rows as the main set, but with the **raw mapping**: Ethernet not stripped, `SrcLoss`/`SrcWin` left as-is, missing values set to 0 | Measure sensitivity to the adjustment steps |
| `data/5gnidd/cleaned/unsw_test_roundtrip.parquet` | UNSW-test after applying the exact same approximations | Round-trip verification |

Usage with the current model (same `X_of` function as NB07):

```python
g = pd.read_parquet('data/5gnidd/cleaned/5gnidd_unsw31.parquet')
p = rf.predict_proba(g[FEATS].astype({c: str for c in ['proto', 'service', 'state']}))[:, 1]
```

---

## 7. CROSS-VALIDATION RESULTS

### 7.1 Zero-shot — UNSW model unchanged, no 5G labels used

| Configuration | n | π | ROC-AUC | PR-AUC | Accuracy | Bal acc | MCC | Precision | Recall | FPR |
|---|---|---|---|---|---|---|---|---|---|---|
| @0.5 | 379,563 | 0.833 | **0.399** | 0.747 | 0.484 | **0.446** | **−0.080** | 0.805 | 0.503 | **0.611** |
| @0.6949 (UNSW test-dev threshold) | 379,563 | 0.833 | 0.399 | 0.747 | 0.199 | 0.357 | −0.286 | 0.596 | 0.120 | 0.407 |
| EM prior-corrected, @0.5 | 379,563 | 0.833 | 0.399 | 0.747 | 0.820 | 0.503 | 0.013 | 0.834 | 0.978 | **0.973** |
| BS1 @0.5 | 208,021 | 0.806 | 0.425 | 0.725 | 0.477 | 0.454 | −0.074 | 0.778 | 0.491 | 0.584 |
| BS2 @0.5 | 171,542 | 0.866 | 0.354 | 0.776 | 0.493 | 0.430 | −0.096 | 0.835 | 0.517 | 0.658 |

- **PR-AUC 0.747 < π = 0.833**: exactly the signature of a ranker that is **worse than random**.
- The EM row's 0.820 accuracy is illusory: the model labels almost every flow as Attack (FPR 97%), while 83% of the data actually is Attack. This is precisely the "accuracy alone" trap that NB07 warned about.
- EM estimates π = 0.831, very close to the true π of 0.833. But correcting the prior does not change the ranking order, so it does not help.

### 7.2 Labeled threshold calibration (few-shot) — tune on one station, report on the other

| Threshold tuned on | Threshold found (FPR ≤ 0.10) | Reported on | Recall | FPR |
|---|---|---|---|---|
| BS1 | **1.000** | BS2 | 0.000 | 0.000 |
| BS2 | **1.000** | BS1 | 0.000 | 0.000 |

Because ROC < 0.5, no threshold achieves FPR ≤ 0.10 while still catching attacks. The rule is forced to pick a threshold of 1.0. **The "a few 5G labels to retune the threshold" scenario (E2 in the plan) fails.**

### 7.3 Recall by attack type

| Type | n | Recall @0.5 | Recall @0.6949 | What does it resemble in UNSW? |
|---|---|---|---|---|
| **Benign (= FPR)** | 63,283 | **0.611** | 0.407 | — |
| HTTPFlood | 140,811 | 0.694 | 0.245 | Complete TCP connection, `ackdat` 13 ms |
| SlowrateDoS | 73,123 | **0.834** | 0.044 | Long TCP connection, large `ackdat` |
| UDPScan | 584 | 0.401 | 0.331 | — |
| **UDPFlood** | 69,921 | **0.003** | 0.000 | — |
| **TCPConnectScan** | 20,042 | **0.001** | 0.000 | — |
| **SYNFlood** | 9,721 | **0.000** | 0.000 | — |
| **SYNScan** | 1,048 | **0.000** | 0.000 | — |
| **ICMPFlood** | 1,030 | **0.000** | 0.000 | — |

FPR on Benign by protocol @0.5: UDP **0.782** (39,453 flows) · SCTP **0.902** (3,514; 5G S1-AP signaling, which in UNSW is 100% attack) · TCP 0.308 (14,678) · ICMP 0.007 (5,496).

### 7.4 Sensitivity to the mapping and labeling approach

| Variant | ROC-AUC | Bal acc @0.5 | Recall | FPR |
|---|---|---|---|---|
| **Main** (full adjustment, labels fixed, deduplicated) | 0.399 | 0.446 | 0.503 | 0.611 |
| Raw mapping (Ethernet not stripped, no `swin`/`sloss`/state normalization, missing → 0) | 0.352 | 0.431 | 0.499 | 0.638 |
| Published labels, **not** deduplicated, mislabeled duplicates kept (1,215,890 rows) | 0.400 | 0.448 | 0.501 | 0.606 |

The adjustment steps raise ROC-AUC by **+0.047**, in the right direction. But no variant exceeds 0.5. **The "does not transfer" conclusion holds under every data-handling approach tried.**

---

## 8. WHY THE MODEL FAILS — THE MECHANISM

### 8.1 Comparing each 5G attack type with its closest UNSW "relative"

The table below uses the median feature values of each 5G group and the corresponding UNSW group. The last column shows how much the average attack probability increases when **only** that feature is replaced with the UNSW value (`diagnose_similarity_results.txt`).

| 5G type | Avg p(Attack) in 5G | Closest UNSW group | p(Attack) in UNSW | Decisive differing feature (5G → UNSW, Δp) |
|---|---|---|---|---|
| UDPFlood | 0.46 | UDP attack, INT, ≤ 2 packets | **0.97** | `smean` 28 → 112 (**+0.15**), `sinpkt` 2,576 → 0.008 ms (+0.10), `dur` 2.6 s → 8 µs (+0.03) |
| SYNScan | 0.04 | TCP Reconnaissance | **1.00** | `smean` 44 → 56 (**+0.37**), `dbytes` 0 → 354 (+0.18), `ackdat` 0 → 0.056 (+0.15) |
| TCPConnectScan | 0.44 | TCP Reconnaissance | 1.00 | `dbytes` 0 → 354 (+0.10), `state` REQ → FIN (+0.07), `ackdat` 0 → 0.056 (+0.05) |
| SYNFlood | 0.16 | TCP attack, no handshake | 0.53 | `smean` 40 → 63 (+0.25), `dbytes` 44 → 586 (+0.18) |
| Benign UDP | **0.70** | Normal UDP (DNS) | **0.00** | Inter-packet gap 30 ms vs 0.01 ms, `dload` 7 kB/s vs 635 kB/s |

**Three mechanisms, in order of importance:**

1. **UNSW attacks carry a payload; 5G floods and scans do not.** IXIA generates UNSW attacks at the application level: UNSW's Reconnaissance is a *complete* TCP connection (state FIN, 8 reply packets, 354 reply bytes, 56 ms handshake). nmap `-sS` and hping3 in 5G send **bare packets** (40–58 bytes, no payload, no handshake). The model has learned "small packet, no reply bytes → Normal," because UNSW's Normal UDP/ARP traffic looks exactly like that. `smean` has the largest diagnostic impact (+0.115 ROC-AUC when neutralized).
2. **Radio latency: the `ackdat` shortcut the earlier plan predicted.** Benign TCP with `ackdat` 10–50 ms triggers a 71.5% false-alarm rate. The reason: in UNSW, `ackdat` ≥ 10 ms is almost synonymous with an attack (99.6% of TCP attack flows, versus 24.7% of Normal flows).
3. **Benign 5G phone traffic (QUIC/streaming over UDP, SCTP S1-AP signaling) has no counterpart in UNSW.** Long Benign UDP flows with ~30 ms inter-packet gaps score 0.70. SCTP is scored as an attack because in UNSW, 100% of SCTP traffic is attack traffic.

### 8.2 No single feature can "fix" this

Neutralizing each feature individually (replacing it with the UNSW-train median, without using labels) on a sample of 8,000 rows per class:
- The most improving feature is `smean`: ROC-AUC only moves from 0.296 to **0.411**, still below 0.5.
- Neutralizing `ct_*` (setting it to 1) **makes things worse** (0.267). So `ct_*` exceeding its range is not the cause.

The failure is **spread across many features**, exactly what happens when the concept of "attack" itself differs between the two domains. There is no single mapping bug to fix.

---

## 9. CONCLUSION

| Goal | Status |
|---|---|
| Download 5G-NIDD | ✅ Fairdata, CC BY 4.0, 4 CSV files, hashes verified |
| Compare every feature between the two datasets | ✅ §3 (definitions, sources, transformations, evidence), §4 (distributions, KS, diagnostics), §10 (all 52 5G-NIDD columns) |
| **5G-NIDD can be cross-validated against the current model** | ✅ **Achieved.** `5gnidd_unsw31.parquet` matches the 31-feature schema; 83% of importance is mapped exactly, via a verified formula, or via an evidence-backed adjustment; the round-trip only costs 0.007 ROC-AUC |
| The current model detects attacks well on 5G | ❌ ROC-AUC 0.40, bal acc 0.45. Recalibrating the threshold with 5G labels does not help either |

**It should not** be reported that the model "has been validated on 5G." The accurate statement is: *"The UNSW-NB15 model was cross-validated on 5G-NIDD using a verified feature mapping; it does not generalize to the 5G network (ROC-AUC 0.40), because the attacks and benign traffic in the two datasets are fundamentally different in nature."* This is still a valuable result, consistent with NB07's findings on distribution shift, but far more severe.

### Recommendations

1. **Building an IDS for 5G requires training on 5G data.** The `5gnidd_unsw31.parquet` set already has a `bs` column, so experiment E3 from the plan can be run immediately: train on BS1 → test on BS2 and vice versa. Split by station, not randomly.
2. **In every experiment on 5G-NIDD**, the 281,529 duplicates (§5.1) must be removed and deduplication applied. Otherwise the Benign class is 59% contaminated with attacks, and there is leakage between the two stations.
3. If a single model spanning both domains is still desired, try E5: train on UNSW + 5G-BS1 combined, test on BS2. Drop features that are purely "environment fingerprints": `ackdat`/`synack`/`tcprtt` (latency), `stcpb`/`dtcpb` (random numbers).
4. If exact `sinpkt`/jitter values are needed instead of approximations, Argus can be rerun (with jitter enabled) on the GTP-decapsulated pcap (≈3.8 GB) using WSL. However, the round-trip shows this would only be worth about 0.01 ROC-AUC, which would not change the conclusion.
5. Update slides and reports: when mentioning 5G, use the figures in §7.1, with a note on methodology from §3.

---

## 10. APPENDIX — ALL 52 COLUMNS OF `Combined.csv` AND THEIR ROLE

| 5G-NIDD column | Role in the mapping | Notes |
|---|---|---|
| `Unnamed: 0`, `Seq`, `Offset` | Dropped: metadata | Row position within the file; `Seq`/`Offset` topped the ANOVA in the original paper, so they are a leakage risk |
| `Dur` | → `dur`; input to `sinpkt`, `dinpkt`, `sload`, `dload` | |
| `RunTime`, `Mean`, `Sum`, `Min`, `Max` | Not used | Argus record-duration statistics; UNSW has none of these |
| `Proto` | → `proto`, `swin`, `dwin`, `service` | |
| `sTos`, `dTos`, `sDSb`, `dDSb` | Not used | UNSW has none of these |
| `sTtl`, `dTtl`, `sHops`, `dHops` | **Dropped: leaky** | `sttl`/`dttl` were already removed by NB01 (D'hooge 2022); hops are derived from TTL |
| `Cause` | Not used | Reason Argus emitted the record (Start/Status) |
| `TotPkts`, `TotBytes` | Not used | = src + dst |
| `SrcPkts`, `DstPkts` | → `spkts`, `dpkts` | |
| `SrcBytes`, `DstBytes` | → `sbytes`, `dbytes` (−14 bytes/packet) | |
| `sMeanPktSz`, `dMeanPktSz` | Replaced by recomputed → `smean`, `dmean` | Original value still includes Ethernet |
| `Load`, `SrcLoad`, `DstLoad` | Replaced by recomputed → `sload`, `dload` | Formula verified to match 100% |
| `Loss`, `pLoss` | Not used | |
| `SrcLoss`, `DstLoss` | Only used in the "raw" variant | Different semantics from UNSW's `sloss` (§3 #12) |
| `SrcGap`, `DstGap` | Not used | UNSW has none of these |
| `Rate` | → `rate` | Formula matches 100% |
| `SrcRate`, `DstRate` | Not used | |
| `State` | → `state` (UDP REQ → INT) | |
| `SrcWin`, `DstWin` | Only used in the "raw" variant | Real values, a different scale from UNSW's 0/255 |
| `sVid`, `dVid` | Not used | VLAN |
| `SrcTCPBase`, `DstTCPBase` | → `stcpb`, `dtcpb` | |
| `TcpRtt`, `SynAck`, `AckDat` | → `tcprtt`, `synack`, `ackdat` | |
| `Label` | → `label` (Malicious = 1) | |
| `Attack Type` | → `attack_cat` | |
| `Attack Tool` | → `attack_tool` (metadata) | |

Additional columns taken from `BTS1_BTS2_fields_preserved.csv` (not present in `Combined.csv`):

| Column | Used for |
|---|---|
| `SrcAddr`, `DstAddr` | `ct_src_ltm`; detecting mis-captured duplicates (§5.1). Not fed into the model |
| `Dport` | `service`, `ct_src_dport_ltm` |
| `SAppBytes`, `DAppBytes` | Checked: = 0 in every row, **unusable** |
| `SIntPkt`, `DIntPkt`, jitter | Checked: 100% empty, **unusable** |

---

## 11. LIMITATIONS

- `ct_src_ltm`/`ct_src_dport_ltm` use row order instead of time, because `StartTime` is truncated to `mm:ss`. These are the only two features that cannot be verified by round-trip (the cleaned UNSW data no longer has IPs/ports). The diagnosis in §8.2 shows that neutralizing them does not improve the result.
- `service` is based on the port, while Bro identifies it from the payload. For HTTPFlood/Slowrate (port 80, completed handshake) the two approaches agree. For encrypted traffic on an unusual port, they may differ.
- The `sloss`/`dloss` lookup tables and the jitter regression model are trained on UNSW-**train** without using labels. They carry "UNSW semantics" over to 5G; verified by round-trip in §3.
- The model evaluated is the 31-feature RF. The 39-feature RF configuration (NB05/NB07) requires `sttl`/`dttl`, which are both leaky and cannot be refit, so it was not evaluated.
- 5G-NIDD only contains DoS and scan attacks. This result says nothing about Exploits, Fuzzers, Backdoor, etc. on 5G networks.
