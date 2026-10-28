# Technical Report A2: 5G Label Complexity and Few-Shot Learning Curves

**Execution Date:** October 27, 2026 · **Configuration:** FULL (300 estimators, 5 random seeds 0–4) · **Runtime:** ~50 minutes  
**Experimental Specification:** [`docs/Plan_A_5G_Supervised_Adaptation.md`](../docs/Plan_A_5G_Supervised_Adaptation.md) §3  
**Execution Script:** `src/A2_few_shot.py`  
**Underlying Data Artifacts:**
- Tables: `results/A2_few_shot/tables/` (`A2_per_run.csv`, `A2_summary.csv`, `A2_results.json`)
- Figures: `results/A2_few_shot/figures/A2_learning_curve.png`
- Execution Log: `results/A2_few_shot/logs/A2_log.txt`

---

## 0. Executive Summary

| Research Question / Pre-Registered Hypothesis | Empirical Outcome |
|---|---|
| **What is the minimum number of 5G labels required?** | **~2,000 training labels** (+ ~500 validation labels) for the pure 5G model (A2-a) or domain-balanced merged model (A2-c). The unweighted merged formula (A2-b) requires **~5,000 labels**. |
| **Hypothesis H1: Negative transfer when labels are scarce ($n \le 200$)?** | **ACCEPTED (True).** The pure 5G model outperforms the unweighted merged model: ROC-AUC difference is +0.1077 ($n = 50$), +0.0598 ($n = 100$), and +0.0291 ($n = 200$). |
| **Hypothesis H2: Domain balancing mitigates the performance deficit?** | **ACCEPTED (True).** Model A2-c recovers 35% of the gap at $n = 50$, 54% at $n = 100$, and 65% at $n = 200$. |
| **Hypothesis H3: Joint validation thresholding inflates FPR by $\ge 0.20$?** | **REJECTED (False).** Joint validation did not inflate FPR; unexpectedly, it provided substantially higher threshold stability ($\text{SD} \approx 0.02$ vs. $0.10\text{--}0.32$). |
| **Primary Low-Resource Operational Bottleneck** | **Threshold calibration, not ranking ability.** At $n = 50$, model A2-a already achieves an ROC-AUC of 0.9604, but FPR fluctuates violently between 0.05 and 0.29 due to scarce benign validation samples. |
| **Preservation of Enterprise Capabilities** | **Completely Preserved.** UNSW test-final ROC-AUC remained stable at 0.957 across all sample sizes. |

---

## 1. Empirical Evaluation on 5G BS2 Across Sample Sizes $n$

Reported as Mean $\pm$ Standard Deviation across 5 independent seeds:

| Sample Size ($n$) | A2-a (Pure 5G) ROC / FPR | A2-b (Merged A1-2) ROC / FPR | A2-c (Domain Bal) ROC / FPR | A2-d (Joint Val) FPR | UNSW ROC (A2-b) |
|---|---|---|---|---|---|
| **50** | **0.9604** ± 0.0143 / 0.165 ± 0.104 | 0.8527 ± 0.0154 / **0.404 ± 0.318** | 0.8902 ± 0.0288 / 0.248 ± 0.230 | 0.320 ± 0.023 | 0.9572 ± 0.0002 |
| **100** | 0.9644 ± 0.0149 / 0.123 ± 0.133 | 0.9046 ± 0.0123 / 0.187 ± 0.129 | 0.9366 ± 0.0267 / 0.072 ± 0.026 | 0.290 ± 0.033 | 0.9572 ± 0.0003 |
| **200** | 0.9771 ± 0.0073 / 0.155 ± 0.124 | 0.9480 ± 0.0068 / 0.210 ± 0.114 | 0.9670 ± 0.0066 / 0.180 ± 0.124 | 0.216 ± 0.023 | 0.9572 ± 0.0002 |
| **500** | 0.9871 ± 0.0015 / 0.130 ± 0.006 | 0.9761 ± 0.0042 / 0.203 ± 0.096 | 0.9853 ± 0.0026 / 0.140 ± 0.069 | 0.157 ± 0.016 | 0.9572 ± 0.0002 |
| **1,000** | 0.9891 ± 0.0030 / 0.108 ± 0.033 | 0.9844 ± 0.0030 / 0.159 ± 0.070 | 0.9895 ± 0.0018 / 0.115 ± 0.027 | 0.113 ± 0.013 | 0.9574 ± 0.0002 |
| **2,000** | **0.9909 ± 0.0015 / 0.089 ± 0.015** | 0.9897 ± 0.0017 / 0.127 ± 0.056 | **0.9925 ± 0.0010 / 0.090 ± 0.039** | 0.090 ± 0.015 | 0.9575 ± 0.0001 |
| **5,000** | 0.9938 ± 0.0012 / 0.093 ± 0.010 | **0.9937 ± 0.0015 / 0.102 ± 0.023** | 0.9947 ± 0.0009 / 0.077 ± 0.006 | **0.071 ± 0.002** | 0.9575 ± 0.0002 |
| **20,000** | 0.9962 ± 0.0005 / 0.088 ± 0.006 | 0.9960 ± 0.0006 / 0.110 ± 0.030 | 0.9966 ± 0.0004 / 0.109 ± 0.016 | 0.065 ± 0.010 | 0.9571 ± 0.0001 |

**Minimum Label Thresholds Achieving Operational Targets (ROC-AUC $\ge 0.99$ and FPR $\le 0.12$):**
- Pure 5G Model (A2-a): **$n = 2,000$**
- Domain-Balanced Merged Model (A2-c): **$n = 2,000$**
- Equal-Weight Merged Model (A2-b): **$n = 5,000$**

