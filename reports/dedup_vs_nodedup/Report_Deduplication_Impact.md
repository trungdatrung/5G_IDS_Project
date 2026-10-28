# Empirical Comparative Audit: Deduplicated vs. Non-Deduplicated Benchmarks

**Project:** 5G Intrusion Detection System / UNSW-NB15 Benchmark · Binary Classification (`label`: 0 = Normal, 1 = Attack)  
**Data Source:** `experiment_nodedup/reports/nodedup_results.csv` (Executed October 2, 2026)  
**Algorithm:** Invariant configuration across branches (identical Random Forest parameters, identical preprocessing, random seed 42). The only varying independent factor is the training set deduplication rule.

---

## 1. Structural Comparison of Partitions

| Statistical Metric | Deduplicated (Official Baseline) | Non-Deduplicated (Variant V1) | Impact of Skipping Deduplication |
|---|---|---|---|
| **Training Records** | 98,934 | 170,515 | +71,581 records (+72.4%) |
| **Testing Records** | 50,567 | 80,816 | +30,249 records (+59.8%) |
| **Attack Base Rate (Train $\pi$)** | 0.4964 | 0.6807 | Base rate shifts +18.4 percentage points |
| **Attack Base Rate (Test $\pi$)** | 0.3665 | 0.5560 | Base rate shifts +18.9 percentage points |
| **Purged Exact Duplicates (Train)** | 75,775 | 0 | Duplicates retained in training |
| **Purged Contradictions (Train)** | 632 | 4,826 | Conflicting label pairs |
| **Cross-Split Duplicates (Test $\cap$ Train)** | **1,993 (3.94%)** | **20,960 (25.94%)** | **6.6x increase in test-to-train data leakage** |

*Crucial Methodological Takeaway:* Skipping deduplication causes 25.94% of the testing set to be exact duplicates of training flows, severely corrupting out-of-sample evaluation validity.

---

## 2. Controlled Benchmark Evaluation on Invariant `test-final` (25,284 Flows)

Evaluating both training variants on the strictly frozen, identical 25,284 flows of `test-final` isolates the true generalization impact of deduplication:

### 2.1 Model M1 (Random Forest 100 Trees, Default Threshold 0.50)

| Metric | Trained with Deduplication (Official) | Trained without Deduplication (V1) | Absolute Delta ($\Delta$) |
|---|---|---|---|
| **Accuracy** | 0.8123 | 0.8152 | +0.0029 |
| **Precision** | 0.6728 | 0.6771 | +0.0042 |
| **Recall (TPR)** | 0.9498 | 0.9480 | -0.0018 |
| **Specificity (TNR)** | 0.7328 | 0.7384 | +0.0056 |
| **Balanced Accuracy** | 0.8413 | 0.8432 | +0.0019 |
| **MCC** | 0.6582 | 0.6625 | +0.0043 |
| **PR-AUC** | 0.9388 | 0.9361 | **-0.0027** |
| **ROC-AUC** | 0.9576 | 0.9574 | -0.0002 |

### 2.2 Key Scientific Conclusions

1. **Controlled Generalization Difference is Negligible:** When evaluated against an invariant, clean test set, retaining duplicates in training yields an insignificant difference in performance ($\Delta\text{PR-AUC} = -0.0027$, $\Delta\text{ROC-AUC} = -0.0002$).
2. **Apparent Inflation in Native Evaluation is Spurious:** Evaluating non-deduplicated models natively on non-deduplicated test sets reports superficially higher metrics (e.g. Accuracy ~0.89) solely because the model memorizes the 20,960 duplicate flows (25.9% of the test set).
3. **Mandatory Methodological Practice:** Removing intra-split duplicates is essential to prevent data leakage and provide realistic estimates of production detection efficacy.

