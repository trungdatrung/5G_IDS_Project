# experiment_nodedup — Ablation Study: Cleaning Without Deduplication

This module is **fully decoupled** from the rest of the project:
- Reads strictly from `../data/raw/` and `../data/cleaned/` (benchmark test partition) alongside `../models/random_forest_v2_metrics.json` (to inherit the exact hyperparameters of round 2).
- Writes strictly within `experiment_nodedup/`.
- Leaves `../notebooks/`, `../data/cleaned/`, `../models/`, and `../reports/` completely untouched.

---

## Research Question

Is observed performance variance driven by the **underlying data distribution** or the **learning algorithm**?

To rigorously isolate causal attribution, the algorithm and evaluation protocol are held strictly invariant: identical Random Forest hyperparameter configuration, identical preprocessing steps, identical partitioning scheme, identical random seed (42), and identical evaluation metrics. The only variable factor is the training set deduplication strategy.

---

## Data Cleaning Variants

All variants remove `id`, downcast numeric dtypes, and excise the 8 contaminated columns (`sttl`, `dttl`, `ct_state_ttl`, `ct_dst_ltm`, `ct_srv_dst`, `ct_dst_src_ltm`, `ct_srv_src`, `ct_dst_sport_ltm`) alongside 3 non-discriminative features—matching the exact sanitization pipeline of Notebook 01.

They differ solely in their deduplication and contradiction removal rules:

| Variant | Remove Duplicates | Remove Contradictions | Purpose |
|---|---|---|---|
| `V1_nodedup` | **No** | Yes | Primary variant: Evaluates learning without record deduplication |
| `V2_nodedup_nocontra` | **No** | **No** | Extreme baseline: Retains all duplicates and contradictory labels |
| `V0_official_recipe` | Yes | Yes | Control baseline: Replicates the official cleaned dataset |

`V0` serves as a strict internal sanity check: the sanitization function must reconstruct the official cleaned dataset with bit-for-bit equality.

---

## Dual Evaluation Methodology

To avoid false equivalencies, two distinct evaluation paradigms are reported:

- **(A) Native Evaluation**: Evaluated directly on the non-deduplicated test set. This reflects the metrics reported by practitioners who skip deduplication.
- **(B) Controlled Benchmark Evaluation**: Evaluated strictly on the identical 25,284 flows of the official `test-final` split. Because the test set is held invariant, any performance delta is causally attributable solely to training set deduplication.

Evaluation Mode (B) answers the scientific question, while Mode (A) demonstrates the inflation risks of evaluating on duplicate-rich data.

---

## Module Structure

```
experiment_nodedup/
├── README.md                 Documentation and reproduction guide
├── data/cleaned_nodedup/     Parquet partitions and test split index files
├── notebooks/                Sanitization and model evaluation notebooks
├── models/                   Model checkpoints fitted during this trial
└── reports/                  JSON/CSV metrics and technical report
```

---

## Reproduction

Execute notebooks sequentially from top to bottom. Random seed is locked at 42 across all data splits and estimators.
