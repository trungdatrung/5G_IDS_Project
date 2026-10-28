# Plan for Cross-Validation on 5G-NIDD — Feasibility and Detection Capability

> **Update 2026-10-26:** real data has been downloaded and cross-validation has been run. See `Report_5G-NIDD_Comparison_Detailed.md`.
> Some points in this plan have been **corrected** by the real data:
> - `SIntPkt`/jitter are 100% empty, so they do not belong in the "available in CSV" group.
> - UNSW's `swin` only takes values 0/255.
> - The prediction that "floods and scans would be caught well," as well as the zero-shot ROC-AUC of 0.70–0.90, were **wrong**. The real result is ROC-AUC 0.40, with floods/scans missed.

**Project:** 5G IDS · RF 31-feature model trained on UNSW-NB15 (pipeline `reports/exp05/rf_A_trainfit.joblib`)
**Date:** 2026-10-26
**Target dataset:** 5G-NIDD (Samarakoon et al., University of Oulu, 5GTN) — IEEE DataPort `10203`
**Baseline figures:** `reports/5gnidd/stress_test_5g.py` → `stress_test_5g_results.json`
(reproducible: `python stress_test_5g.py <project directory>`; model verified to match NB07, test-final accuracy = 0.81862)

---

## 0. SUMMARY

| Question | Answer |
|---|---|
| **Is it feasible from a data standpoint?** | **Yes.** 5G-NIDD uses **Argus**, the same tool that generated UNSW-NB15. 21/31 of the model's features map directly, accounting for **87.5%** of total permutation importance. The 3 missing Bro features account for only **0.7%**. |
| **Can the current model be used as-is (zero-shot)?** | **It can run, but is expected to be unusable operationally.** The model's most important feature is `ackdat`, which in UNSW acts as a **network-latency shortcut**: 99.6% of attacking TCP flows have `ackdat ≥ 10 ms`, versus only 24.7% of Normal flows. On a 5G network, almost **every** benign TCP flow has radio latency ≥ 10 ms. |
| **Quantitative prediction** | Stress test simulating 5G conditions on UNSW: FPR @0.5 rises from **25.7% to 37.6–40.7%**. FPR on Normal flows with a completed TCP handshake rises from **28.2% to 43.3–47.2%**. ROC-AUC drops from **0.959 to 0.911–0.922**. Recall stays roughly constant at **~0.95**. The model **still catches attacks but with a lot of false alarms**. |
| **What numbers are worth reporting?** | **Three separate numbers** should be reported: (1) zero-shot, (2) with threshold calibration using a small number of 5G labels, (3) trained within the 5G domain, split by the original base station. **Do not** use a random 70/30 split as in the original paper (99.9%), since that approach has both leakage and leaky features (§4). |

---

## 1. 5G-NIDD — what has been verified from the original paper (arXiv 2212.01298)

| Item | Value |
|---|---|
| Infrastructure | 5GTN Oulu, NSA option 3a, 2 pico base stations (BS1, BS2), victim is an Ubuntu server in the MEC |
| Capture point | Base station S1-U interface → includes a GTP-U layer, decapsulated with Tracewrangler |
| Flow generation | **Argus**, 112 features → CSV. Files include `BTS_1.csv`, `BTS_2.csv`, `Combined.csv`, `Encoded.csv` |
| Benign traffic | Real phone (Moto g50 5G): HTTP/HTTPS (streaming, web), SSH, SFTP |
| Total | **1,215,890 flows**: 477,737 Benign (39.3%) and 738,153 Attack (60.7%) |

| Attack type | Tool | # flows | % of attacks | Closest UNSW equivalent |
|---|---|---|---|---|
| UDP Flood | hping3 `--rand-source` | 457,340 | 62.0% | DoS (not a close match) |
| HTTP Flood | GoldenEye | 140,812 | 19.1% | DoS / Exploits (not a close match) |
| Slowrate DoS | Slowloris, Torshammer | 73,124 | 9.9% | **none** |
| TCP Connect Scan | nmap `-sT` | 20,052 | 2.7% | Reconnaissance |
| SYN Scan | nmap `-sS` | 20,043 | 2.7% | Reconnaissance |
| UDP Scan | nmap `-sU` | 15,906 | 2.2% | Reconnaissance |
| SYN Flood | hping3 `--rand-source` | 9,721 | 1.3% | DoS |
| ICMP Flood | hping3 `--rand-source` | 1,155 | 0.2% | DoS |

Structural differences between the two datasets:
- **5G-NIDD only contains DoS and scan attacks.** There is no Exploits, Fuzzers, Backdoor, Shellcode, Worms, Generic, or Analysis category. This test measures **network-domain generalization** for two attack families only, not the model's full capability.
- **Access:** the file on IEEE DataPort requires login and a subscription. The Fairdata copy (`etsin.fairdata.fi/dataset/9d13ef28-2ca7-44b0-9950-225359afac65`) requires the team to verify access rights itself. Only `Combined.zip` (26.7 MB) needs to be downloaded. Recomputing the Bro features would additionally require the GTP-decapsulated pcap (BS1 2.17 GB + BS2 1.43 GB).

---

## 2. FEASIBILITY — mapping the 31 features

Weights follow the permutation importance of the 31-feature model (`models/random_forest_v2_importance.csv`).

| Group | UNSW feature → 5G-NIDD Argus field | # features | % importance |
|---|---|---|---|
| **A. Direct** | dur→Dur, proto→Proto, state→State, spkts/dpkts→SrcPkts/DstPkts, sbytes/dbytes→SrcBytes/DstBytes, rate→Rate, sload/dload→SrcLoad/DstLoad, sloss/dloss→SrcLoss/DstLoss, swin/dwin→SrcWin/DstWin, stcpb/dtcpb→SrcTCPBase/DstTCPBase, tcprtt/synack/ackdat→TcpRtt/SynAck/AckDat, smean/dmean→sMeanPktSz/dMeanPktSz | 21 | **87.5%** |
| **B. In Argus, must verify presence in CSV** | sinpkt/dinpkt→SIntPkt/DIntPkt, sjit/djit→SrcJitter/DstJitter | 4 | 4.1% |
| **C. Can be recomputed** | service ← inferred from Dport (80→http, 22→ssh, 53→dns, else `-`); ct_src_ltm, ct_src_dport_ltm ← 100-connection window over StartTime, SrcAddr, Dport | 3 | 7.6% |
| **D. Missing (Bro/Zeek)** | trans_depth, response_body_len, ct_flw_http_mthd → set to 0, or run Zeek on the pcap | 3 | 0.7% |

**Conclusion:** technically, ≥99% of the model's weight can be run. The risk is **not** missing features but feature **semantics**:

1. **Units.** Argus allows configuring units (ms vs. s, bit/s vs. byte/s). The value ranges of `Dur`, `SIntPkt`, `Load` must be cross-checked against UNSW before feeding the model. UNSW's two raw CSVs are unavailable (as noted in NB07 §13.7), so this can only be cross-checked via distributions.
2. **`ct_src_*` is nearly meaningless with hping3 `--rand-source`.** Each packet carries a random source IP, so `ct_src_ltm` ≈ 1 for every flood flow. This behavior has never appeared in UNSW.
3. **`stcpb`/`dtcpb` are random initial sequence numbers.** They carry no real signal, so they should be dropped in any new experiment.
4. **The 39-feature model (the configuration chosen by NB05/NB07) cannot be used for 5G-NIDD.** It requires `sttl`/`dttl`/`ct_state_ttl`. These are leaky features (D'hooge et al. 2022), and in 5G-NIDD `sTtl` ranks **3rd** by ANOVA. It also cannot be refit due to the missing raw CSV. → **Use only the RF 31-feature model.**

---

## 3. DETECTION CAPABILITY — stress test before the data arrives

### 3.1 The latency shortcut

On `UNSW_NB15_training-set`, considering only TCP flows with a completed handshake (`ackdat > 0`):

| | Median `ackdat` | q90 | Share with `ackdat ≥ 10 ms` |
|---|---|---|---|
| Normal | **0.14 ms** | 75 ms | **24.7%** |
| Attack | **60.6 ms** | 109 ms | **99.6%** |

In UNSW, "large handshake latency" is almost synonymous with "attack." This matches NB07: `ackdat` ranks first by permutation importance and shows the largest distribution shift (KS Normal 0.27).

In 5G-NIDD, the probe sits at S1-U, between the UE and the core/MEC:
- `synack` is the probe → MEC leg, short.
- `ackdat` is the probe → **UE over the radio link** → probe leg. For 5G NSA, this leg is typically on the order of tens of ms.

So every benign HTTPS or SSH session from a phone will have `ackdat` landing in UNSW's "Attack" region.

### 3.2 Simulation on UNSW `test-final` (25,284 rows)

Scenarios: (1) set the three Bro features to 0 and `service='-'`; (2) add radio latency U(10, 40) ms to `ackdat` and `dur`, U(1, 5) ms to `synack`, then recompute `tcprtt`; (3) combine (1) and (2); (4) same as (3) but with U(30, 80) ms latency. Two thresholds: 0.5 and 0.6949 (the RF 31f threshold chosen on test-dev under the FPR ≤ 0.10 constraint in NB07).

| Scenario | ROC-AUC | FPR @0.5 | Recall @0.5 | Bal acc @0.5 | FPR @0.695 | Recall @0.695 | FPR Normal-TCP @0.5 |
|---|---|---|---|---|---|---|---|
| 0. Original | 0.9594 | 0.2569 | 0.9491 | 0.8461 | 0.1050 | 0.8607 | 0.2817 |
| 1. Missing Bro | 0.9433 | 0.2799 | 0.9452 | 0.8326 | 0.1399 | 0.8354 | 0.3110 |
| 2. 5G latency 10–40 ms | 0.9432 | 0.3499 | 0.9490 | 0.7995 | 0.1289 | 0.8554 | 0.4001 |
| **3. Missing Bro + 10–40 ms latency** | **0.9223** | **0.3756** | 0.9455 | **0.7850** | **0.1707** | 0.8252 | **0.4327** |
| 4. Missing Bro + 30–80 ms latency | 0.9108 | 0.4066 | 0.9479 | 0.7706 | 0.1948 | 0.8143 | 0.4721 |

Recall by category in scenario 3 vs. original, @0.695: Reconnaissance 0.979 → 0.899 · DoS 0.951 → 0.936 · Generic 0.978 → 0.973.

**How to read this:**
- Just **two** known differences (missing Bro, radio latency) push FPR from 25.7% to 37.6%. Recall barely changes. This is exactly the kind of failure NB07 already saw (shift concentrated in the Normal class), just more severe.
- This is a **lower bound** on the degradation. The simulation does not include other differences: benign traffic being real streaming and SSH, MTU and packet sizes after GTP decapsulation, Android's TCP window, and random source IPs.

### 3.3 Short flows — the hping3 and nmap fingerprint

On UNSW `test-final`, here is how the model handles short flows (`spkts ≤ 2`, `dpkts ≤ 1`):

| | n | Share labeled Attack @0.5 |
|---|---|---|
| Short Attack (mostly `udp/INT`) | 2,041 | **97.2%** |
| Short Normal (mostly `udp/INT`, `arp`, `tcp/REQ`) | 952 | **56.9%** |

The model treats almost every short, one-way UDP flow as an attack. For 5G-NIDD, this means:
- **UDP Flood, ICMP Flood, SYN Flood, and the scan types** (≈71% of attack flows) are **expected to be caught well.**
- But benign UDP traffic from phones (DNS, QUIC/HTTP3 for streaming services) will also be flagged as Attack. This is a second, independent source of false positives, unrelated to `ackdat`.

### 3.4 Predictions on 5G-NIDD by category (zero-shot, RF 31f)

| Type | % of flows | Predicted recall | Reason |
|---|---|---|---|
| UDP Flood | 37.6% | **High (≥0.9)** | Short `udp/INT` flow; the model catches 97% of this flow type in UNSW |
| SYN/TCP Connect/UDP Scan | 4.6% | **High (0.85–0.98)** | Corresponds to Reconnaissance (0.98 → 0.90 under stress) |
| SYN Flood, ICMP Flood | 0.9% | Moderate–high | One-way flow, no handshake; `proto=icmp` is rare in UNSW, so there is some risk |
| HTTP Flood, Slowrate DoS | 17.6% | **Possibly high, but for the wrong reason** | A complete TCP session over 5G has a large `ackdat`. The model will score it exactly like benign HTTPS, i.e., it cannot tell them apart |
| **Benign** | 39.3% | **FPR expected 40–60%** | Radio `ackdat` plus short UDP/QUIC flows |

**Illustrative calculation** (assuming Recall 0.90 and FPR 0.45, π = 0.607):
Precision = 0.90·738,153 / (0.90·738,153 + 0.45·477,737) = **0.755** · Accuracy = **0.762** · **Balanced acc = 0.725**.
An accuracy of 0.76 sounds acceptable only because 61% of flows are attacks. Balanced accuracy and FPR are the real numbers. Worth repeating NB07's lesson: **never report Accuracy alone.**

---

## 4. PITFALLS WITHIN 5G-NIDD ITSELF — must be handled before measuring

| # | Issue | Evidence | Handling |
|---|---|---|---|
| T1 | **Metadata features top the ANOVA table:** `Seq` (329,589) and `Offset` (223,792) | These are the record sequence number and offset within the Argus file, i.e., position within the file, not network behavior. Attack sessions were captured on a separate schedule (Tables III, IV of the paper) | **Drop**, along with `StartTime`, `LastTime`, `SrcAddr`, `DstAddr`, `Sport`, `Dport`, `SrcId`, `Rank` |
| T2 | **TTL / Hops:** `sTtl` ranks 3rd, `sHops` ranks 13th, `dTtl` ranks 15th | The attacker is a dedicated Raspberry Pi → TTL always encodes machine identity. Exactly the kind of leaky feature from D'hooge 2022 | Drop `sTtl`, `dTtl`, `sHops`, `dHops`. Experiment E6 will separately measure how much score inflation they add |
| T3 | **Massive duplication** | hping3 `--flood` generates hundreds of thousands of nearly identical flows (UDP Flood 457k) | Deduplicate as in NB01, **and cross-deduplicate** between train and test (NB07 found 3.22% residual leakage from deduplicating within each split only). Report n before and after deduplication |
| T4 | **Random 70/30 split** (the paper's method, yielding 99.9%) | Temporal and session-level leakage; NB07 §3 measured that a random split increases balanced acc by +0.073 on UNSW | Split by **base station** and by **attack type** |
| T5 | Benign traffic is captured **at the same time** as attacks | Benign is present in every session | Good: no "timestamp = label" shortcut in benign traffic. But must be re-checked after dropping `Seq` |

---

## 5. EXPERIMENT PLAN

General rules, inherited from NB07: **declare criteria before running** · tune the threshold on one set, report on another · always report ROC-AUC, PR-AUC, Balanced acc, MCC, Recall, FPR, plus **Recall by attack type** · paired bootstrap with 1,000 iterations for every comparison.

### Phase 0 — Collection and schema check (0.5 day)
- Download `Combined.zip` (and `BTS_1`, `BTS_2` if `Combined.csv` lacks a station column).
- Check: whether the header has `SIntPkt`, `DIntPkt`, `SrcJitter`, `DstJitter`, `StartTime`, `SrcAddr`, `Dport`; labels `Label`, `Attack Type`, `Attack Tool`; n per class matches Table XXII of the paper.
- **Gate 0:** if both group B and group C are missing, the model is reduced to 21 features → use the fallback in Phase 1.

### Phase 1 — Mapping, unit normalization, cleaning (1–2 days) → `notebooks/08_5GNIDD_Prepare.ipynb`
- Apply the mapping table in §2. Cross-check percentiles (q1, q50, q99) of each feature against UNSW to detect unit mismatches (ms/s, bit/byte).
- Drop the columns from T1 and T2. Deduplicate (T3). Write `data/5gnidd/cleaned/*.parquet`.
- Fallback if group B/C is missing: refit the RF on UNSW **using only the intersection of the two feature sets** (≈21–25 features). Compare against the RF 31f on UNSW `test-final` to learn how much dropping features costs **within-domain**, before measuring cross-domain.

### Phase 2 — Experiments → `notebooks/09_5GNIDD_CrossValidation.ipynb`

| ID | Experiment | Train | Threshold selection | Evaluate on | Question |
|---|---|---|---|---|---|
| **E1** | Zero-shot | UNSW (RF 31f, frozen) | 0.5 / 0.6949 / EM-prior (no 5G labels used) | all of 5G-NIDD, split by BS | Can the current model be used on 5G right away? |
| **E2** | Few-shot threshold calibration | UNSW (frozen) | 1% labeled from **BS1**, FPR ≤ 0.10 | **BS2** | If a small amount of 5G traffic can be labeled, does that help? |
| **E3** | Within-domain, split by station | 5G BS1 | val within BS1 | BS2 (and vice versa) | The practical ceiling on 5G |
| **E4** | Leave-one-attack-out | 5G, one attack type held out | val | the held-out type + benign | Can unseen (zero-day) attacks be detected? |
| **E5** | Combined training and domain adaptation | UNSW + 5G BS1; try CORAL | val | BS2 | Does UNSW knowledge help with 5G at all? (CORAL is on NB07 §14's "not yet tried" list) |
| **E6** | Leaky-feature check | 5G, one feature at a time | — | blind generalization (D'hooge) | How much do `sTtl`, `Seq`, `Offset` inflate the score? |
| **E7** | Reverse direction | 5G (BS1+BS2) | — | UNSW, DoS + Reconnaissance classes | Is the domain shift symmetric? |

E1 and E2 must additionally include two analyses:
- **FP breakdown**: FP by `proto`/`state`, and by `ackdat` bucket (0, <10 ms, 10–50 ms, >50 ms), to directly verify the latency-shortcut hypothesis from §3.1.
- **Ablation of `ackdat`/`synack`/`tcprtt`**: rerun E1 with a UNSW model that **excludes** these three features (refit on UNSW). If FPR on 5G drops sharply while UNSW loses only a little, this is the configuration to carry over to 5G.

### Pre-declared decision criteria

| Conclusion | Condition |
|---|---|
| "The UNSW model **transfers** to 5G" | E1: ROC-AUC ≥ 0.90 **and** Balanced acc ≥ 0.80 **and** FPR ≤ 0.20 at a threshold chosen without 5G labels |
| "Transfers **with a few labels**" | E2: Recall ≥ 0.90 with FPR ≤ 0.10 on BS2 |
| "Training within the 5G domain is required" | Both E1 and E2 fail; E3 reaches Balanced acc ≥ 0.95 |
| Reporting a figure like the original paper's (99.9%) | **Never** — may only be cited as a reference, with notes T1–T4 attached |

### Predictions, recorded in advance for later comparison

| | ROC-AUC | Balanced acc | FPR @0.5 |
|---|---|---|---|
| E1 zero-shot | 0.70–0.90 | 0.65–0.80 | **0.40–0.60** |
| E2 few labels | ROC-AUC unchanged from E1 (changing the threshold does not change the ranking — NB07 §7) | — | — |
| E3 within-domain, split by station | ≥0.98 | 0.95–0.99 | — |
| E4 leave-attack-out | lowest for HTTP Flood and Slowrate DoS (the paper also notes these two classes are often confused with each other) | — | — |

If E1 turns out **better** than this predicted range, leakage (T1, T3) must be re-checked before trusting the result.

### Compute resources
- After dropping `Seq`/`Offset`, deduplication is expected to sharply reduce the 1.2 million rows, mostly in UDP Flood. Even without reduction, an RF with 300 trees, `max_depth` 20, 25 features on 850k training rows takes about 10–20 minutes on the current machine.
- E1 and E2 do not refit the model (they reuse `rf_A_trainfit.joblib`). E3 through E7 require about 15 fits.
- Estimated total time: **4–6 working days**, including the report.

---

## 6. UNKNOWNS / LIMITATIONS OF THIS PLAN

- **The data file has not yet been opened** (requires an IEEE DataPort subscription). The column list for `Combined.csv` (groups B, C in §2) was inferred from the paper and Argus documentation, **not directly verified**.
- The stress test in §3.2 is a **simulation on UNSW data**, not a measurement on 5G-NIDD. The 10–40 ms and 30–80 ms latency ranges are reasonable assumptions for 5G NSA measured at S1-U, not measurements from 5GTN itself. The simulation only captures two known differences, so the figures in the table are a **lower bound** on the degradation.
- 5G-NIDD only contains DoS and scan attacks. No matter how good the result, **nothing** can be concluded about Exploits, Fuzzers, or Backdoor attacks on 5G.

---

**Source:** Samarakoon et al., *5G-NIDD: A Comprehensive Network Intrusion Detection Dataset Generated over 5G Wireless Network*, arXiv 2212.01298 · IEEE DataPort 10203 · D'hooge et al., PST 2022 (`References/PST_CR.pdf`) · `reports/Report_Notebook07_Results_Detailed.md`.
