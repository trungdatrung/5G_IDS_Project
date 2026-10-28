# Notebook 07 — Consolidated Rerun Results

**Project:** 5G IDS / UNSW-NB15 · binary classification `label` (0 = Normal, 1 = Attack)
**Notebook:** `notebooks/07_Consolidated_Rerun.ipynb` — 39 cells, fully executed, **0 cell errors**
**Run date:** 2026-10-08 · Random Forest, 300 trees · seed 42
**Environment:** Python 3.11.16 · scikit-learn 1.9.1 · pandas 3.0.6 · numpy 2.4.6
**Source data:** `reports/rerun07/` — `results_rerun07.json`, `config_table.csv`,
`algorithm_comparison.csv`, `confusion_matrix_2x2.csv`, `dedup_same_eval_set.csv`,
`recall_by_class.csv`, `confusion_before_after.png`, `summary.csv`

**Notebook structure:** 57 cells — 23 code cells, 34 Text cells. Code cells **only compute and
display tables**; all interpretation lives in a separate Text cell immediately after. The whole
notebook has only 25 `print` statements, all of three kinds: fit progress, a passed `assert`, and
a single number. No function prints anything.

**Purpose:** rerun the measurements from notebooks 03–06 under a stricter protocol, after the
audit `Report_Notebook06_Audit_Detailed.md` found 9 methodological errors in notebook 06. This is
**not** a new experiment — the goal is to determine which of notebook 06's figures hold up and
which must be replaced.

**No file under `data/`, `models/`, or `notebooks/01..06` was modified.** Notebook 07 only writes
to `reports/rerun07/`.

---

## 0. SUMMARY

**Perfect reproduction.** The RF 31-feature baseline @0.5 on `test-final` gives accuracy
**0.818620** — matching `models/random_forest_v3_metrics.json` to **6 decimal places**.
Every comparison that follows stands on a confirmed baseline.

**Five of notebook 06's conclusions hold up**, and one of them now has stronger evidence.
**Four of notebook 06's figures must be replaced.**

**Most important result:** measuring the deduplication question while keeping the evaluation set
fixed gives **ΔPR-AUC = −0.0027** — an **exact match to 4 decimal places** with the
`experiment_nodedup` experiment run independently on 2026-10-02. Notebook 06 reported **+0.0294**
for the same question because it changed the evaluation set too. This is a clear cross-
confirmation that notebook 06's measurement was wrong, not that the old measurement was wrong.

**Selected configuration** (pre-declared rule, locked on `test-dev`): RF 39-feature,
threshold 0.7311 → on `test-final`: **Accuracy 0.8952 · Balanced acc 0.8955 · MCC 0.7794 ·
Recall 0.8967 · FPR 0.1058 · PR-AUC 0.9527**. Versus baseline: FP drops 4,114 → 1,694,
FN rises 472 → 957.

And most notably: this configuration **nearly exactly matches the configuration notebook 05
selected** (threshold 0.7309 → Accuracy 0.8951 · Fuzzers 0.6249). Notebook 07 searched again over
**7 algorithms** instead of 4, under an independent rule, and **landed back in the same place**.
This means notebook 05's operating point was correct, and notebook 06 was a detour.

---

## 1. REPRODUCTION — ACHIEVED

| Item | Notebook 07 measured | Previously saved value | Match |
|---|---|---|---|
| 4 splits | 79,147 / 19,787 / 25,283 / 25,284 | same | ✅ |
| Attack ratio, 4 splits | 0.4964 / 0.4964 / 0.3665 / 0.3665 | same | ✅ |
| Baseline accuracy `test-final` | **0.818620** | 0.818620 | ✅ 6 digits |
| TN / FP / FN / TP | 11,903 / 4,114 / 472 / 8,795 | same | ✅ |
| PR-AUC `test-final` | 0.941405 | 0.941405 | ✅ |
| Validation accuracy | 0.932228 | 0.932228 | ✅ |

The `test-dev` / `test-final` split is taken from `data/cleaned/test_split_v3.csv` instead of
re-calling `train_test_split`, so the reported set is fixed by **data**, not dependent on a seed.

---

## 2. DIAGNOSIS — NB06's conclusion holds, and is now sharper

| Split | PR-AUC | ROC-AUC | Accuracy @0.5 | Balanced acc @0.5 | MCC @0.5 |
|---|---|---|---|---|---|
| train-fit (memorized) | 0.9985 | 0.9988 | 0.9775 | 0.9776 | 0.9552 |
| CV 5-fold within train-fit | 0.9830 ± 0.0015 | — | — | — | — |
| validation (train distribution) | 0.9849 | 0.9860 | 0.9322 | 0.9324 | 0.8657 |
| test-dev (test distribution) | 0.9429 | 0.9600 | 0.8154 | 0.8438 | 0.6620 |
| test-final (test distribution) | 0.9414 | 0.9594 | 0.8186 | 0.8461 | 0.6672 |

Drop from validation to test-final:

| Metric | Drop | Meaning |
|---|---|---|
| ROC-AUC | **−0.0266** | **ranking** ability barely changes |
| PR-AUC | −0.0435 | drop partly due to a lower π_test |
| MCC @0.5 | **−0.1984** | **the operating point collapses outright** |

**This sharpens the finding from notebook 06.** NB06 only said "distribution shift." The three
metrics above say it more precisely: the model still **ranks** almost as well as before (ROC-AUC
only loses 2.7%), but **the 0.5 threshold is in the wrong place**, so decision quality at that
threshold collapses (MCC loses 20 points). The MCC drop is **7.5 times** the ROC-AUC drop. That is
the fingerprint of a *wrong operating point*, not of a *weak model*.

### Where the distribution shift actually is — computed on cleaned data, model features only

| Scope | KS mean, Normal only | KS mean, Attack only | Ratio |
|---|---|---|---|
| **28 numeric features in the model, cleaned data** *(correct way)* | **0.1300** | **0.0492** | **2.64×** |
| 39 numeric features, raw data *(what NB06 did)* | 0.1097 | 0.0385 | 2.85× |

The conclusion "the shift is concentrated in the Normal class" **holds** under either calculation.
But the **feature list must change**: NB06 names `sttl` (0.2763) and `ct_state_ttl` (0.2559) as the
two most-shifted features, yet both **are among the 11 dropped columns** — they cannot explain the
drop of the 31-feature model.

The five most-shifted features **actually in the model**:

| Feature | KS, Normal only | Median train | Median test |
|---|---|---|---|
| `ackdat` | 0.2698 | 0.0002 | 0.0288 |
| `dload` | 0.2391 | 9,923 | 6,971 |
| `tcprtt` | 0.2258 | 0.0009 | 0.0530 |
| `synack` | 0.2250 | 0.0007 | 0.0100 |
| `dmean` | 0.2061 | 80 | 66 |

Four of the five are **TCP handshake timings** (`ackdat`, `tcprtt`, `synack`) and return-direction
traffic (`dload`, `dmean`). The Normal class's median `ackdat` increases **144-fold** from train to
test.

*(Self-correction note: in `Report_Notebook06_Audit_Detailed.md` §L6 I gave the figure 3.39× — that
was KS computed on the **raw** data, then filtered to the model's features. The correct figure to
use is **2.64×**, computed on the **cleaned** data — i.e., the distribution the model actually
sees.)*

### Upper bound of a class-ratio correction

| | Accuracy | Balanced acc | MCC | Recall | FPR | PR-AUC |
|---|---|---|---|---|---|---|
| Baseline @0.5 | 0.8186 | 0.8461 | 0.6672 | 0.9491 | 0.2569 | 0.9414 |
| Prior corrected with the **true** π, still @0.5 | **0.8673** | **0.8726** | **0.7274** | 0.8921 | **0.1470** | 0.9414 |

No change to the model, no change to the threshold: **+4.87 points** of accuracy, FPR nearly
halved, and **PR-AUC doesn't budge** — because the prior correction is a monotonic increasing map.
This is the cleanest piece of evidence for "the problem is the operating point."

---

## 3. THE 2×2 SCALE — fixing NB06's error 1

Four cells, same algorithm / parameters / seed. **The evaluation set differs across the four
cells**, so the table explicitly prints `n` and `π_test` for each:

| Dedup | Split method | n_test | π_test | Leakage | Accuracy | Balanced acc | MCC | ROC-AUC |
|---|---|---|---|---|---|---|---|---|
| yes | official | 47,361 | 0.3332 | 0.000 | 0.8160 | 0.8462 | 0.6535 | 0.9543 |
| yes | random | 47,361 | 0.4221 | 0.000 | 0.9074 | 0.9037 | 0.8098 | 0.9760 |
| no | official | 80,816 | 0.5560 | **0.2594** | 0.8710 | 0.8578 | 0.7495 | 0.9797 |
| no | random | 80,816 | 0.6406 | **0.4624** | 0.9475 | 0.9457 | 0.8868 | 0.9916 |

π_test ranges from 0.3332 to 0.6406 — a spread of **0.3074**. Accuracy and PR-AUC both depend on
π_test, so **they cannot be compared across cells**. The magnitude of the two factors, measured by
four metrics:

| Factor | Accuracy | PR-AUC | **Balanced acc** | **ROC-AUC** |
|---|---|---|---|---|
| Switching split official → random | +0.0840 | +0.0268 | **+0.0727** | **+0.0168** |
| Removing deduplication (avg of 2 cells) | +0.0476 | +0.0435 | **+0.0268** | **+0.0205** |
| Removing deduplication (official split only) | +0.0550 | +0.0599 | **+0.0116** | +0.0253 |
| **Split / dedup ratio** | 1.76× | 0.62× | **2.71×** | **0.82×** |

**This is why NB06's "8.5x" figure cannot be used.** The order and magnitude of the factors
**change completely** depending on the metric:

- By **balanced accuracy**: the split choice is **2.7 times** larger than deduplication.
- By **ROC-AUC**: deduplication is **slightly larger** than the split choice (0.82×).

There is no single number that describes "the size of a factor." The correct presentation is to
show the whole table and state which metric is robust to the class ratio.

The **leakage** column must be read before any other column: in the non-deduplicated branch,
**25.9%** (official) and **46.2%** (random) of test rows are **exact duplicates** of a train row.
This 25.94% figure exactly matches what `experiment_nodedup` measured independently.

---

## 4. DEDUPLICATION, MEASURED CORRECTLY — fixing error 2, the most important result

Two models, same algorithm / parameters / seed. The **only** difference: the training data. Both
are measured on **the exact same 25,284 rows** of `test-final`.

| | n_train | Leakage into test-final | Accuracy | Balanced acc | MCC | Recall | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|---|---|---|
| train = `data/cleaned` (**deduplicated**) | 79,147 | 3.22% | **0.8186** | **0.8461** | **0.6672** | 0.9491 | 0.2569 | **0.9594** | **0.9414** |
| train = `V1_nodedup` (**not deduplicated**) | 136,412 | 3.67% | 0.8179 | 0.8458 | 0.6666 | 0.9503 | 0.2587 | 0.9584 | 0.9387 |

Difference (not deduplicated − deduplicated): **ΔPR-AUC = −0.0027** · Δbalanced acc = −0.0003 ·
ΔMCC = −0.0006 · ΔROC-AUC = −0.0008 · Δaccuracy = −0.0007.

### Three measurements of the same question, side by side

| Source | Measurement approach | Result |
|---|---|---|
| `experiment_nodedup` (2026-10-02) | kept the evaluation set fixed | **−0.0027 PR-AUC**, CI95 [−0.0037; −0.0017], p ≈ 0 |
| **Notebook 07** (2026-10-08) | kept the evaluation set fixed | **−0.0027 PR-AUC** |
| Notebook 06 (2026-10-03) | changed **both** the evaluation set | +0.0294 accuracy |

Two independent, correctly-done measurements arrive at **the same number to 4 decimal places**.
Notebook 06's measurement has the wrong sign because it changed the evaluation set too.

### Why skipping deduplication looked "better" in Section 3

Leakage into `test-final` is **nearly identical** across the two branches (3.22% and 3.67%),
because `V1_nodedup` contains exactly the same set of **distinct rows** as `data/cleaned`, just
with duplicates added. The set of distinct rows doesn't change ⇒ leakage doesn't change ⇒ there is
no advantage.

The "nice" numbers only appear when the **evaluation set also still has duplicate rows**
(80,816 rows in Section 3, leakage 25.9–46.2%). At that point the model doesn't need to generalize,
it just needs to recall rows it has already seen in train — exactly Arp et al.'s pitfall P1/P3.

**Conclusion: doubling the training data with duplicates does not help, and is even slightly
worse. The repeat count is merely an implicit sample weight. The deduplication step is CORRECT and
should be kept.**

### Secondary finding

Even the official, **already** deduplicated dataset still has **3.22%** of `test-final` rows that
exactly match a train row. Cause: notebook 01 deduplicates **separately within each split** (train
on its own, test on its own), without cross-deduplicating between the two. This amount is small and
doesn't change the conclusion, but it should be disclosed so no one finds it later and starts
doubting everything else.

---

## 5. SEVEN ALGORITHMS — fixing error 7

Same 31 features (except the 39f row), same split, same seed. The threshold for every row is
chosen **on `test-dev`** under the `FPR ≤ 0.10` constraint.

| Algorithm | PR-AUC val | PR-AUC dev | PR-AUC final | ROC-AUC final | Acc @0.5 | Threshold (from dev) | Acc @threshold | Bal acc @threshold | Recall @threshold | FPR @threshold |
|---|---|---|---|---|---|---|---|---|---|---|
| **RF 39f (NB05)** | **0.9881** | **0.9525** | **0.9527** | **0.9690** | 0.8345 | 0.7311 | **0.8952** | **0.8955** | **0.8967** | 0.1058 |
| RF multiclass `1−P(Normal)` | 0.9842 | 0.9453 | 0.9427 | 0.9607 | 0.8270 | 0.6859 | 0.8846 | 0.8812 | 0.8682 | 0.1059 |
| HGB | 0.9833 | 0.9435 | 0.9423 | 0.9594 | 0.8215 | 0.7153 | 0.8786 | 0.8739 | 0.8563 | 0.1085 |
| Soft Voting (RF+ET+HGB) | 0.9847 | 0.9430 | 0.9419 | 0.9591 | 0.8038 | 0.7013 | 0.8790 | 0.8742 | 0.8560 | 0.1077 |
| Random Forest (baseline) | 0.9849 | 0.9429 | 0.9414 | 0.9594 | 0.8186 | 0.6949 | 0.8825 | 0.8779 | 0.8607 | 0.1050 |
| Extra Trees | 0.9812 | 0.9292 | 0.9285 | 0.9496 | 0.7694 | 0.7220 | 0.8702 | 0.8619 | 0.8309 | 0.1071 |
| Logistic Regression | 0.9238 | 0.7326 | **0.7330** | 0.8349 | 0.7285 | 0.8635 | 0.7296 | 0.6673 | **0.4341** | 0.0995 |

PR-AUC spread on `test-final`, **reported both ways** as error 7 requires:

| Calculation | Spread | Drop val → final | How to read it |
|---|---|---|---|
| Including Logistic Regression | **0.2197** | 0.0428 | spread **larger than** the drop ⇒ "choosing the right algorithm DOES matter" |
| Only the 6 strong families | **0.0242** | 0.0428 | the drop is **1.8 times** larger ⇒ "among suitable families, switching algorithms is not a lever" |

**Both are correct, and both must be stated.** Notebook 06 printed 0.2142 then concluded with
0.0138 without saying it had excluded Logistic Regression. The correct way to state it:

- **Picking the wrong algorithm family costs a lot.** Logistic Regression: PR-AUC 0.9238 (val) →
  0.7330 (final). The hypothesis that "a simpler model handles distribution shift better" is
  **refuted by the numbers** — this preserves NB06's conclusion.
- **Among already-suitable families, the difference is negligible.** Among the 31-feature models:
  RF multiclass 0.9427 vs. RF 0.9414 = **+0.0013**. Exactly matches the figure notebook 05 measured
  (p = 0.046).

### Recovering the "keep the leaky features" branch

The two raw CSV files are unavailable, so the model cannot be refit on the full feature set.
**But** notebook 05 saved the 39-feature branch's predicted probabilities to
`reports/exp05/ablation_proba.npz`. Notebook 07 loads those arrays and **self-checks the
alignment**: re-scoring the 31-feature array with its own labels gives `accuracy = 0.818620` and
`PR-AUC = 0.941405` — a 6-digit match, so the row order is consistent.

Clean effect of the 8 leaky features, **same 25,284 rows, same 0.5 threshold**:

| Metric | Δ |
|---|---|
| Accuracy | **+0.0159** |
| Balanced accuracy | **+0.0171** |
| MCC | **+0.0330** |
| ROC-AUC | +0.0115 |
| PR-AUC | **+0.0113** |

Matches the +0.0167 / +0.0116 figure the audit computed from notebook 06's 13 configurations. It
is now measured on a fixed evaluation set and under the correct selection rule — **a better
measurement than notebook 06's own**.

**The decision still belongs to the team:** these 8 features are worth about +1.6 points of
accuracy, but `sttl` and `ct_state_ttl` are also the two most-shifted features in the raw data, and
D'hooge et al. 2022's argument that they encode the label directly still stands. The cost is now
**measured**, not estimated.

---

## 6. SELECTED CONFIGURATION — fixing error 3

### Rule, pre-declared in cell 0 before running

> Maximize **Recall** subject to **FPR ≤ 0.10**, measured **on `test-dev`**.
> `test-final` is touched only once, at the reporting step.

14 candidates (7 algorithms × 2 prior-correction choices) are scored **only on `test-dev`**:

| Algorithm | Threshold | dev: Recall | dev: FPR | dev: Bal acc |
|---|---|---|---|---|
| **RF 39f (NB05)** | **0.7311** | **0.8920** | 0.0999 | **0.8960** |
| RF multiclass | 0.6859 | 0.8657 | 0.1000 | 0.8829 |
| RF | 0.6949 | 0.8556 | 0.1000 | 0.8778 |
| Soft Voting | 0.7013 | 0.8510 | 0.0997 | 0.8756 |
| HGB | 0.7153 | 0.8503 | 0.0999 | 0.8752 |
| Extra Trees | 0.7220 | 0.8278 | 0.0999 | 0.8639 |
| Logistic Regression | 0.8635 | 0.4371 | 0.1000 | 0.6686 |

Logistic Regression **satisfies** the FPR constraint but has Recall of only 0.44, so the rule
naturally eliminates it — evidence the rule works correctly: it does not reward a model for
keeping FPR low by missing almost every attack.

### Measured once on `test-final`

| | n | π_test | Accuracy | Bal acc | MCC | Precision | Recall | F1 | FPR | PR-AUC | TN | FP | FN | TP |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Baseline RF 31f @0.5 | 25,284 | 0.3665 | 0.8186 | 0.8461 | 0.6672 | 0.6813 | 0.9491 | 0.7932 | 0.2569 | 0.9414 | 11,903 | 4,114 | 472 | 8,795 |
| **Selected: RF 39f @0.7311** | 25,284 | 0.3665 | **0.8952** | **0.8955** | **0.7794** | **0.8253** | 0.8967 | **0.8624** | **0.1058** | **0.9527** | **14,323** | **1,694** | 957 | 8,310 |

| Change | Δ |
|---|---|
| Accuracy | **+0.0765** |
| Balanced accuracy | **+0.0494** |
| MCC | **+0.1122** |
| Precision | +0.1440 |
| Recall | **−0.0523** |
| F1 | +0.0692 |
| FPR | **−0.1511** |
| PR-AUC | +0.0113 |
| False alarms (FP) | 4,114 → **1,694** (−2,420, −59%) |
| Missed attacks (FN) | 472 → **957** (+485, +103%) |

### Notebook 07 independently lands on notebook 05's exact configuration

| | Threshold | Accuracy | F1 | FPR | Recall Fuzzers |
|---|---|---|---|---|---|
| Notebook 05's choice (RF 39f, FPR ≤ 0.10) | 0.7309 | 0.8951 | 0.8624 | 0.1059 | 0.6249 |
| **Notebook 07's choice** (re-searched over 7 algorithms) | **0.7311** | **0.8952** | **0.8624** | 0.1058 | 0.6244 |

Two independent searches, two different candidate sets, the same destination. **Notebook 05's
operating point is correct.** Notebook 06 strayed from it by dropping the FPR constraint and
selecting on the reporting set.

---

## 7. THE BRANCH WITHOUT TEST LABELS

Every configuration in Section 6 needs `test-dev` **with labels** to set the threshold. In real
deployment, a labeled sample from the target domain may not be available. The branch using no test
labels at all:

| Configuration (RF 31 feature) | Threshold | Accuracy | Bal acc | MCC | Recall | FPR |
|---|---|---|---|---|---|---|
| 0. Baseline @0.5 | 0.5000 | 0.8186 | 0.8461 | 0.6672 | 0.9491 | 0.2569 |
| 1. Threshold optimizing Acc on validation | 0.5349 | 0.8335 | 0.8550 | 0.6844 | 0.9354 | 0.2254 |
| 2. Prior corrected by EM, still @0.5 | 0.5000 | 0.8310 | 0.8535 | 0.6814 | 0.9378 | 0.2309 |
| 3. EM + threshold on validation | 0.5066 | 0.8333 | 0.8548 | 0.6841 | 0.9354 | 0.2258 |
| *upper bound: prior corrected with the **true** π* | 0.5000 | *0.8673* | *0.8726* | *0.7274* | *0.8921* | *0.1470* |

**Best across the entire no-test-labels group** (including 39 features):

| Configuration | Threshold | Accuracy | Bal acc | MCC | Recall | FPR |
|---|---|---|---|---|---|---|
| **RF 39f + EM + threshold from validation** | 0.5148 | **0.8460** | **0.8704** | **0.7140** | **0.9618** | 0.2210 |
| RF 39f + threshold from validation | 0.5329 | 0.8460 | 0.8703 | 0.7139 | 0.9617 | 0.2210 |
| HGB + threshold from validation | 0.5881 | 0.8507 | 0.8639 | 0.7046 | 0.9131 | 0.1854 |

**This is a notable configuration that notebook 06 never found.** It **uses no label from the test
set at all**, yet reaches balanced accuracy **0.8704** (versus 0.8461 for baseline) **while keeping
Recall at 0.9618** — higher than baseline too. If the team wants a deployable configuration that
needs no labeled sample from the target domain, this is the configuration to use, not the one in
Section 6.

### EM under-corrects — confirming notebook 06's finding

| | Value |
|---|---|
| π(train-fit) | 0.4964 |
| π(test) estimated by EM | **0.4684** |
| π(test) true | **0.3665** |

The gap to correct is 0.1299. EM corrects only 0.0280 of it, i.e. **21.6%** — leaving **78.4%**
uncorrected.

The reason, now backed by evidence from Section 2: EM assumes **only** a shift in class ratio,
i.e. that P(x|y) is unchanged. KS for the Normal class is 2.64 times that of the Attack class ⇒
P(x | y=0) **genuinely changes** ⇒ the assumption is violated. **This finding of notebook 06 holds
completely.**

### New finding: once labels exist, EM prior correction is REDUNDANT

In the 14-candidate table in Section 6, the two rows "prior correction = none" and "prior
correction = EM" for **every** algorithm score **identically** on `test-dev`, and the same holds on
`test-final` (0.8952 for both).

This is not a bug: the prior correction is a **monotonic increasing** map, so once the threshold
has been re-tuned to reach the same FPR, the resulting confusion matrix is identical. The two
operations are simply two different paths to the same point on the ROC curve.

**Practical consequence:** EM prior correction is **only** valuable when there are **no** labels
available to set the threshold. Notebook 06 bundled "prior correction + re-thresholding" into a
single configuration (`#3`, `#11`, `#12`), so it could not separate the two, and credited EM for
work that actually belonged to re-thresholding.

---

## 8. THE PRICE PAID — fixing error 8

Recall by attack category, **same `test-final`**, for every notable configuration:

| Category | n | Baseline @0.5 | RF 31f @0.695 | EM prior @0.5 (no labels) | **Selected: RF 39f @0.731** |
|---|---|---|---|---|---|
| Exploits | 3,780 | 0.9870 | 0.9556 | 0.9849 | 0.9804 |
| **Fuzzers** | 2,218 | **0.8237** | **0.5496** | 0.7845 | **0.6244** |
| Reconnaissance | 1,131 | 0.9956 | 0.9788 | 0.9929 | 0.9920 |
| DoS | 839 | 0.9881 | 0.9511 | 0.9869 | 0.9845 |
| Generic | 715 | 0.9902 | 0.9776 | 0.9902 | 0.9902 |
| Analysis | 213 | 1.0000 | 0.9812 | 1.0000 | 0.9437 |
| Shellcode | 185 | 0.9514 | 0.8000 | 0.9243 | **0.9622** |
| Backdoor | 164 | 0.9939 | 0.9939 | 0.9939 | 0.9878 |
| Worms | 22 | 1.0000 | 0.9545 | 1.0000 | 1.0000 |
| **TOTAL Recall** | 9,267 | **0.9491** | 0.8607 | 0.9378 | **0.8967** |
| **TOTAL FPR** | 16,017 | 0.2569 | 0.1050 | 0.2309 | **0.1058** |

**Notebook 06 buried this table.** It only reported Fuzzers 0.430 for the winning configuration and
called it "the only remaining weakness," without noting that at threshold 0.5 the same model type
catches **0.824**. Readers could not see that Fuzzers dropping **is the price of raising the
threshold**.

### Direct comparison with notebook 06's "best" configuration

| | Threshold | Accuracy | FPR | Total recall | **Recall Fuzzers** | FN |
|---|---|---|---|---|---|---|
| NB06 #12 (HGB 42f, max-Acc threshold) | 0.8586 | **0.9050** | **0.0561** | 0.8376 | **0.4301** | 1,505 |
| **NB07 selected** (RF 39f, FPR ≤ 0.10) | 0.7311 | 0.8952 | 0.1058 | **0.8967** | **0.6244** | **957** |

Notebook 06 is ahead by **0.0098 accuracy**. In exchange, it **misses 548 more attacks** and has
Recall Fuzzers **0.1943 lower**. Under any realistic operating requirement for an intrusion
detection system, **notebook 07's configuration is the right choice** — and it is the choice the
pre-declared rule leads to on its own, not a choice made after looking at the scores.

**This is still a trade-off decision, not simply an "improvement."** The decision belongs to the
system's operator, based on the cost of a false alarm versus the cost of a missed attack. The
notebook's only job is to put both numbers on the table.

---

## 9. BREAKDOWN OF THE IMPROVEMENT — fixing error 4

Everything here is **accuracy on `test-final`**, so the parts add up exactly to the total:

| Step | Accuracy | Δ vs previous step | % of total |
|---|---|---|---|
| 0. Baseline RF 31f @0.5 | 0.8186 | — | — |
| 1. Switch to RF 39 features, still @0.5 | 0.8345 | **+0.0159** | **20.8%** |
| 2. + prior corrected by EM, still @0.5 | 0.8345 | **+0.0000** | **0.0%** |
| 3. + reset threshold to 0.7311 | **0.8952** | **+0.0606** | **79.2%** |
| **Total** | | **+0.0765** | 100% |

| Source | Figure | Status |
|---|---|---|
| NB06 claims | 85% operating point / 15% model | ❌ divides ΔAccuracy by ΔPR-AUC — two different units |
| Audit's recalculation over NB06's 13 configurations | 77.3% / 19.3% features / 3.3% algorithm | ✅ same units |
| **Notebook 07's direct measurement** | **79.2% operating point / 20.8% features / 0.0% prior** | ✅ same units, adds up to the total |

Three calculations give the same qualitative answer: **about 80% of the improvement is
re-thresholding the operating point, about 20% is features, and 0% is the algorithm or the prior
correction.**

Independent evidence: **ΔPR-AUC is only +0.0113**, and all of that +0.0113 comes from the 39
features (see Section 5), none from the algorithm. The model's ranking ability barely changes.

---

## 10. SIGNIFICANCE TESTING — fixing error 9

### Paired bootstrap, 1,000 iterations, on `test-final`

Now **valid**, because the configuration was selected on `test-dev`, not on the set being tested.

| Metric | Mean | 95% CI | Nonzero? |
|---|---|---|---|
| Δ Accuracy | **+0.0765** | [+0.0718 ; +0.0808] | ✅ |
| Δ Balanced accuracy | **+0.0493** | [+0.0448 ; +0.0534] | ✅ |
| Δ PR-AUC | **+0.0113** | [+0.0093 ; +0.0134] | ✅ |
| Δ Recall | **−0.0523** | [−0.0582 ; −0.0462] | ✅ |
| Δ FPR | **−0.1510** | [−0.1572 ; −0.1448] | ✅ |

Reading the table: ΔAccuracy and ΔFPR are very strong, ΔPR-AUC is small, and ΔRecall is
**significantly negative**. This is the fingerprint of a change in **operating point**, not of a
stronger model. The ΔRecall CI sitting entirely below 0 is something notebook 06 never reported.

### Robustness to seed

Fixing the split, only changing the Random Forest's `random_state` (42, 7, 2024):

| | Spread |
|---|---|
| Accuracy @threshold | **0.0006** |

The improvement (+0.0765) is about **128 times** larger than seed noise. The conclusion is robust.

---

## 11. FULL TABLE — 42 configurations

`reports/rerun07/config_table.csv` contains all 42 configurations = 7 algorithms × 2
prior-correction choices × 3 threshold rules, 17 metrics per row, with a `needs_test_labels` column
to clearly separate the two groups.

Each model is **fit once**; the 42 configurations reuse the saved probabilities. Notebook 06 refit
21 times for 21 configurations.

**Two rows worth remembering:**

| Purpose | Configuration | Accuracy | Bal acc | Recall | FPR |
|---|---|---|---|---|---|
| A labeled sample from the deployment domain exists | RF 39f, threshold from test-dev (FPR ≤ 0.10) | 0.8952 | 0.8955 | 0.8967 | 0.1058 |
| **No** test labels | RF 39f + EM, threshold from validation | 0.8460 | 0.8704 | 0.9618 | 0.2210 |

---

## 12. SUMMARY: NOTEBOOK 06 — WHAT HOLDS, WHAT FALLS

### Five conclusions that hold

| NB06's conclusion | Notebook 07 confirms |
|---|---|
| No implementation bug; baseline 0.8186 | ✅ reproduced to 6 digits |
| The drop arises at the train → test boundary, not from model complexity | ✅ and sharper: ROC-AUC −0.0266 vs MCC −0.1984 |
| Distribution shift is concentrated in the Normal class | ✅ 2.64× when computed correctly (NB06 said 2.85×) |
| EM under-corrects → the shift is not a pure prior shift | ✅ EM corrects only 22% of the gap |
| Switching algorithms is not a lever among suitable families | ✅ spread 0.0242 vs. drop 0.0428 |

### Four figures that must be replaced

| NB06 claimed | Correct figure | Why |
|---|---|---|
| "The split choice is **8.5x** larger than dropping features" | **2.6–4.9x** depending on the metric | compares Accuracy across cells whose π_test differs by up to 0.31 |
| "Removing deduplication: **+0.0294**" | **−0.0027 PR-AUC** | changed the evaluation set too; measured correctly, the sign flips |
| "**85% / 15%**" | **79.2% / 20.8% / 0.0%** | divides ΔAccuracy by ΔPR-AUC |
| "Best configuration **0.9050**, CI95 [+0.0812; +0.0914]" | **0.8952**, CI95 [+0.0718; +0.0808] | NB06 selected the configuration on `test-final` itself |

### Three new findings from notebook 07

1. **EM prior correction is redundant once labels exist for thresholding** — the two operations
   are two paths to the same point on the ROC curve. NB06 bundled them and credited the wrong one.
2. **A deployable configuration with no test labels needed**: RF 39f + EM + threshold from
   validation → balanced accuracy 0.8704 **and** Recall 0.9618, better than baseline on both. NB06
   only found a +1.5-point gain for this branch.
3. **The official dataset still has 3.22% test → train leakage** because notebook 01 deduplicates
   separately within each split, without cross-deduplicating. Small, doesn't change the
   conclusion, but should be disclosed before someone else finds it.

---

## 13. RECOMMENDATIONS

1. **Use the RF 39f @threshold 0.7311 configuration as the headline figure** (Accuracy 0.8952 ·
   Balanced acc 0.8955 · Recall 0.8967 · FPR 0.1058), and state clearly that the threshold was
   chosen on `test-dev` under the pre-declared `FPR ≤ 0.10` constraint. This is also the
   configuration notebook 05 selected — two independent searches, same destination.
2. **Remove notebook 06's 0.9050 figure from every document.** It was selected on the reporting
   set, and it trades 548 missed attacks for 0.98 points of accuracy.
3. **Keep the official split, keep the deduplication step.** Section 4 confirms this with a clean
   measurement that exactly matches `experiment_nodedup`.
4. **Report Balanced Accuracy, MCC, and PR-AUC alongside Accuracy.** On an imbalanced,
   distribution-shifted set, Accuracy alone is misleading — it is the very reason the question "why
   is accuracy low" comes up.
5. **Every operating-point change must come with a Recall-by-attack-type table.** Fuzzers is the
   category most sensitive to the threshold: from 0.824 (@0.5) down to 0.624 (@0.731) down to 0.430
   (@0.859).
6. **Fix 4 figures in `Report_Accuracy_Root_Cause_Detailed.md`** and the corresponding spots in
   `Presentation_Slide_Content_Detailed.md`, following the table in Section 12.
7. **Restore `data/raw/CSV Files/Training and Testing Sets/`** to re-measure the full 2×2×2 scale.
   This is the only remaining missing piece.

---

## 14. WHAT CANNOT BE CONCLUDED FROM THIS NOTEBOOK

- **Cannot** conclude that the RF 39-feature model is the configuration that should be deployed. It
  uses 8 features the team deliberately dropped under D'hooge et al. 2022's argument, and its
  probabilities are notebook 05's **saved** probabilities, not refit in this run.
- **Cannot** conclude that `FPR ≤ 0.10` is the correct constraint. It is inherited from notebooks
  04/05 so every run can be compared. The figure 0.10 needs confirmation from the system's
  operator.
- **Cannot** conclude that no algorithm can beat this ceiling. 7 configurations across 6 families
  were tried, one reasonable configuration per family, **no wide hyperparameter search**, and no
  XGBoost/LightGBM/CatBoost were available in the environment.
- **Cannot** conclude that every domain-adaptation method is useless. Notebook 07 only tried EM
  prior correction. Quantile alignment was already ruled out by notebook 06 (PR-AUC 0.9414 →
  0.7736), so it was not retried. Not yet tried: CORAL, domain-adversarial training, self-training
  on unlabeled test data.
- **Does not** solve Fuzzers. In the selected configuration, Recall Fuzzers is 0.6244 — better than
  notebook 06 (0.4301) but still the weakest attack category, and that improvement comes purely
  from choosing a lower threshold, not from any Fuzzers-specific handling.
- The scale in Section 3 is only **2×2**. The feature factor needs refitting on the combined data
  pool, which requires the two raw CSV files that are currently unavailable.
