# Machine Learning-Based Intrusion Detection System for 5G Networks: Cross-Validation & Domain Adaptation between UNSW-NB15 and 5G-NIDD

A comprehensive Network Intrusion Detection System (NIDS) research project based on Random Forest classifiers. This project evaluates cross-dataset generalization from the legacy enterprise benchmark (**UNSW-NB15**) to authentic 5G cellular network telemetry (**5G-NIDD**), investigates failure modes under zero-shot transfer, and executes supervised domain adaptation via co-training and few-shot learning.

The repository contains **source code, evaluation pipelines, comprehensive technical reports, result tables, and figures**. Heavy binary artifacts and datasets (`.parquet`, `.zip`, `.joblib`, `.npz`, etc.) are excluded per `.gitignore`. See the [Data Acquisition](#data-acquisition) section to download and place required datasets.

---

## Executive Summary & Key Results

| Experiment | Quantitative Finding | Documentation / Source |
|---|---|---|
| **UNSW-NB15 Baseline (NB07)** | Baseline RF 31 features on `test-final`: **Accuracy 0.8186 · ROC-AUC 0.9594**. Threshold-optimized RF 39 features at $\theta^* = 0.7311$: **Accuracy 0.8952 · ROC-AUC 0.9684 · FPR 0.1058**. | [`reports/Report_Notebook07_Results.md`](reports/Report_Notebook07_Results.md) |
| **Zero-Shot Transfer (UNSW → 5G-NIDD)** | **Catastrophic Transfer Collapse.** ROC-AUC drops to **0.3990** (worse than random guessing 0.5000), Balanced Accuracy 0.4461, MCC −0.0804, Benign FPR 61.10%. The root cause is profound concept shift (real 5G attacks are raw payload-free packets misclassified as benign) and cellular radio latency shortcuts (`ackdat`), not technical feature mapping errors (round-trip validation on UNSW yields ROC-AUC 0.9525). | [`reports/5gnidd/Report_5G_NIDD_Comparison.md`](reports/5gnidd/Report_5G_NIDD_Comparison.md) |
| **5G-NIDD Data Forensic Audit** | Identified a critical ground-truth defect in 5G-NIDD: **281,529 flows (58.91% of the published Benign class) were corrupted duplicates of UDP flood attacks** captured at BS1. Data sanitization reduced the dataset to 379,563 clean, verified flows. | [`reports/5gnidd/Report_5G_NIDD_Comparison.md`](reports/5gnidd/Report_5G_NIDD_Comparison.md) §5 |
| **A1: Merged Dual-Domain Model** | Unified RF model on shortcut-free **LOI18** schema: **5G BS2 ROC-AUC 0.9976 · Recall 0.9995 · FPR 0.0789**. Enterprise UNSW-NB15 ROC-AUC **0.9554** (only a 0.0015 degradation from pure UNSW model), confirming zero catastrophic forgetting. | [`experiment_5g_adaptation/reports/Report_A1.md`](experiment_5g_adaptation/reports/Report_A1.md) |
| **A2: 5G Label Complexity & Few-Shot Curves** | Operational maturity requires **~2,000 labelled 5G training flows** (+ ~500 validation flows). When labels are scarce ($n \le 200$), co-training with legacy enterprise data induces severe negative transfer. The primary operational bottleneck in low-sample adaptation is operating threshold calibration, not ranking ability. | [`experiment_5g_adaptation/reports/Report_A2.md`](experiment_5g_adaptation/reports/Report_A2.md) |
| **A3: Detection of Unseen 5G Threats (LOAO)** | Leave-one-attack-out reveals a sharp dichotomy: raw-packet floods and scans are intercepted with **100% Recall** even when withheld during training; however, application-like attacks suffer severe evasion (HTTPFlood Recall 49.8%, TCPConnectScan Recall 0.6%). Incorporating legacy enterprise data does not improve zero-day detection. | [`experiment_5g_adaptation/reports/Report_A3.md`](experiment_5g_adaptation/reports/Report_A3.md) |

---

## Directory Architecture

```
5G_IDS_Project/
├── README.md                          Project overview and reproduction guide
├── requirements.txt                   Python dependency specifications
├── Clean_Data.ipynb                   Initial exploratory cleaning notebook
├── notebooks/                         Primary UNSW-NB15 experimental pipeline (01 → 07)
│   ├── 01_Data_Cleaning.ipynb         Sanitization, contaminant feature excision (F31)
│   ├── 02_Model_Training.ipynb        Initial Random Forest model training
│   ├── 03_Model_Training_v2.ipynb      Model optimization iteration v2
│   ├── 04_Precision_Improvement.ipynb Static test-dev / test-final split generation
│   ├── 05_Model_Comparison.ipynb      Algorithm benchmark across 14 configurations
│   ├── 05_Model_Improvement.ipynb     F39 threshold tuning branch
│   ├── 06_Root_Cause_Audit.ipynb      Forensic audit of TTL shortcuts and contaminants
│   └── 07_Consolidated_Rerun.ipynb    Verified master replication script (NB07)
├── models/                            Model parameter checkpoints, feature importances (.json/.csv)
├── reports/                           Comprehensive markdown technical audit reports
│   ├── rerun07/ audit06/ exp05/       Metrics and figures across notebook phases
│   ├── dedup_vs_nodedup/              Evaluation of deduplication impacts
│   └── 5gnidd/                        5G-NIDD zero-shot transfer audit and cross-validation plans
├── experiment_nodedup/                Controlled ablation without deduplication
├── experiment_5gnidd/                 5G-NIDD data sanitization, in-domain baselines, and cross-val
│   ├── src/                           01_clean_5gnidd.py → 02_train_evaluate.py → 03_scenario_cross_validate.py
│   └── results/                       Evaluation logs, tables, and confusion matrix figures
├── experiment_5g_adaptation/          Plan A: Supervised 5G domain adaptation
│   ├── docs/                          Formal mathematical and experimental specification
│   ├── src/                           A1_merged_model.py, A2_few_shot.py, A3_loao.py
│   ├── models/                        Exported unified dual-domain model artifacts
│   ├── results/                       Metrics tables (.csv), logs, and figures
│   └── reports/                       Detailed experimental reports for A1, A2, and A3
└── bao_cao_BTL/                       Capstone graduation project reports
    ├── Khung_bao_cao_BTL.docx         Word formatting template
    ├── generate_en_figures.py         Script generating English architecture and topology diagrams
    ├── build_full_report_en.py        Comprehensive English capstone report generator
    ├── Bao_cao_BTL_English.docx       Complete final graduation report (.docx)
    └── Report_5G_IDS_Capstone.docx    Deliverable capstone report (.docx)
```

---

## Data Acquisition

### 1. UNSW-NB15 Dataset

Download the official dataset release from the University of New South Wales:
<https://research.unsw.edu.au/projects/unsw-nb15-dataset>.

Obtain the *Training and Testing Sets* CSV files and place them into:
```
data/raw/CSV Files/Training and Testing Sets/UNSW_NB15_training-set.csv
data/raw/CSV Files/Training and Testing Sets/UNSW_NB15_testing-set.csv
```

Execute `notebooks/01_Data_Cleaning.ipynb` to generate `data/cleaned/UNSW_NB15_{training,testing}-set.parquet`. Then run `notebooks/04_Precision_Improvement.ipynb` to generate `data/cleaned/test_split_v3.csv` (the immutable partition index).

### 2. 5G-NIDD Dataset

Download the raw 5G-NIDD dataset from Fairdata (identifier `9d13ef28-2ca7-44b0-9950-225359afac65`) or IEEE DataPort (Dataset 10203). License: **CC BY 4.0**. Mandatory citation:

> S. Samarakoon, C. Siriwardhana, Y. Nanayakkara, M. Liyanage, and P. Kumar, *"5G-NIDD: A Comprehensive Network Intrusion Detection Dataset Generated over 5G Wireless Network,"* IEEE Xplore, Art. no. 11098458, 2025. arXiv:2212.01298.

Place the downloaded archive files into:
```
experiment_5gnidd/data/raw/BTS1_BTS2_fields_preserved.zip   # Mandatory
experiment_5gnidd/data/raw/BTS_1.zip                        # Mandatory (delineates BS1 / BS2 boundary)
data/5gnidd/raw/{BTS1_BTS2_fields_preserved,BTS_1,BTS_2,Combined}.zip
```

The script `experiment_5gnidd/src/01_lam_sach_5gnidd.py` automatically unpacks and decontaminates the telemetry, generating `experiment_5gnidd/data/cleaned/5gnidd_unsw31.parquet`.

---

## Environment & Dependencies

Tested on Python 3.11 / 3.12, scikit-learn 1.9.1, pandas 3.0.6, numpy 2.4.6, pyarrow 25.0.1, joblib 1.6.0, and python-docx 1.2.0.

```bash
# Initialize virtual environment
python -m venv .venv
# Activate on Windows:
.venv\Scripts\activate
# Activate on Linux / macOS:
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

---

## Reproduction Pipeline

Follow these sequential steps to reproduce all experiments from raw data to final reports:

### Step 1: UNSW-NB15 Pipeline
Execute notebooks `01` through `07` in numerical sequence:
```bash
jupyter nbconvert --to notebook --execute notebooks/01_Data_Cleaning.ipynb
jupyter nbconvert --to notebook --execute notebooks/07_Consolidated_Rerun.ipynb
```

### Step 2: 5G-NIDD Sanitization & In-Domain Baseline
```bash
python -I -X utf8 experiment_5gnidd/src/01_clean_5gnidd.py .
python -I -X utf8 experiment_5gnidd/src/02_train_evaluate.py .
python -I -X utf8 experiment_5gnidd/src/03_scenario_cross_validate.py .
```

### Step 3: Plan A — Supervised 5G Domain Adaptation
```bash
python -I -X utf8 experiment_5g_adaptation/src/A1_merged_model.py .  # ~12 mins (Trains 7 variants)
python -I -X utf8 experiment_5g_adaptation/src/A2_few_shot.py .      # ~50 mins (8 sample sizes x 5 seeds)
python -I -X utf8 experiment_5g_adaptation/src/A3_loao.py .          # ~20 mins (8 LOAO classes x 2 variants)
```
*Note:* Prefix `QUICK=1` for rapid validation with 40 trees. Every script takes the project root directory as its first argument and writes strictly to its own module subdirectories.

### Step 4: Capstone Deliverables
The complete graduation capstone reports are compiled under `bao_cao_BTL/`:
- `bao_cao_BTL/Khung_bao_cao_BTL.docx`: Graduation capstone project report formatted in academic English.
- `bao_cao_BTL/Report_5G_IDS_Capstone.docx`: Full academic capstone deliverable report.

---

## Technical Reports Index

- **UNSW-NB15 Baseline & Audit**:
  - [`reports/Report_Notebook07_Results.md`](reports/Report_Notebook07_Results.md): Replicated baseline metrics and pre-registered model selection.
  - [`reports/Report_Accuracy_Root_Cause.md`](reports/Report_Accuracy_Root_Cause.md): Diagnostic investigation of accuracy discrepancies.
  - [`reports/Report_Notebook06_Audit.md`](reports/Report_Notebook06_Audit.md): Forensic audit of non-metadata TTL contaminants.
  - [`reports/dedup_vs_nodedup/Report_Deduplication_Impact.md`](reports/dedup_vs_nodedup/Report_Deduplication_Impact.md): Controlled ablation of data deduplication.
- **5G-NIDD & Zero-Shot Transfer**:
  - [`reports/5gnidd/Report_5G_NIDD_Comparison.md`](reports/5gnidd/Report_5G_NIDD_Comparison.md): Discovery of the 5G-NIDD ground-truth mislabeling defect and zero-shot transfer collapse.
  - [`reports/5gnidd/Plan_5G_NIDD_Cross_Validation.md`](reports/5gnidd/Plan_5G_NIDD_Cross_Validation.md): Cross-dataset experimental methodology.
  - [`experiment_5gnidd/results/Report_Cross_Validation_Options.md`](experiment_5gnidd/results/Report_Cross_Validation_Options.md): Empirical comparison of protocols P1 through P5.
- **Supervised 5G Domain Adaptation (Plan A)**:
  - [`experiment_5g_adaptation/README.md`](experiment_5g_adaptation/README.md): Plan A overview, execution status, and reproduction commands.
  - [`experiment_5g_adaptation/docs/Plan_A_5G_Supervised_Adaptation.md`](experiment_5g_adaptation/docs/Plan_A_5G_Supervised_Adaptation.md): Complete mathematical and experimental specification.
  - [`experiment_5g_adaptation/reports/Report_A1.md`](experiment_5g_adaptation/reports/Report_A1.md): Performance of the unified dual-domain model (A1).
  - [`experiment_5g_adaptation/reports/Report_A2.md`](experiment_5g_adaptation/reports/Report_A2.md): 5G label complexity and few-shot learning curves (A2).
  - [`experiment_5g_adaptation/reports/Report_A3.md`](experiment_5g_adaptation/reports/Report_A3.md): Resilience against novel, unseen 5G zero-day attacks (A3).
- **Capstone Graduation Report**:
  - [`bao_cao_BTL/Report_5G_IDS_Capstone.docx`](bao_cao_BTL/Report_5G_IDS_Capstone.docx): Full final capstone report formatted in Microsoft Word (.docx).
  - [`reports/Presentation_Slides_Outline.md`](reports/Presentation_Slides_Outline.md): Complete slide-by-slide thesis defense outline.
