# Notebook 06 Audit — tasks, findings, techniques, results, and comparison with earlier versions

**Project:** 5G IDS / UNSW-NB15 · binary classification `label` (0 = Normal, 1 = Attack)
**Audit subject:** `notebooks/06_Root_Cause_Audit.ipynb` (34 cells, run 2026-10-03) and
`reports/Report_Accuracy_Root_Cause_Detailed.md`
**Audit date:** 2026-10-08
**Audit method:** re-read all the code + saved output of notebook 06; recompute every figure
from `reports/audit06/results_audit06.json`; cross-check against `models/*_metrics.json`,
`notebooks/model_comparison_results.csv`, `reports/exp05/*.json`, and
`reports/dedup_vs_nodedup/Report_Deduplication_Impact_Detailed.md`.
**No model was rerun.** Every number below is either a saved figure or a recomputation from a
saved figure (with the formula noted at each spot).

---

## 0. SUMMARY FOR THE QUICK READER

**Notebook 06's verification section is solid.** The cleaning step reproduces `data/cleaned`
exactly; baseline 0.8186 matches `models/random_forest_v3_metrics.json` to 7 decimal places;
one-hot encoding has no leakage; split sizes are correct. The conclusion "the low accuracy is not
an implementation bug" **holds**.

**The "measuring the cause" section has a real methodological error, and it changes the
conclusion.** The 2×2×2 scale compares accuracy across 8 cells with **different evaluation sets**
(47,214 / 52,640 / 82,332 rows) and **different class ratios** (π_test ranging from 0.3338 to
0.6391). Accuracy depends on the class ratio, so the three figures in the conclusion table cannot
be compared to each other. Recomputed with class-ratio-independent metrics:

| Factor | NB06 reports (accuracy) | Recomputed (balanced acc) | Recomputed (ROC-AUC) |
|---|---|---|---|
| Split official → random | **+0.0955** | +0.0616 | +0.0194 |
| Keeping the 11 dropped features | +0.0112 | +0.0125 | +0.0075 |
| Removing deduplication | +0.0294 | +0.0161 | +0.0156 |
| **"Split / feature" ratio** | **8.53x** | 4.94x | **2.58x** |

The conclusion "the split matters 8.5x more than dropping features" is the **largest of the three
measurement approaches**. A more honest measurement gives **2.6–4.9x**. The direction of the
conclusion is still correct, but the magnitude is inflated.

**The "remediation" section has a more serious error:** the best configuration is selected via
`FIX.accuracy.idxmax()` — i.e., **the model is selected on `test-final` itself**, exactly what the
notebook's first cell forbids. The bootstrap CI is then computed for the configuration that was
just selected on that same set, so the CI95 [+0.0812; +0.0914] is **systematically optimistic**
(winner's curse). The gap between #12 and #11 is only **0.0002** accuracy — and if ranked by
balanced accuracy, #11 wins, not #12.

**Compared with earlier versions:** notebook 06's figure of 0.9050 is **not new capability**.
Notebook 05 already measured an equivalent configuration (ablation with 39 leaky features,
threshold at FPR ≤ 10%) and got **0.8951** accuracy / **0.9527** PR-AUC. Notebook 06 is ahead by
0.0098 accuracy, but pays for it with **Recall Fuzzers dropping from 0.625 to 0.430** and loses the
FPR constraint that notebooks 04/05 deliberately imposed.

---

## 1. WHAT NOTEBOOK 06 ACTUALLY DID

34 cells, split into 5 parts. The table below lists each task, the technique used, and the output
it left behind.

### Part 1 — Auditing the cleaning step (cells 2–9)

| # | Task | Technique | Output |
|---|---|---|---|
| 1.1 | Read the 2 official split files | `read_csv` + `assert` on size/NaN | train 175,341×45, test 82,332×45, 0 NaN |
| 1.2 | Check whether `df_shrink` loses information | Compare absolute/relative error per column; count duplicate rows before–after | largest error in `sjit` = 0.062 (relative 4.2×10⁻⁸); duplicate rows 75,775 **unchanged** |
| 1.3 | Drop 11 columns (8 leaky + 3 useless) | `CONTAM` + `USELESS` lists per D'hooge 2022 | 31 features + 2 label columns remain; `ct_srv_ltm` **does not exist** in the data |
| 1.4 | Drop duplicate rows, split by class | `drop_duplicates()` + `groupby('label').size()` before/after | **new finding**: removes 58.6% of Attack rows but only 10.5% of Normal rows (train) |
| 1.5 | Drop contradictory rows | `groupby(feats).label.nunique() > 1` | 632 (train) / 242 (test) |
| 1.6 | Cross-check against `data/cleaned` | Compare **every value** after `astype(str)` | **exact match**, 98,934×33 and 50,567×33 |

### Part 2 — Auditing preprocessing & modeling (cells 10–15)

| # | Task | Technique | Output |
|---|---|---|---|
| 2.1 | Reproduce NB03/04's split | `train_test_split` stratify + `assert` | 79,147 / 19,787 / 25,283 / 25,284 |
| 2.2 | Check One-Hot for leakage | Count columns; find values only seen in test; count test rows encoded all-zero | 183 columns; `state` = `ACC`,`CLO` only in test → zero vector; encoder fit **only** on train-fit |
| 2.3 | Reproduce the baseline | RF, 300 trees, NB03's parameters | test-final accuracy **0.8186** |
| 2.4 | Underfit or overfit? | 5-step ladder: train-fit → CV 5-fold → validation → test-dev → test-final | train-fit 0.9985 · CV 0.9830±0.0015 · val 0.9849 · test 0.9414 (PR-AUC) |

### Part 3 — Measuring the cause (cells 16–21)

| # | Task | Technique | Output |
|---|---|---|---|
| 3.1 | Design a 2×2×2 factorial | Pool train+test → deduplicate **globally** → assign train/test by origin or randomly; 8 cells, same algorithm/parameters/seed | `confusion_matrix_2x2x2.csv` |
| — | Measure test→train leakage | Hash each row (`pd.util.hash_pandas_object`) then `np.isin` | 0% with deduplication; 10.0–47.5% without |
| 3.2 | Separate the magnitude of the three factors | Accuracy difference across cells | +0.0955 / +0.0112 / +0.0294 |
| 3.3 | Forensic analysis of the distribution shift | Two-sample Kolmogorov–Smirnov, computed per class; `attack_cat` composition | mean KS: all 0.0530 · Normal only 0.1097 · Attack only 0.0385 |
| 3.4 | How much is due to the class-ratio shift | Correct the prior using test's **true** class ratio (upper bound) | accuracy 0.8186 → **0.8673**; FPR 0.2569 → 0.1470 |

### Part 4 — Trying remediation approaches (cells 22–32)

| # | Task | Technique | Output |
|---|---|---|---|
| 4.1 | Build the tooling | EM prior (Saerens–Latinne–Decaestecker 2002); `shift_prior`; `QuantileTransformer`; the 42-feature branch **keeps exactly the same row set** as the 31-feature branch | — |
| 4.2 | Run 13 configurations | 4 dimensions: algorithm × feature set × prior correction × threshold rule | `remediation_options.csv` |
| 4.3 | Does EM estimate correctly? | Compare estimated π with the true π | EM gives **0.4684**, true is **0.3665** → under-corrects |
| 4B | Compare 5 algorithm families | RF, Extra Trees, HistGradientBoosting, Logistic Regression, Soft Voting | `algorithm_comparison.csv` |
| 4.4 | Statistical significance test | Paired bootstrap, 1,000 iterations | ΔAcc +0.0863 CI95 [+0.0812; +0.0914]; ΔPR-AUC +0.0130 |
| 4.5–4.7 | Confusion matrices, recall by attack type, write files | — | `confusion_before_after.png`, `results_audit06.json` |

### Part 5 — Conclusions (cell 33)

Eight subsections, two of which deserve credit for academic integrity: **5.4 reports two
failed approaches** and **5.8 lists what should NOT be concluded**.

---

## 2. RE-VERIFICATION: WHAT NOTEBOOK 06 DID RIGHT

I cross-checked every key figure against files saved from earlier runs. All match:

| NB06's figure | Value | Independent cross-check source | Value | Match? |
|---|---|---|---|---|
| Baseline accuracy test-final | 0.818620 | `random_forest_v3_metrics.json` → `A: RF @0.5` | 0.8186204714 | ✅ matches to 7 digits |
| Baseline validation accuracy | 0.932228 | `random_forest_v2_metrics.json` → `Tuned - validation` | 0.932228 | ✅ |
| PR-AUC train-fit | 0.998464 | `random_forest_v2_metrics.json` → `Tuned - train-fit` | 0.998464 | ✅ |
| TN/FP/FN/TP baseline | 11,903 / 4,114 / 472 / 8,795 | `exp05/step7_final.json` → `RF-A binary @0.50` | 11,903 / 4,114 / 472 / 8,795 | ✅ |
| CV PR-AUC | 0.982977 | `exp05/step5_shift.json` → `cv_pr_auc_trainfit.mean` | 0.982977 | ✅ |
| CV standard deviation | 0.0014806 | `exp05/step5_shift.json` → `std` | 0.0014806 | ✅ |
| Size of the 4 splits | 79,147/19,787/25,283/25,284 | `exp05/step0_baseline.json` → `sizes` | same | ✅ |
| Attack ratio, 4 splits | 0.4964/0.4964/0.3665/0.3665 | `exp05/step5_shift.json` → `prevalence` | same | ✅ |

**Assessment:** notebook 06's reproduction work is rigorous and error-free. Every `assert` in the
notebook is a real assert (a concrete value, capable of failing), not a decorative one. This is
the notebook's strongest point.

---

## 3. NOTEBOOK 06'S FINDINGS — WHICH ONES HOLD

| Finding | Holds? | Audit note |
|---|---|---|
| **P1.** The cleaning step reproduces exactly, no implementation bug | ✅ **Holds** | Value-by-value comparison, backed by asserts |
| **P2.** `df_shrink` downcasts float64→float32, error 0.062 but doesn't change the dedup result | ✅ **Holds** | Verified correctly: counted duplicate rows before/after |
| **P3.** Deduplication removes ~59% of Attack rows but only 10–13% of Normal rows | ✅ **Holds, and is a valuable new finding** | Explains the mechanism behind the Attack ratio dropping from 0.68 to 0.50 |
| **P4.** The 0.13-point class-ratio shift **already exists in the raw data**, not created by cleaning | ✅ **Holds** | train drops 0.1842, test drops 0.1841 — a difference of 0.0001. This is where **a wrong sentence can be fixed** in `Report_Comparison_3_Runs.txt` §3.2 and `Presentation_Slide_Content_Detailed.md` slide 2 |
| **P5.** No underfitting, no overfitting; the entire drop happens at the train→test boundary | ✅ **Holds** | The 5-step ladder is a good way to present this |
| **P6.** One-Hot has no leakage, handles unseen values correctly | ✅ **Holds** | Count of all-zero-encoded rows = 0 |
| **P7.** Distribution shift is concentrated in the Normal class (KS 0.1097 vs 0.0385) | ✅ **Holds — and is stronger than NB06 states** | Recomputed on only the 28 features the model actually uses: Normal 0.1156 vs Attack 0.0341 = **3.39x** (NB06 says 2.85x) |
| **P8.** EM under-estimates (0.4684 vs 0.3665 true) → the shift is not a pure prior shift | ✅ **Holds, an important finding** | This is a negative result reported honestly — valuable |
| **P9.** Quantile alignment fails badly (PR-AUC 0.9414 → 0.7736) | ✅ **Holds** | The explanation (quantiles depend on the set's own composition) is correct |
| **P10.** Switching algorithms is not a lever | ⚠️ **Correct conclusion, wrong proof** | See error L5 below |
| **P11.** "The split matters 8.5x more than dropping features" | ⚠️ **Inflated** | Actually 2.6–4.9x. See error L1 |
| **P12.** "Removing deduplication makes the numbers nicer by +0.0294" | ❌ **Contradicts existing experimental evidence** | See error L2 |
| **P13.** "~85% of the improvement from the operating point, ~15% from the model" | ❌ **Not a valid calculation** | See error L4 |

---

## 4. METHODOLOGICAL ERRORS FOUND — AND THE CORRECT FIGURES

This section directly answers the "unscientific" criticism.

### L1 — The 2×2×2 scale compares accuracy across **different evaluation sets** (serious error)

The `n_test` and `pi_test` columns for the 8 cells, read directly from `results_audit06.json`:

| dedup | features | split | n_train | n_test | π_train | π_test | leakage | accuracy | balanced acc | ROC-AUC |
|---|---|---|---|---|---|---|---|---|---|---|
| yes | 31 | official | 93,462 | **47,214** | 0.4671 | **0.3338** | 0.000 | 0.8145 | 0.8454 | 0.9547 |
| yes | 31 | random | 93,462 | **47,214** | 0.4224 | **0.4224** | 0.000 | 0.9102 | 0.9068 | 0.9771 |
| yes | 42 | official | 100,630 | **52,640** | 0.4868 | **0.3605** | 0.000 | 0.8259 | 0.8577 | 0.9652 |
| yes | 42 | random | 100,630 | **52,640** | 0.4434 | **0.4434** | 0.000 | 0.9211 | 0.9195 | 0.9816 |
| no | 31 | official | 175,341 | **82,332** | 0.6806 | **0.5506** | 0.286 | 0.8633 | 0.8507 | 0.9782 |
| no | 31 | random | 175,341 | **82,332** | 0.6391 | **0.6391** | 0.475 | 0.9400 | 0.9371 | 0.9892 |
| no | 42 | official | 175,341 | **82,332** | 0.6806 | **0.5506** | 0.100 | 0.8711 | 0.8580 | 0.9814 |
| no | 42 | random | 175,341 | **82,332** | 0.6391 | **0.6391** | 0.443 | 0.9505 | 0.9481 | 0.9923 |

The notebook itself claims (cell 16): *"Same algorithm, same parameters, same seed in all 8
cells — only the three factors below change."* In reality **all three factors change the
evaluation set**:

- Switching `features` 31→42 changes which columns deduplication runs on, so **the row set also
  changes** (47,214 → 52,640 test rows, π_test 0.3338 → 0.3605).
- Switching `dedup` from yes→no jumps the test set to 82,332 rows with π_test 0.5506–0.6391.
- Switching the `split` official→random uses a different row set, and π_test is **forced to
  equal** π_train by stratification.

Accuracy is a **class-ratio-dependent** metric. So is PR-AUC (its baseline is exactly π). With a
model that has high recall like this one (0.94–0.99), a test set with more Attack rows will
automatically give higher accuracy, **with no improvement to the model whatsoever**. So these
cells cannot be compared to each other using accuracy.

**Correct figures.** Recomputing the three factors with balanced accuracy (class-ratio
independent) and ROC-AUC (also class-ratio independent), using the exact same cell-difference
formula cell 18 uses:

| Factor | accuracy (NB06) | balanced acc | ROC-AUC |
|---|---|---|---|
| Split official → random | +0.0955 | **+0.0616** | **+0.0194** |
| Keeping the 11 features | +0.0112 | +0.0125 | +0.0075 |
| Removing deduplication (avg of 4 cell pairs) | +0.0383 | +0.0161 | +0.0156 |
| Split / feature ratio | 8.53x | **4.94x** | **2.58x** |

→ The conclusion should be rewritten as: *"The train/test split is the largest of the three
factors, larger than dropping 11 features by roughly 2.6–4.9x depending on the metric."* The
direction is unchanged; the "8.5x" figure must be dropped.

### L2 — The "removing deduplication" factor is reported from **a single cell**, and contradicts existing experimental evidence

Cell 18 computes `eff_split` and `eff_feat` by averaging 2 cells, but `eff_dedup` uses **exactly
1 cell** (42 features, random split). The four cell pairs give four very different values:

| Cell pair | Δ accuracy | Δ balanced acc |
|---|---|---|
| 31 features, official split | +0.0489 | **+0.0054** |
| 42 features, official split | +0.0451 | **+0.0003** |
| 31 features, random split | +0.0298 | +0.0303 |
| 42 features, random split | **+0.0294** ← the cell NB06 picked | +0.0286 |
| Average of 4 cells | +0.0383 | +0.0161 |

NB06 reports the exact **smallest** of the four accuracy values, yet presents it on equal footing
with the other two factors (which are averages). The basis for calculation is inconsistent.

**More importantly:** rows 1–2 of the table above show that under the **official split** — the
project's actual protocol — removing deduplication yields **almost nothing** in balanced accuracy
(+0.0054 and +0.0003). This **fully matches** the `experiment_nodedup` experiment run on
2026-10-02, which measured more carefully (keeping the 25,284-row test-final evaluation set fixed,
changing only the training data) and concluded: **ΔPR-AUC = −0.0027, CI95 [−0.0037; −0.0017],
p ≈ 0 — removing deduplication performs WORSE**, and the nice numbers only appear under "native"
evaluation on a test set that still has duplicates.

Notebook 06 re-measured the same question with a **worse** design (changing the evaluation set
too), getting the opposite sign (+0.0294 instead of −0.0027), **and did not cross-check against
the earlier experiment**. Notebook 06 does explain that "+0.0294 is an illusory score because
leakage increased," so this isn't dishonesty — but it replaced a clean measurement with a dirty
one without saying so, and no one reading that table would know this question **already had a
more accurate answer** sitting in `reports/dedup_vs_nodedup/`.

### L3 — The best configuration is selected **on `test-final` itself** (the most serious error)

The notebook's cell 0 sets its own discipline:

> *"`test-final` is touched only at the final reporting step. Every threshold/feature/model
> choice is decided on `validation` or `test-dev`."*

Cell 29 does the opposite:

```python
best_name = FIX.loc[FIX.accuracy.idxmax(), 'name']   # accuracy here is accuracy on test-final
```

13 configurations are scored on `test-final`, and the highest-scoring one is picked. Cell 29 then
computes a bootstrap CI for **the exact configuration that was just selected using that same
set**. This is a textbook winner's curse: CI95 [+0.0812; +0.0914] and p ≈ 0 are **systematically
optimistic**, not a valid significance test.

Severity: high, because the gap between the top configurations sits within the noise.

| Rank | Configuration | accuracy | balanced acc |
|---|---|---|---|
| 1 by accuracy | **12. HGB 42f + prior correction** | 0.90496 | 0.8908 |
| 2 by accuracy | 11. RF 42f + prior correction | 0.90476 | **0.8920** |
| 3 | 9. HGB 31f + prior correction | 0.8930 | 0.8704 |
| 4 | 3. RF 31f + prior + threshold from test-dev | 0.8925 | 0.8725 |

#12 − #11 = **+0.00020** accuracy, i.e. 5 rows out of 25,284. And **if ranked by balanced accuracy,
#11 wins**, not #12. Calling #12 "the best configuration" is selecting on noise.

**The correct approach:** select on `test-dev` (notebooks 04 and 05 did this correctly), then
report once on `test-final`. Notebook 05 took one further correct step: pre-declaring the
`FPR ≤ 0.10` constraint as the selection criterion, leaving no room for fishing.

### L4 — "85% of the improvement from the operating point, 15% from the model" is not a valid calculation

This statement is derived from: ΔAccuracy = +0.0863 and ΔPR-AUC = +0.0130. The two quantities are
in **different units, different scales, different meanings** — they cannot be divided by each
other to get a percentage.

**The correct decomposition** must use a single unit. All three figures below are accuracy on
`test-final`, taken from the same 13-configuration table:

| Component | Reference configurations | Δ accuracy | Share |
|---|---|---|---|
| From keeping the 11 features | #0 (0.8186) → #10 RF 42f @0.5 (0.8353) | **+0.0167** | 19.3% |
| From switching RF → HGB | #0 (0.8186) → #8 HGB 31f @0.5 (0.8215) | **+0.0029** | 3.3% |
| From prior correction + re-thresholding | the remainder | **+0.0668** | **77.3%** |
| **Total** | #0 → #12 | **+0.0863** | 100% |

NB06's qualitative conclusion (*the improvement comes mainly from the operating point, not from a
stronger model*) **still holds**, and now has a valid figure to back it: **77% operating point,
19% features, 3% algorithm**.

### L5 — The conclusion "switching algorithms is not a lever" uses a different number than the one the notebook printed

Cell 28 prints:

```
Spread across algorithms: within the train distribution 0.0611 | on test-final 0.2142
Average drop from validation to test-final: 0.0752
HOW TO READ: if the drop (from distribution shift) is MUCH LARGER than the spread across
algorithms, then switching algorithms is not a lever.
```

By the exact reading rule that same cell sets: 0.0752 is **not** larger than 0.2142, so the
conclusion should be *"switching algorithms IS a lever."* But markdown cell 33 instead states:

> *"The four tree-based algorithm families ... sit within **0.0138** PR-AUC of each other ...
> while the drop ... is 0.0752 — 5 times larger."*

In other words, the markdown **silently excluded Logistic Regression** from the spread to flip the
conclusion. 0.2142 is the spread including Logistic (0.9423 − 0.7281); 0.0138 is the spread among
only the 4 tree-based families (0.9423 − 0.9285). I confirm both figures are computed correctly —
the problem is that **the number printed in the notebook and the number used to draw the
conclusion are two different numbers**, with no line explaining the exclusion of Logistic.

The final conclusion (*among tree-based families, switching algorithms doesn't add anything
meaningful*) is **correct** — HGB beats RF by only +0.0009 PR-AUC. The presentation just needs to
be fixed to match.

### L6 — KS computed on **raw** data and on features the model doesn't even use

Cell 19 computes KS on `raw['training']` / `raw['testing']` — i.e., data **before** deduplication
and **before** dropping columns. The model, however, trains on deduplicated data (losing 59% of
Attack rows) and uses only 31 features. So the KS table describes a different distribution from
the one the model actually sees.

Concrete consequence: 3 of the 6 "most-shifted" features named in conclusion §5.2 — `sttl`
(0.2763), `ct_state_ttl` (0.2559), `dttl` (0.2055) — **are among the 11 dropped columns**, so they
cannot explain the drop of the 31-feature model.

**Good news:** the conclusion "the shift is concentrated in the Normal class" holds under every
calculation:

| Calculation scope | KS mean, Normal only | KS mean, Attack only | Ratio |
|---|---|---|---|
| 39 numeric features, **raw** data (what NB06 used) | 0.1097 | 0.0385 | 2.85× |
| 28 features in the model, **raw** data | 0.1156 | 0.0341 | 3.39× |
| 11 dropped features, **raw** data | 0.0946 | 0.0495 | 1.91× |
| **28 features in the model, CLEANED data** *(correct way)* | **0.1300** | **0.0492** | **2.64×** |

The last row is the figure that should be used, because it is the distribution the **model
actually sees** — columns dropped and duplicate rows removed. It is measured in notebook 07 (see
`reports/Report_Notebook07_Results_Detailed.md` §2).

The list of most-shifted features **in the model, on cleaned data** should instead read:
`ackdat` 0.2698 · `dload` 0.2391 · `tcprtt` 0.2258 · `synack` 0.2250 · `dmean` 0.2061.
Four of the five are TCP handshake timings and return-direction traffic.

(Note: notebook 05's `reports/exp05/step5_shift.json` already computed KS **on cleaned data and
only on the model's features** — the correct way. NB06 redid this worse.)

### L7 — Comparing "28 standard deviations of CV" compares two unlike things

(0.982977 − 0.941405) / 0.0014806 = 28.08 — the arithmetic is correct. But the standard deviation
across CV folds measures **sampling noise of the CV estimate within the same distribution**, not a
measure of distribution shift. Dividing the two to get a large number sounds impressive, but has
no statistical meaning. The statement "PR-AUC drops 0.0416 from CV to test-final" is sufficient on
its own.

### L8 — Notebook 06 **cannot be rerun** on the current synced copy

Cell 1 sets `RAW = BASE/'data'/'raw'/'CSV Files'/'Training and Testing Sets'`, and cell 3 reads
`UNSW_NB15_training-set.csv` and `UNSW_NB15_testing-set.csv` from there. That folder **does not
exist** in the current synced copy (`data/raw/CSV Files/` only has `UNSW-NB15_1..4.csv`,
`NUSW-NB15_GT.csv`, `NUSW-NB15_features.csv`, `UNSW-NB15_LIST_EVENTS.csv`). Parts 1 and 3 of the
notebook depend entirely on these two files, so they currently **cannot be reproduced**; only
Parts 2 and 4 run, since they use `data/cleaned/*.parquet` (which is available).

The two files may still be on Google Drive but not yet synced locally, or they may have been
moved. This needs to be confirmed and restored — otherwise Part 1's claim of "matching
`data/cleaned` exactly" is an assertion no one can re-verify.

### L9 — Presentation problems: why the notebook is so hard to read

This section directly answers the "too hard to understand" criticism:

1. **13 configurations in one flat list, mixing 4 dimensions.** A name like `"12. HGB 42f + prior
   correction"` forces the reader to remember on their own that #12 differs from #0 in **three**
   ways (algorithm, feature set, threshold+prior). No table states which configuration is a
   single-variable comparison against which other one.
2. **Parts 3 and 4 each refit 21 models that share nothing with each other** (8 scale cells +
   13 configurations), ~22 minutes total. The two parts build the data two different ways
   (`pool()` deduplicates **globally** over train+test; `cleaned_with_contaminants()` deduplicates
   **within each split**), so the numbers in Part 3 and Part 4 cannot be directly compared — and
   the notebook never says so.
3. **Code comments are in unaccented Vietnamese, markdown is in accented Vietnamese.** The reader
   must jump between two writing systems.
4. **Cell 33 is a 90-line markdown block with 8 subsections and 6 tables** — it is a report
   embedded inside the notebook, almost entirely duplicating
   `reports/Report_Accuracy_Root_Cause_Detailed.md`. The two copies will drift apart the moment
   one side gets edited.
5. **There is no one-line-per-factor summary table at the top of the notebook.** The reader must
   run through the full 22 minutes before seeing the conclusion.

---

## 5. EACH TECHNIQUE USED AND ITS ACTUAL RESULT

### 5.1 Thirteen remediation configurations (test-final, 25,284 rows)

| # | Technique | Threshold | Accuracy | Bal. acc | Recall | FPR | F1 | PR-AUC | Uses test labels? | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | RF 31f @0.5 — **baseline** | 0.500 | 0.8186 | 0.8461 | 0.9491 | 0.2569 | 0.7932 | 0.9414 | — | reference |
| 1 | + threshold optimizing Acc on validation | 0.535 | 0.8335 | 0.8550 | 0.9354 | 0.2254 | 0.8046 | 0.9414 | **No** | ✅ cheap, usable right away |
| 2 | + prior corrected by EM | 0.500 | 0.8310 | 0.8535 | 0.9378 | 0.2309 | 0.8026 | 0.9414 | **No** | ✅ usable, but under-corrects |
| 3 | + prior correction + threshold on test-dev | 0.794 | 0.8925 | 0.8725 | 0.7978 | 0.0528 | 0.8447 | 0.9414 | Yes (test-dev) | ✅ most effective on 31f |
| 4 | Distribution alignment by quantile | 0.500 | 0.7314 | 0.7561 | 0.8485 | 0.3363 | 0.6984 | **0.7736** | No | ❌ **fails badly** |
| 5 | #4 + prior correction | 0.775 | 0.7617 | 0.7342 | 0.6312 | 0.1628 | 0.6600 | **0.7736** | Yes | ❌ fails |
| 6 | RF 24f (drop the 7 most-shifted features) | 0.500 | 0.8200 | 0.8476 | 0.9510 | 0.2557 | 0.7948 | 0.9393 | No | ➖ no effect (+0.0014) |
| 7 | #6 + prior correction | 0.780 | 0.8903 | 0.8722 | 0.8045 | 0.0600 | 0.8432 | 0.9393 | Yes | ➖ worse than #3 |
| 8 | HGB 31f @0.5 | 0.500 | 0.8215 | 0.8485 | 0.9498 | 0.2527 | 0.7959 | 0.9423 | No | ➖ +0.0029, not meaningful |
| 9 | HGB 31f + prior correction | 0.841 | 0.8930 | 0.8704 | 0.7860 | 0.0451 | 0.8433 | 0.9423 | Yes | ✅ on par with #3 |
| 10 | RF 42f (keep the leaky features) @0.5 | 0.500 | 0.8353 | 0.8643 | 0.9727 | 0.2442 | 0.8124 | 0.9530 | No | ✅ +0.0167 — **cleanest measurement** of the 11 features' value |
| 11 | RF 42f + prior correction | 0.817 | 0.9048 | **0.8920** | 0.8444 | 0.0603 | **0.8667** | 0.9530 | Yes | ✅ **best by balanced acc & F1** |
| 12 | HGB 42f + prior correction | 0.859 | **0.9050** | 0.8908 | 0.8376 | 0.0561 | 0.8660 | **0.9544** | Yes | ⚠️ NB06 calls this best, but it beats #11 by exactly 0.0002 |

**How to read this table correctly:**

- Configurations 1, 2, 6, 8, 10 (and #4, which failed) are the **no test labels needed** group →
  usable in real deployment. The maximum gain in this group is **+1.67 points** (#10), and if 31
  features must be kept, only **+1.49 points** (#1).
- Configurations 3, 7, 9, 11, 12 gain +7 to +8.6 points but **all need a labeled sample from the
  deployment distribution** to set the threshold. This is not a model improvement, it is a change
  of operating point.
- #4 and #5 are **negative results, reported honestly** — a point in the notebook's favor.

### 5.2 The ignored cost: raising the threshold collapses attack-catching capability

Notebook 06 reports improved accuracy / F1 / FPR, but never places it next to its cost:

| Metric | #0 baseline @0.5 | #12 @0.859 | Change |
|---|---|---|---|
| Total recall | 0.9491 | 0.8376 | **−0.1115** |
| FN (missed attacks) | 472 | 1,505 | **+1,033 (+219%)** |
| FP (false alarms) | 4,114 | 898 | −3,216 (−78%) |
| **Recall Fuzzers** | **0.8237** (†) | **0.4301** | **−0.3936** |

(†) taken from `reports/exp05/step6_fuzzers.json` — same RF-A model, same `test-final`,
threshold 0.5.

Notebook 06 does note "Fuzzers 0.430 remains the only weakness" (§5.7) but **never states that
raising the threshold to 0.859 is exactly what dropped it from 0.824**. A reader of §5.5 would
think this is a pre-existing weakness, not a cost just paid. For an IDS, missing 1,033 additional
attacks to cut 3,216 false alarms is a **trade-off decision that must be stated explicitly and
decided by a human**, not a plain "improvement."

### 5.3 Five algorithms

| Algorithm | PR-AUC val | PR-AUC test-final | ROC-AUC test-final | Acc @0.5 | Acc @threshold | F1 @threshold | Seconds |
|---|---|---|---|---|---|---|---|
| Random Forest | 0.9849 | 0.9414 | 0.9594 | 0.8186 | 0.8925 | 0.8448 | 126 |
| HistGradientBoosting | 0.9833 | **0.9423** | 0.9594 | 0.8215 | 0.8930 | 0.8433 | 110 |
| Soft Voting (RF+ET+HGB) | 0.9847 | 0.9419 | 0.9591 | 0.8038 | **0.8950** | **0.8462** | 113 |
| Extra Trees | 0.9812 | 0.9285 | 0.9496 | 0.7694 | 0.8798 | 0.8250 | 115 |
| Logistic Regression | 0.9238 | **0.7281** | 0.8337 | 0.7270 | 0.7298 | 0.6091 | 26 |

- Spread across the 4 tree-based families: **0.0138** PR-AUC. HGB beats RF by **+0.0009** —
  within noise.
- Logistic Regression collapses from 0.9238 → 0.7281. The hypothesis *"a simpler model handles
  distribution shift better"* is **refuted by the numbers** — a valuable result.
- Soft Voting gives the highest F1 at the operating point, but PR-AUC stays in the same range →
  no ceiling is broken.

---

## 6. COMPARISON WITH EARLIER NOTEBOOK VERSIONS

### 6.1 Same evaluation set: `test-final`, 25,284 rows

Every row below is evaluated on **the exact same 25,284 rows**
(`data/cleaned/test_split_v3.csv`, seed 42), so they can be directly compared.

| Version | Configuration | Threshold | Accuracy | Precision | Recall | F1 | FPR | PR-AUC | Where was the threshold chosen |
|---|---|---|---|---|---|---|---|---|---|
| **NB02** | RF, 100 trees, default | 0.500 | 0.8156 | 0.6773 | 0.9491 | 0.7905 | 0.2616 | 0.9264 | not chosen |
| **NB03** | RF, 300 trees, tuned | 0.515 | 0.8287 | 0.6965 | 0.9438 | 0.8015 | 0.2379 | 0.9420 | CV on train-fit |
| **NB04** | + isotonic calibration, threshold FPR ≤ 0.10 | 0.711 | 0.8820 | 0.8251 | 0.8605 | 0.8424 | 0.1055 | 0.9416 | test-dev, pre-declared constraint |
| **NB05** | RF multiclass `1−P(Normal)`, FPR ≤ 0.10 | 0.686 | 0.8846 | 0.8259 | 0.8682 | 0.8465 | 0.1059 | 0.9427 | test-dev, pre-declared constraint |
| **NB05** | *(ablation)* RF 39 leaky features, FPR ≤ 0.10 | 0.731 | 0.8951 | 0.8305 | 0.8968 | **0.8624** | 0.1059 | 0.9527 | test-dev, pre-declared constraint |
| **NB06** | #3 RF 31f + EM prior + max-Acc threshold | 0.794 | 0.8925 | 0.8974 | 0.7978 | 0.8447 | 0.0528 | 0.9414 | test-dev, **no** constraint |
| **NB06** | #12 HGB 42f + EM prior + max-Acc threshold | 0.859 | **0.9050** | 0.8963 | 0.8376 | 0.8660 | 0.0561 | **0.9544** | test-dev, **no** constraint; **configuration selected on test-final** |

Note the baseline differs between notebooks: NB02 uses an RF with 100 trees and unlimited depth
(0.8156); from NB03 onward, tuned parameters are used (0.8186). This 0.0030 gap is due to
parameters, not data.

### 6.2 How much real progress each step actually represents

| Transition | Δ Accuracy | Δ PR-AUC | Nature of the step |
|---|---|---|---|
| NB02 → NB03 | +0.0131 | **+0.0156** | **Real** — parameter tuning makes the model rank better |
| NB03 → NB04 | +0.0533 | −0.0003 | **Operating point only** — calibration + threshold. PR-AUC doesn't budge |
| NB04 → NB05 | +0.0026 | +0.0011 | **Real but very small** — multiclass, p = 0.046 (`step7_final.json`) |
| NB05 → NB06 #12 | +0.0204 | +0.0117 | **Mostly the 11 leaky features being kept** |
| NB05 *(39f ablation)* → NB06 #12 | **+0.0098** | **+0.0017** | ⚠️ almost **nothing new** |

The last row is the most important one. Notebook 05 **already** ran the ablation keeping the leaky
features and got 0.8951 accuracy / 0.9527 PR-AUC. Notebook 06's "best" configuration
(0.9050 / 0.9544) is ahead by only **+0.0098 accuracy and +0.0017 PR-AUC** — and most of that gap
comes from notebook 06 **dropping the FPR ≤ 0.10 constraint** to freely push the threshold up to
0.859.

The consequence for catching attacks, on the same `test-final`:

| Version / configuration | Threshold | FPR | Total recall | **Recall Fuzzers** |
|---|---|---|---|---|
| NB05 RF-A @0.5 | 0.500 | 0.2569 | 0.9491 | **0.8237** |
| NB05 RF-A @FPR≤10% | 0.695 | 0.1050 | 0.8607 | 0.5496 |
| NB05 RF multiclass @FPR≤10% | 0.686 | 0.1059 | 0.8682 | 0.5676 |
| NB05 RF 39f @FPR≤10% | 0.731 | 0.1059 | 0.8968 | **0.6249** |
| **NB06 #12** | 0.859 | 0.0561 | 0.8376 | **0.4301** |

Notebook 06 buys an extra 0.0098 accuracy with **0.1948 Recall Fuzzers** compared to notebook 05's
closest configuration. Under any reasonable reading for an intrusion detection system, this is
**not an improvement**, but a different operating point — more conservative on false alarms, more
porous to attacks.

### 6.3 What notebook 06 actually contributes that is new

| Contribution | Existed before? |
|---|---|
| Full reproduction audit of NB01 against `data/cleaned`, value-by-value | ❌ **New** — no earlier notebook did this |
| Mechanism of deduplication removing 59% Attack vs 10–13% Normal | ❌ **New, valuable** |
| Proof that the 0.13 class-ratio shift **already exists in the raw data** | ❌ **New** — fixes a wrong sentence in an earlier report + slide |
| Checking whether `df_shrink` loses information | ❌ **New** |
| Checking One-Hot for unseen values, encoder leakage | ❌ **New** |
| A 2×2×2 factorial design separating three factors | ❌ **New design** — but the measurement has errors L1, L2 |
| EM prior (Saerens 2002) estimating π from unlabeled test data | ❌ **New** — a negative result, reported honestly, valuable |
| Distribution alignment by quantile | ❌ **New** — fails, reported honestly |
| Extra Trees, Logistic Regression, Soft Voting | ❌ **New** (HGB was already in NB05) |
| A "what should NOT be concluded" section | ✅ NB05 also has this, but NB06 writes it in more detail |

### 6.4 Where notebook 06 regresses relative to notebook 05

| Item | Notebook 05 | Notebook 06 | Comment |
|---|---|---|---|
| Model / threshold selection | on **test-dev**, under a **pre-declared** `FPR ≤ 0.10` constraint | `idxmax` accuracy on **test-final** | ❌ **serious regression** (error L3) |
| Statistical testing | bootstrap CI for **every** pre-declared candidate (`step7_final.json`) | CI only for the configuration that just won on test-final | ❌ winner's curse |
| Robustness to seed | yes (`step8_seeds.json`: spread 0.00024) | none | ❌ missing |
| Distribution-shift KS | on **cleaned** data, only the 28 features **in the model** | on **raw** data, 39 features including dropped columns | ❌ worse (error L6) |
| Fuzzers analysis | a dedicated experiment: probability quantiles, per-class KS, `service` composition | one recall table at the end | ❌ worse |
| The `attack_cat` multiclass approach | tried, and is a **statistically significant winner** (p = 0.046) | not tried | ❌ dropped |
| Operating constraint (FPR) | pre-declared, held constant throughout | none | ❌ missing |
| The deduplication question | `experiment_nodedup`: evaluation set held fixed, ΔPR-AUC = −0.0027 (p≈0) | changed the evaluation set too, +0.0294 accuracy | ❌ dirtier measurement, no cross-check (error L2) |
| Reproducible | yes (uses `data/cleaned`) | **no** — missing raw files (error L8) | ❌ |

---

## 7. OVERALL ASSESSMENT: WHAT NOTEBOOK 06 IMPROVES, WHAT IT DOESN'T

**Real improvements (keep):**

1. This is the **first** notebook to verify the entire 01→04 chain with real asserts instead of
   trusting earlier reports. The conclusion "no implementation bug" is now an evidence-backed
   conclusion.
2. Three findings about **data mechanics** (deduplication affecting classes unevenly; the
   class-ratio shift pre-existing in raw data; distribution shift concentrated in the Normal
   class) are new contributions and fix errors in earlier documents.
3. Two **negative results** (EM under-correcting; quantile alignment breaking PR-AUC) are reported
   in full. This is the project's strongest point of academic integrity.
4. The framing "the gap to the 97–98% papers is a gap in **evaluation protocol**" is correct and
   turns a weakness into an explainable result.

**Not improvements (do not use for reporting):**

5. The **0.9050** accuracy figure is not new capability. It is notebook 05's leaky-feature
   ablation (0.8951) plus a more aggressive threshold, selected on the reporting set.
6. The factor-magnitude figures **+0.0955 / +0.0112 / +0.0294** cannot be used as written, because
   the three comparison cells have different evaluation sets and class ratios.
7. The claim "**8.5x**" must be corrected to "**2.6–4.9x**."
8. The ratio "**85% / 15%**" must be corrected to "**77% operating point / 19% features / 3%
   algorithm**."
9. CI95 [+0.0812; +0.0914] cannot be used because the configuration was selected on the very set
   being tested.

---

## 8. WHAT NOTEBOOK 06 NEEDS TO BECOME A SCIENTIFICALLY SOUND NOTEBOOK

Fixes in priority order. Each is small; none requires rerunning from scratch.

| Priority | Task | Cell to fix | Cost |
|---|---|---|---|
| 1 | Change `best_name` to select by accuracy **on `test-dev`**, keep the bootstrap on `test-final` | cell 29, 1 line | 0 minutes (reuses existing probabilities) |
| 2 | Pre-declare an operating constraint (e.g. `FPR ≤ 0.10`) and use it as the threshold-selection rule, like NB04/NB05 | cell 24 (`thr_rule`) | ~5 minutes |
| 3 | Add `balanced_acc` and `roc_auc` columns to the **three-factor magnitude table**; note each cell's different `n_test` and `π_test` | cell 18, print 2 more tables | 0 minutes (the numbers already exist in `LAD`) |
| 4 | Compute `eff_dedup` as the average of **all 4** cell pairs, print the min–max range too | cell 18 | 0 minutes |
| 5 | Reference `reports/dedup_vs_nodedup/` where discussing the deduplication factor, and state which measurement is cleaner | markdown cell 21 | 0 minutes |
| 6 | Replace the "85/15" ratio with the three-component accuracy breakdown table (#0→#10, #0→#8, remainder) | markdown cell 33 | 0 minutes |
| 7 | Recompute KS on **cleaned** data, only on the model's features; update the most-shifted-feature list | cell 19 | ~2 minutes |
| 8 | Add a Recall-by-attack-type table **for the baseline too**, next to the best configuration | cell 31 | 0 minutes (only needs adding `p_base`) |
| 9 | Fix cell 28 to print both the 4-tree-family spread **and** the spread including Logistic, with a line explaining the split | cell 28 | 0 minutes |
| 10 | Restore `data/raw/CSV Files/Training and Testing Sets/` or switch Part 1 to read `data/cleaned` with a note | cells 1, 3 | needs file confirmation |
| 11 | Add a one-line-per-factor summary table right after cell 0; trim cell 33 down to 10 lines + a link to the report | cells 0, 33 | ~15 minutes to write |
| 12 | Merge `pool()` and `cleaned_with_contaminants()` into one data-building approach, or clearly note that Part 3 and Part 4 numbers are not directly comparable | cells 17, 23 | ~10 minutes |

---

## 9. DATA SOURCES USED FOR THIS REPORT

| File | Used for |
|---|---|
| `notebooks/06_Root_Cause_Audit.ipynb` | Re-reading all the code + saved output of the 34 cells |
| `reports/audit06/results_audit06.json` | Source of every recomputation (scale, KS, 13 configurations, 5 algorithms, bootstrap) |
| `models/random_forest_v2_metrics.json`, `..._v3_metrics.json` | Cross-check against NB03 / NB04 baseline |
| `notebooks/model_comparison_results.csv` | NB02 / NB03 / NB04 figures on the same `test-final` |
| `reports/exp05/step5_shift.json` | KS on cleaned data; CV; adversarial AUC |
| `reports/exp05/step6_fuzzers.json` | Baseline's Recall Fuzzers at threshold 0.5 and 0.711 |
| `reports/exp05/step7_final.json` | NB05's configuration, bootstrap CI, recall by category at the operating point |
| `reports/exp05/step8_seeds.json` | NB05's robustness to seed |
| `reports/dedup_vs_nodedup/Report_Deduplication_Impact_Detailed.md` | Clean deduplication measurement, used to cross-check error L2 |
| `reports/Report_Accuracy_Root_Cause_Detailed.md` | NB06's report, the one being audited |

**No file under `data/`, `models/`, `notebooks/`, or `reports/audit06/` was modified while
producing this report.** Every recomputation ran on a copy in a temporary directory.

### Formulas for the recomputed figures

- Factor magnitude, using cell 18's exact formula but different metrics:
  `split = AVG[ cell(dedup, f, random) − cell(dedup, f, official) ]` for f ∈ {31, 42};
  `feature = AVG[ cell(dedup, 42, c) − cell(dedup, 31, c) ]` for c ∈ {official, random};
  `remove dedup = AVG[ cell(no_dedup, f, c) − cell(dedup, f, c) ]` over all 4 pairs.
- Accuracy decomposition: `(#10 − #0)` = feature share; `(#8 − #0)` = algorithm share;
  `(#12 − #0) − (#10 − #0) − (#8 − #0)` = operating-point share.
- Mean KS by scope: filtering `3.3_ks` by whether a feature is in `CONTAM ∪ USELESS` or not
  (11 dropped features / 28 features in the model).
