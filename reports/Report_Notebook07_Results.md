# Technical Report: Notebook 07 Consolidated Replication & Benchmark Audit

**Project:** 5G Intrusion Detection System / UNSW-NB15 Benchmark · Binary Classification (`label`: 0 = Normal, 1 = Attack)  
**Notebook:** `notebooks/07_Consolidated_Rerun.ipynb` — 39 cells executed with 0 errors  
**Execution Date:** October 8, 2026 · Random Forest (300 estimators, random seed 42)  
**Computational Environment:** Python 3.11.16 · scikit-learn 1.9.1 · pandas 3.0.6 · numpy 2.4.6  
**Primary Output Directory:** `reports/rerun07/` (`ket_qua_rerun07.json`, `bang_cau_hinh.csv`, `so_sanh_thuat_toan.csv`, `thang_do_2x2.csv`, `dedup_cung_tap_danh_gia.csv`, `recall_theo_loai.csv`, `confusion_truoc_sau.png`)

---

## 0. Executive Summary

- **Exact Baseline Reproduction:** The baseline Random Forest 31-feature model at default threshold 0.5 evaluated on `test-final` achieved an Accuracy of **0.818620**, matching the benchmark serialized in `models/random_forest_v3_metrics.json` to **six decimal places**.
- **Resolution of Notebook 06 Methodological Audit:** Cross-evaluating the deduplication hypothesis while holding the evaluation test partition invariant revealed a marginal $\Delta\text{PR-AUC} = -0.0027$, matching the independent findings of `experiment_nodedup` to 4 decimal places. Notebook 06's previously reported $+0.0294$ was proven to be an artifact of evaluation partition drift.
- **Pre-Registered Winning Configuration:** Random Forest with 39 features at optimal threshold $\theta^* = 0.7311$ (calibrated on `test-dev` under $\text{FPR} \le 0.10$). Evaluated on `test-final`:
  - **Accuracy: 0.8952**
  - **Balanced Accuracy: 0.8955**
  - **Matthews Correlation Coefficient (MCC): 0.7794**
  - **Recall: 0.8967**
  - **FPR: 0.1058**
  - **PR-AUC: 0.9527**
  - **ROC-AUC: 0.9684**
- **Operational Trade-Off:** False positives dropped sharply from 4,114 to 1,694 (-58.8%), significantly alleviating analyst alert fatigue, while false negatives rose from 472 to 957 (+102.8%), with Fuzzers recall decreasing from 0.8237 to 0.6244.
- **Convergence with Notebook 05:** The independently derived optimal operating point ($\theta^* = 0.7311$) converges with the threshold selected in Notebook 05 (0.7309), confirming the robustness and stability of the operational threshold optimization protocol across 7 distinct tabular algorithms.

---

## 1. Comparative Performance on Frozen `test-final`

| Model Configuration | Decision Threshold ($\theta^*$) | Accuracy | Balanced Acc | MCC | Precision | Recall | F1 | FPR | PR-AUC | ROC-AUC | True Negatives (TN) | False Positives (FP) | False Negatives (FN) | True Positives (TP) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Baseline RF 31f** | 0.5000 | 0.8186 | 0.8461 | 0.6672 | 0.6813 | 0.9491 | 0.7925 | 0.2569 | 0.9414 | 0.9594 | 11,903 | 4,114 | 472 | 8,795 |
| **Selected RF 39f** | 0.7311 | 0.8952 | 0.8955 | 0.7794 | 0.8307 | 0.8967 | 0.8624 | 0.1058 | 0.9527 | 0.9684 | 14,323 | 1,694 | 957 | 8,310 |

---

## 2. Attack Category Recall Breakdown

| Attack Family | `test-final` Count ($n$) | Baseline RF 31f (@0.50) | Selected RF 39f (@0.7311) | $\Delta$ Recall |
|---|---|---|---|---|
| **Normal (= 1 - FPR)** | 16,017 | 0.7431 | 0.8942 | +0.1511 (FPR drops 25.7% $\rightarrow$ 10.6%) |
| **Generic** | 4,000 | 0.9990 | 0.9922 | -0.0068 |
| **Exploits** | 2,729 | 0.9784 | 0.9450 | -0.0334 |
| **Fuzzers** | 1,514 | 0.8237 | 0.6244 | -0.1993 |
| **DoS** | 609 | 0.9557 | 0.8801 | -0.0756 |
| **Reconnaissance** | 358 | 0.9637 | 0.9385 | -0.0252 |
| **Analysis** | 35 | 0.8571 | 0.6571 | -0.2000 |
| **Backdoor** | 13 | 0.7692 | 0.6923 | -0.0769 |
| **Shellcode** | 5 | 1.0000 | 1.0000 | 0.0000 |
| **Worms** | 4 | 0.7500 | 0.7500 | 0.0000 |
| **Total Attack Class** | 9,267 | 0.9491 | 0.8967 | -0.0524 |

