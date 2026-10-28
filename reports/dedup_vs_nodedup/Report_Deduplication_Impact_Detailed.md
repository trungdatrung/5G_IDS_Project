# Confusion Matrices & Metrics — DEDUPLICATED vs NON-DEDUPLICATED Dataset

**Project:** 5G IDS / UNSW-NB15, binary label `label` (0 = Normal, 1 = Attack)  
**Data source:** `experiment_nodedup/reports/nodedup_results.csv` (run 2026-10-02) — no retraining, just aggregating saved results  
**Algorithm:** held absolutely constant across both branches (same RF, same preprocessing, same split, seed 42). The only variable that changes is the **training dataset**.

## 1. The two datasets

| | Deduplicated (official) | Non-deduplicated (V1) |
|---|---|---|
| Train rows | 98,934 | 170,515 |
| Test rows | 50,567 | 80,816 |
| Train attack ratio | 0.4964 | 0.6807 |
| Test attack ratio | 0.3665 | 0.5560 |
| Duplicate rows removed (train) | 75,775 | 0 |
| Contradictory rows removed (train) | 632 | 4,826 |
| **Test rows that exactly match a train row** | **1,993 (3.94%)** | **20,960 (25.94%)** |

> The last row determines how every number below should be read: skipping deduplication increases the test→train leakage rate by **6.6x**.

## 2. Controlled comparison — same evaluation set (official test-final, 25,284 rows)

This is the **only comparison that actually answers the question**: the evaluation set stays fixed, so any difference comes solely from the training data.

### 2.1  M1 - RF run1 (100 trees, unlimited depth)

**M1 - RF run1 (100 trees, unlimited depth) — train: Deduplicated (official)**  
threshold = 0.5000

| Actual \ Predicted | Normal | Attack | Total |
|---|---|---|---|
| **Normal** | TN = 11,737 | FP = 4,280 | 16,017 |
| **Attack** | FN = 465 | TP = 8,802 | 9,267 |

**M1 - RF run1 (100 trees, unlimited depth) — train: Non-deduplicated (V1)**  
threshold = 0.5000

| Actual \ Predicted | Normal | Attack | Total |
|---|---|---|---|
| **Normal** | TN = 11,827 | FP = 4,190 | 16,017 |
| **Attack** | FN = 482 | TP = 8,785 | 9,267 |

| Metric | Deduplicated (official) | Non-deduplicated (V1) | Diff |
|---|---|---|---|
| Accuracy | 0.8123 | 0.8152 | +0.0029 |
| Precision | 0.6728 | 0.6771 | +0.0042 |
| Recall (TPR) | 0.9498 | 0.9480 | −0.0018 |
| Specificity (TNR) | 0.7328 | 0.7384 | +0.0056 |
| F1 | 0.7877 | 0.7899 | +0.0023 |
| Balanced Accuracy | 0.8413 | 0.8432 | +0.0019 |
| FPR | 0.2672 | 0.2616 | −0.0056 |
| FNR | 0.0502 | 0.0520 | +0.0018 |
| NPV | 0.9619 | 0.9608 | −0.0010 |
| MCC | 0.6582 | 0.6617 | +0.0035 |
| PR-AUC | 0.9265 | 0.9240 | −0.0025 |
| ROC-AUC | 0.9547 | 0.9537 | −0.0010 |


### 2.2  M2 - RF run2 (300 trees, tuned)

**M2 - RF run2 (300 trees, tuned) — train: Deduplicated (official)**  
threshold = 0.5000

| Actual \ Predicted | Normal | Attack | Total |
|---|---|---|---|
| **Normal** | TN = 11,903 | FP = 4,114 | 16,017 |
| **Attack** | FN = 472 | TP = 8,795 | 9,267 |

**M2 - RF run2 (300 trees, tuned) — train: Non-deduplicated (V1)**  
threshold = 0.5000

| Actual \ Predicted | Normal | Attack | Total |
|---|---|---|---|
| **Normal** | TN = 11,873 | FP = 4,144 | 16,017 |
| **Attack** | FN = 461 | TP = 8,806 | 9,267 |

| Metric | Deduplicated (official) | Non-deduplicated (V1) | Diff |
|---|---|---|---|
| Accuracy | 0.8186 | 0.8179 | −0.0008 |
| Precision | 0.6813 | 0.6800 | −0.0013 |
| Recall (TPR) | 0.9491 | 0.9503 | +0.0012 |
| Specificity (TNR) | 0.7431 | 0.7413 | −0.0019 |
| F1 | 0.7932 | 0.7927 | −0.0005 |
| Balanced Accuracy | 0.8461 | 0.8458 | −0.0003 |
| FPR | 0.2569 | 0.2587 | +0.0019 |
| FNR | 0.0509 | 0.0497 | −0.0012 |
| NPV | 0.9619 | 0.9626 | +0.0008 |
| MCC | 0.6672 | 0.6666 | −0.0006 |
| PR-AUC | 0.9414 | 0.9387 | −0.0027 |
| ROC-AUC | 0.9594 | 0.9584 | −0.0010 |


### 2.3  M3 - RF run3 (calibrated + threshold at FPR<=0.10)

**M3 - RF run3 (calibrated + threshold at FPR<=0.10) — train: Deduplicated (official)**  
threshold = 0.7105

| Actual \ Predicted | Normal | Attack | Total |
|---|---|---|---|
| **Normal** | TN = 14,344 | FP = 1,673 | 16,017 |
| **Attack** | FN = 1,300 | TP = 7,967 | 9,267 |

**M3 - RF run3 (calibrated + threshold at FPR<=0.10) — train: Non-deduplicated (V1)**  
threshold = 0.7636

| Actual \ Predicted | Normal | Attack | Total |
|---|---|---|---|
| **Normal** | TN = 14,459 | FP = 1,558 | 16,017 |
| **Attack** | FN = 1,408 | TP = 7,859 | 9,267 |

| Metric | Deduplicated (official) | Non-deduplicated (V1) | Diff |
|---|---|---|---|
| Accuracy | 0.8824 | 0.8827 | +0.0003 |
| Precision | 0.8265 | 0.8346 | +0.0081 |
| Recall (TPR) | 0.8597 | 0.8481 | −0.0117 |
| Specificity (TNR) | 0.8955 | 0.9027 | +0.0072 |
| F1 | 0.8428 | 0.8413 | −0.0015 |
| Balanced Accuracy | 0.8776 | 0.8754 | −0.0022 |
| FPR | 0.1045 | 0.0973 | −0.0072 |
| FNR | 0.1403 | 0.1519 | +0.0117 |
| NPV | 0.9169 | 0.9113 | −0.0056 |
| MCC | 0.7493 | 0.7483 | −0.0010 |
| PR-AUC | 0.9418 | 0.9395 | −0.0024 |
| ROC-AUC | 0.9596 | 0.9586 | −0.0010 |


**Statistical significance test** (paired bootstrap, 1,000 iterations, diff = non-deduplicated − deduplicated; source: `experiment_nodedup/reports/Report_NoDedup.txt` §5.1):

| Stage | Δ PR-AUC | 95% CI | p | Conclusion |
|---|---|---|---|---|
| M1 | −0.00243 | [−0.00454; −0.00033] | 0.026 | Significant — worse |
| M2 | −0.00271 | [−0.00374; −0.00167] | 0.000 | Significant — worse |

## 3. "Native" evaluation on the NON-deduplicated test set (40,408 rows)

The numbers a team would **get** if they skipped deduplication on both train and test. 25.94% of rows in this test set are exact duplicates of a train row.

**M1 - RF run1 (100 trees, unlimited depth) — train: Non-deduplicated (V1)**  
threshold = 0.5000

| Actual \ Predicted | Normal | Attack | Total |
|---|---|---|---|
| **Normal** | TN = 13,175 | FP = 4,765 | 17,940 |
| **Attack** | FN = 526 | TP = 21,942 | 22,468 |

**M2 - RF run2 (300 trees, tuned) — train: Non-deduplicated (V1)**  
threshold = 0.5000

| Actual \ Predicted | Normal | Attack | Total |
|---|---|---|---|
| **Normal** | TN = 13,217 | FP = 4,723 | 17,940 |
| **Attack** | FN = 520 | TP = 21,948 | 22,468 |

**M3 - RF run3 (calibrated + threshold at FPR<=0.10) — train: Non-deduplicated (V1)**  
threshold = 0.7636

| Actual \ Predicted | Normal | Attack | Total |
|---|---|---|---|
| **Normal** | TN = 16,094 | FP = 1,846 | 17,940 |
| **Attack** | FN = 1,540 | TP = 20,928 | 22,468 |

| Metric | M1 | M2 | M3 |
|---|---|---|---|
| Accuracy | 0.8691 | 0.8702 | 0.9162 |
| Precision | 0.8216 | 0.8229 | 0.9189 |
| Recall | 0.9766 | 0.9769 | 0.9315 |
| Specificity | 0.7344 | 0.7367 | 0.8971 |
| F1 | 0.8924 | 0.8933 | 0.9252 |
| FPR | 0.2656 | 0.2633 | 0.1029 |
| MCC | 0.7462 | 0.7485 | 0.8301 |
| PR-AUC | 0.9789 | 0.9846 | 0.9851 |
| ROC-AUC | 0.9757 | 0.9794 | 0.9796 |

Compared to section 2, PR-AUC is **0.045–0.046** higher. It looks like a big jump, but it is an **illusory number**: the model does not need to generalize, it only needs to recall rows it already saw in train (data snooping via duplication — Arp et al., pitfall P1/P3).

## 4. Conclusion

1. On the same honest evaluation set, training on the **non-deduplicated data performs worse** by ~0.0025 PR-AUC across all three stages — small but statistically significant.
2. Doubling the training data (79,147 → 136,412 fit rows) **does not help**, because the added rows are just duplicates that carry no new information. The repeat count merely acts as an implicit sample weight.
3. The high scores on the non-deduplicated test set (PR-AUC ~0.985, Accuracy ~0.87–0.92) **must not be reported** as real performance.
4. **The deduplication step is correct and should be kept.**

## 5. Accompanying files

| File | Contents |
|---|---|
| `metrics_and_confusion_matrix.csv` | All 16 result rows: TN/FP/FN/TP + 14 metrics |
| `confusion_control_comparison.png` | M1/M2/M3 confusion matrices × 2 training sets, same evaluation set |
| `confusion_native_nodedup.png` | Confusion matrix for the native evaluation on the non-deduplicated test set |

*Every metric in the CSV was recomputed from TN/FP/FN/TP and cross-checked to match (deviation < 1e-6) the metric stored in the original file.*