# Technical Report: Root Cause Analysis of Baseline Accuracy Discrepancies

**Project:** 5G Intrusion Detection System / UNSW-NB15 Benchmark · Binary Classification (`label`: 0 = Normal, 1 = Attack)  
**Execution Date:** October 3, 2026  
**Notebook:** `notebooks/06_Root_Cause_Audit.ipynb`  
**Underlying Artifacts:** `reports/audit06/` (`thang_do_2x2x2.csv`, `cac_huong_khac_phuc.csv`, `so_sanh_thuat_toan.csv`, `ket_qua_audit06.json`, `confusion_truoc_sau.png`)

---

## 0. Executive Summary

- **Implementation Integrity:** Forensic replication of notebooks 01 through 05 identified **no coding errors, data leaks, or estimator pipeline bugs**.
- **Root Cause Drivers:** The primary drivers of lower-than-expected accuracy on the benchmark are:
  1. **Severe Official Partition Shift:** The official train/test split of UNSW-NB15 suffers from extreme covariate and prior shift (train attack rate $\pi = 0.4964$ vs. test $\pi = 0.3665$). Evaluating with stratified random 80/20 splits artificially inflates Accuracy by **+0.0955**.
  2. **Contaminant Feature Removal:** Removing the 8 contaminated Time-to-Live (TTL) and non-metadata shortcuts reduced Accuracy by **0.0112**, but was scientifically mandatory to avoid shortcut learning.
  3. **Operational Threshold Mismatch:** Evaluating at the default 0.50 threshold distorts predictions due to the base rate shift. Calibrating the decision threshold to the operating constraint $\text{FPR} \le 0.10$ raised Accuracy from **0.8186 to 0.8952** while reducing false alarms from 4,114 to 1,694.

---

## 1. Factorial Attribution Breakdown ($2 \times 2 \times 2$)

| Evaluated Dimension | Description | Accuracy Impact ($\Delta$) | Methodological Interpretation |
|---|---|---|---|
| **Data Partitioning** | Official UNSW Split vs. Stratified Random Split | **+0.0955** | Evaluating on random splits causes severe temporal data leakage, artificially inflating accuracy by nearly 10 percentage points. |
| **Contaminant Features** | Purging 8 Contaminants (TTL shortcuts) vs. Retaining | **-0.0112** | Excising non-metadata shortcuts slightly lowers accuracy on synthetic enterprise traffic, but prevents the model from relying on testbed artifacts. |
| **Deduplication** | Record Deduplication vs. Keeping Intra-Split Duplicates | **-0.0294** | Evaluating on duplicate-rich data yields artificially inflated metrics due to memorization of duplicated normal flows. |

