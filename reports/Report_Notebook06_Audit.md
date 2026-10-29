# Methodological Review: Audit of Notebook 06 Root Cause Analysis

**Project:** 5G Intrusion Detection System / UNSW-NB15 Benchmark · Binary Classification  
**Target of Review:** `notebooks/06_Root_Cause_Audit.ipynb` (34 cells, executed October 3, 2026) and `reports/Report_Accuracy_Root_Cause.md`  
**Review Date:** October 8, 2026  
**Methodology:** Line-by-line code review, mathematical re-computation of reported metrics from `reports/audit06/results_audit06.json`, cross-verification against historical checkpoints (`models/*_metrics.json`, `reports/exp05/*.json`, and deduplication ablation reports).

---

## 0. Executive Summary

1. **Verification of Implementation:** Notebook 06's verification pipeline is sound: sanitization reproduced `data/cleaned` bit-for-bit; the baseline accuracy (0.818620) matched `models/random_forest_v3_metrics.json` to 6 decimal places; OneHot encoding introduced no test leakage. The conclusion that **"low baseline accuracy is not caused by implementation bugs"** stands firm.
2. **Methodological Defect in Factorial Comparison:** The $2 \times 2 \times 2$ factorial matrix compared accuracy across 8 cells that had **different evaluation test partitions** (47,214 vs. 52,640 vs. 82,332 records) and **different class balance ratios** ($\pi_{\text{test}}$ varied from 0.3338 to 0.6391). Because raw accuracy is sensitive to class base rates, directly comparing accuracy deltas introduced confounding bias. Recomputing using base-rate-invariant metrics:

| Evaluated Factor | Reported Accuracy Delta ($\Delta$) | Recomputed Balanced Acc ($\Delta$) | Recomputed ROC-AUC ($\Delta$) |
|---|---|---|---|
| **Partitioning (Official $\rightarrow$ Random)** | **+0.0955** | +0.0616 | +0.0194 |
| **Retaining 11 Dropped Features** | +0.0112 | +0.0125 | +0.0075 |
| **Omitting Record Deduplication** | +0.0294 | +0.0161 | +0.0156 |
| **Ratio: Partition Shift / Feature Effect** | **8.53x** | 4.94x | **2.58x** |

*Interpretation:* The conclusion that partition shift dominates feature selection remains valid in direction, but its relative magnitude was inflated from ~3x to 8.5x due to metric confounding.

3. **Elimination of Data Snooping:** In Notebook 06, the winning configuration was selected by maximizing accuracy directly on `test-final`, violating single-blind evaluation rules. This was rectified in Notebook 07 (NB07) by pre-registering a formal model selection protocol strictly on `test-dev` under an explicit false alarm constraint ($\text{FPR} \le 0.10$).

