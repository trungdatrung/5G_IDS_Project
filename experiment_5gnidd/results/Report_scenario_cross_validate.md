# Choosing a cross-validation scenario between UNSW-NB15 and 5G-NIDD

**Date:** 2026-10-27 · **Directory:** `experiment_5gnidd/` (no file outside this directory is written)
**Model:** NB07's RF (300 trees, max_depth 20, max_features 0.5, max_samples 0.7, seed 42), OneHot for `proto`/`service`/`state`.
**Operating threshold:** always chosen on the **source domain**'s validation set (FPR <= 0.10), without looking at target-domain labels.

| Step | Command | Output |
|---|---|---|
| 1. Map + clean | `python -I -X utf8 experiment_5gnidd/src/01_clean_5gnidd.py <project>` | `data/cleaned/5gnidd_unsw31*.parquet`, `results/01_cleaning_stats.json` |
| 2. E1-E4 | `python -I -X utf8 experiment_5gnidd/src/02_train_evaluate.py <project>` | `results/02_results.json`, `summary_*.csv`, `figures/` |
| 3. Compare scenarios | `python -I -X utf8 experiment_5gnidd/src/03_scenario_cross_validate.py <project>` | `results/03_all_scenarios.csv`, `03_few_shot_summary.csv`, `03_results.json` |

---

## 0. SUMMARY

| | |
|---|---|
| **Data** | 5G-NIDD, Fairdata release (CC BY 4.0). SHA-256 hashes match the version verified on 10/26 (`625F4D178C8A`, `01E6C4669E64`, `6C420140E7DC`). 1,215,890 raw flows -> **379,556** flows after removing 281,529 mislabeled duplicate captures, 554,789 duplicate rows, and 16 label-conflicting rows. |
| **Mapping** | All 31 model features, with UNSW's exact names and units (detailed mapping table: `reports/5gnidd/Report_5G_NIDD_Comparison.md` §3). The base model exactly reproduces NB07: UNSW test-final accuracy = 0.81862. |
| **Zero-shot (current model -> 5G)** | **Not viable.** ROC-AUC 0.21-0.40 across every feature set and every label alignment. The reverse direction (5G -> UNSW) gives 0.45-0.55. |
| **Most viable scenario** | **P3 - train on pooled UNSW + 5G station BS1, test on station BS2 (held out entirely) and on UNSW test-final**, using the **LOI18** feature set (18 stable features, no shortcuts). Results: BS2 ROC-AUC **0.998**, UNSW test-final **0.955** (vs. 0.957 baseline). One model serves both domains without degrading UNSW. |
| **Caveats to state when reporting** | (1) BS2 is easy: same attack tools and same victim server as BS1, so 0.998 is an optimistic figure. (2) UNSW data **adds nothing** to 5G: P3 ~= P5 (5G alone). With very few labels, few-shot transfer is even negative. (3) There is no real knowledge transfer between the two datasets. |

---

## 1. THREE COMPARISON AXES

**Feature set**

| Name | Features | Rationale |
|---|---|---|
| F31 | 31 features of the current model | Baseline |
| **LOI12** | `dur, proto, state, spkts, dpkts, sbytes, dbytes, rate, sload, dload, smean, dmean` | Exact values or Argus-formula values verified to match 99.6-100% on both datasets |
| **LOI18** | LOI12 + `sinpkt, dinpkt, sjit, djit, sloss, dloss` | Adds 6 approximated features (Spearman 0.84-0.98 in round-trip validation) |

Excluded from LOI as environment "fingerprints" or shortcuts:
- `ackdat`/`synack`/`tcprtt`: measure network latency, not attack behavior.
- `stcpb`/`dtcpb`: random TCP sequence numbers.
- `swin`/`dwin`: nearly constant.
- 4 Bro features (`service`, `trans_depth`, `ct_flw_http_mthd`, `response_body_len`): derivable only from the port.
- `ct_src_ltm`/`ct_src_dport_ltm`: counted by row order. In E1, these two features account for **58% of the importance** of the RF trained on 5G. This is the "if the source is flooding, 99/100 of the most recent records come from it" shortcut.

**Label alignment:**
- ALL: keep every UNSW attack family.
- **DR**: UNSW restricted to Normal + DoS + Reconnaissance, the same families as 5G-NIDD's attacks (DoS and scan).

**Protocol:**

| Code | Train | Test |
|---|---|---|
| P1 | UNSW | 5G (full and BS2), zero-shot |
| P2 | 5G-BS1 | UNSW test-final (reverse direction) |
| P3 | UNSW + 5G-BS1 | BS2 **and** UNSW test-final |
| P4 | k% labeled BS1 (with / without UNSW-DR), 3 seeds | BS2 |
| P5 | 5G-BS1 | BS2 (in-domain ceiling) |

---

## 2. RESULTS (ROC-AUC; Bal acc / FPR at the threshold chosen on the source domain)

| Protocol | Feature | Label | -> 5G BS2 | -> UNSW test-final* |
|---|---|---|---|---|
| P1 zero-shot | F31 | ALL | **0.354** (0.33 / 0.46) | 0.959 (baseline) |
| P1 zero-shot | LOI12 | ALL | 0.277 | 0.957 |
| P1 zero-shot | LOI18 | DR | 0.282 (0.37 / **0.96**) | 0.993 |
| P2 reverse | F31 / LOI12 / LOI18 | ALL | — | 0.454 / 0.483 / 0.477 |
| P2 reverse | LOI18 | DR | — | 0.549 |
| P5 in-domain | F31 / LOI12 / LOI18 | — | 0.999 / 0.998 / 0.998 | — |
| **P3 pooled** | **LOI18** | **ALL** | **0.998** (0.974 / 0.049) | **0.955** (0.872 / 0.122) |
| P3 pooled | LOI18 | DR | 0.997 (0.945 / 0.111) | 0.993 (0.941 / 0.107) |
| P3 pooled | F31 | ALL | 0.999 (0.984 / 0.028) | 0.958 (0.869 / 0.155) |

\* For DR, this is UNSW test-final filtered to DR (17,987 rows, pi = 0.11).

**Few-shot P4** (LOI18, BS2, average of 3 seeds):

| 5G labels (k% of BS1) | 5G-only: ROC-AUC | UNSW-DR + 5G: ROC-AUC | UNSW-DR + 5G: FPR @source threshold |
|---|---|---|---|
| 168 (0.1%) | **0.965** +/- 0.017 | 0.943 +/- 0.012 | **0.80** |
| 1,664 (1%) | 0.991 | 0.989 | 0.38 |
| 8,322 (5%) | 0.994 | 0.995 | 0.24 |
| 33,283 (20%) | 0.997 | 0.997 | 0.15 |

When pooled, UNSW test-final DR stays at 0.993 across every k level.

**Recall by attack class on BS2, source threshold:**
- P3 (LOI18, DR): every attack class reaches 0.9997-1.0; Benign FPR 0.11.
- P1 zero-shot (LOI18, DR): UDPFlood 0.003, SYNScan 0.013, SYNFlood 0.20; Benign FPR 0.96.

---

## 3. INTERPRETING THE RESULTS

1. **Zero-shot fails in every variant, and dropping the shortcuts makes it even worse** (F31 0.35 -> LOI12 0.28). After removing `ackdat` and related features, the model is left relying only on packet size and rate. On this axis, the two datasets' notion of "attack" is **reversed**: UNSW attacks carry a payload, while 5G floods/scans are bare packets. Realigning labels to DoS + Recon does not rescue this either.
2. **The reverse direction also fails** (~= 0.5). This matches Layeghy & Portmann's observation about the asymmetry, except here both directions fail.
3. **Pooled training is the only approach that yields good results on both domains.** Adding 166 thousand 5G flows does not degrade UNSW (0.957 -> 0.955). The model is capable of learning both "attack concepts" in parallel.
4. **But UNSW contributes nothing to 5G.** P3 ~= P5. With 168 5G labels, including UNSW is actually **worse** (0.943 vs. 0.965). The threshold chosen on the pooled validation set is also skewed toward UNSW, pushing the FPR on 5G up to 0.80. -> When 5G labels are scarce, the threshold **must** be chosen on the 5G label portion, not on the pooled validation set.
5. **The ~0.998 figures on BS2 do not mean the 5G problem has been solved.** BS1 and BS2 use the same hping3/nmap/slowloris tools and target the same server. Splitting by station is only a split by packet-capture location, not by a genuinely new attack type.

---

## 4. RECOMMENDATIONS

**Standard scenario set for reporting cross-validation** (in presentation order):

1. **P1 - zero-shot, used as the negative result.** Apply the current F31 model to 5G: ROC-AUC 0.40. This figure answers "can the UNSW model be used on 5G as-is".
2. **P3 - train on pooled UNSW + BS1 with LOI18; test on BS2 and UNSW test-final.** This is the main scenario. Report **both domains** side by side, splitting by station rather than randomly, with the threshold chosen on the source validation set.
3. **P4 - the few-shot curve**, answering "how many 5G labels are needed": 1,664 labels (1%) is enough to reach ROC-AUC 0.99.
4. **P5 as the ceiling**, to make clear that UNSW contributes nothing.

Choose **LOI18** over F31: it loses only 0.001-0.002 ROC-AUC, but drops the `ct_*` shortcut, network-latency features, and Bro features that cannot be measured on 5G. The resulting numbers are therefore explainable and transferable to other data.

**Recommended next step** to test genuine generalization within 5G: run **leave-one-attack-out** (holding out an entire attack type, e.g. SYNScan or SlowrateDoS, during training). Splitting by station cannot answer this question.
