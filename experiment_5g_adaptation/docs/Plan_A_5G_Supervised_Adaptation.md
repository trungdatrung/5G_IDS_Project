# Plan A: Supervised 5G Domain Adaptation via Labelled 5G Telemetry

**Date:** October 27, 2026 · **Status:** 
- Trial A1 Completed (`reports/Report_A1.md`: Exceeded all operational targets).
- Trial A2 Completed (`reports/Report_A2.md`: Identified ~2,000 label threshold; H1 and H2 accepted, H3 rejected).
- Trial A3 Completed (`reports/Report_A3.md`: H4 rejected; detection dichotomy exposed).
- Trials A4 & A5: Formulated in capstone report.

**Baseline Foundations:** `experiment_5gnidd/results/Report_Cross_Validation_Options.md` (Protocols P1–P5) and `reports/5gnidd/Report_5G_NIDD_Comparison.md`.

---

## 0. Executive Summary

| Phase | Core Research Question | Primary Operational Target | Execution Runtime |
|---|---|---|---|
| **A1 Merged Model** | Can a single model achieve high performance across both UNSW and 5G domains? | BS2 ROC-AUC $\ge 0.995$ · UNSW ROC-AUC degradation $\le 0.005$ | ~12 mins |
| **A2 Label Complexity** | What is the minimum number of 5G labels required, and how should thresholds be calibrated? | $\approx 2,000$ labels $\rightarrow$ ROC-AUC $\ge 0.99$, FPR $\le 0.12$ | ~50 mins |
| **A3 Leave-One-Attack-Out** | Can the model detect unseen 5G attack classes, and does legacy enterprise data assist? | Open inquiry: Flood/Scan detected 100%; application-like attacks evade | ~20 mins |
| **A4 Model Packaging** | How should the deliverable model and Model Card be published? | `.joblib` model checkpoint + dual operating thresholds + Model Card | ~5 mins |
| **A5 Automated Telemetry** | Pipeline for capturing and processing private 5G testbed pcap data | Optional; requires live cellular testbed deployment | — |

**Locked Methodological Specifications:**
- Feature Schema: Decontaminated **LOI18** (excising Time-to-Live, sliding windows, and radio shortcuts).
- Learning Algorithm: Random Forest configured with NB07 hyperparameters (300 estimators).
- Spatial Generalization: Strict physical partitioning: **Base Station 1 (BS1) for training/validation, Base Station 2 (BS2) for testing**.
- Decision Thresholding: **Calibrated on 5G validation labels** under the constraint $\text{FPR} \le 0.10$.

---

## 1. Common Data Inputs & Partitions

| Dataset Partition | Record Count | Attack Base Rate ($\pi$) | Operational Role |
|---|---|---|---|
| `5gnidd_unsw31.parquet` (Cleaned BS1) | 208,021 | 0.8063 | Source adaptation pool: split into 5G-train (166,416) and 5G-val (41,605). |
| `5gnidd_unsw31.parquet` (Cleaned BS2) | 171,542 | 0.8658 | Single-blind, independent spatial generalization benchmark (5G-test). |
| `UNSW_NB15_training-set.parquet` | 79,147 (train-fit) | 0.4964 | Legacy enterprise training partition. |
| `UNSW_NB15_testing-set.parquet` | 25,283 (test-dev) / 25,284 (test-final) | 0.3665 | Enterprise development set (test-dev) and final test set (test-final). |

---

## 2. Trial A1 — Unified Dual-Domain Model Architecture

Evaluates 7 distinct structural configurations:
- `A1-0`: Pure UNSW baseline trained on LOI18 (measures zero-shot ceiling without shortcuts).
- `A1-1`: Pure 5G baseline trained on 5G-train BS1 using LOI18.
- `A1-2`: Equal-weighted co-training on UNSW train-fit + 5G-train BS1.
- `A1-3`: Domain-balanced co-training (50% aggregate weight to UNSW, 50% to 5G).
- `A1-4`: Multiclass 5G model with binary UNSW co-training.
- `A1-5`: Incremental tree addition: NB07 baseline expanded with 300 new 5G trees via `warm_start`.
- `A1-6`: Protocol routing switch: NB07 model for enterprise traffic, A1-1 for mobile protocols.

**Deliverable Decision:** Model `A1-2` was officially selected as the production model, achieving BS2 ROC-AUC = 0.9976, Recall = 0.9995, FPR = 0.0789, while retaining UNSW ROC-AUC = 0.9554.

---

## 3. Trial A2 — 5G Label Complexity & Few-Shot Learning Curves

Systematically evaluates sample sizes $n \in \{50, 100, 200, 500, 1000, 2000, 5000, 20000\}$ across 5 random seeds (0–4):
- Hypothesis H1 (Accepted): Co-training with legacy enterprise data at $n \le 200$ causes severe negative transfer.
- Hypothesis H2 (Accepted): 50/50 domain balancing bridges $\ge 50\%$ of the performance deficit.
- Hypothesis H3 (Rejected): Joint validation thresholding does not inflate FPR by $\ge 0.20$; instead, it stabilizes threshold variance.
- Practical Guideline: Operators must collect $\approx 2,000$ labelled 5G training flows and $\approx 500$ validation flows to achieve operational stability.

---

## 4. Trial A3 — Leave-One-Attack-Out (LOAO) Protocol

Evaluates zero-day resilience by withholding each of the 8 attack types in turn from training:
- Raw-packet floods and scans (UDPFlood, SYNFlood, ICMPFlood, SYNScan) achieve 100% recall even when completely withheld during training.
- Application-mimicking attacks (HTTPFlood, TCPConnectScan) suffer severe evasion (Recall 49.8% and 0.6%, respectively).
- Hypothesis H4 (Rejected): Legacy enterprise data does not assist in detecting unseen 5G attacks.
- Operational Insight: Expanding decision boundaries to detect TCPConnectScan accounts for 70% of false alarms on benign mobile traffic.

