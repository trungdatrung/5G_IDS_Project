# Root-Causing the Low Accuracy — Independent Audit of the Full Pipeline

**Project:** 5G IDS / UNSW-NB15, binary classification `label` (0 = Normal, 1 = Attack)
**Run date:** 2026-10-03
**Notebook:** `notebooks/06_Root_Cause_Audit.ipynb` (newly created, does not overwrite notebooks 01–05)
**Source data:** `reports/audit06/` — `confusion_matrix_2x2x2.csv`, `remediation_options.csv`,
`algorithm_comparison.csv`, `results_audit06.json`, `confusion_before_after.png`
**Environment:** Python 3.11.16 · scikit-learn 1.9.1 · pandas 3.0.6 · no XGBoost/LightGBM

**Discipline applied:** no existing dataset/notebook was modified or deleted; the new notebook
only writes to `reports/audit06/`. `test-final` is touched only at the final reporting step.
Every claim is accompanied by the number that produced it; no figure from an earlier report is
cited without re-measuring it.

---

## SUMMARY OF RESULTS

**The cause is NOT how the model was implemented.** Re-auditing every step 01→05 found no bugs.

**The cause is that UNSW-NB15's official train/test split is distribution-shifted**, plus a real
but easily fixed operational error: leaving the decision threshold at 0.5 while the model learns
probabilities calibrated to the train set's class ratio (49.64% Attack) and then gets scored on a
set with a completely different ratio (36.65%).

Measured with a 2×2×2 factorial design, the effect on Accuracy:

| Factor | Effect size |
|---|---|
| **Train/test split** (official → random) | **+0.0955** |
| Keeping the 11 dropped features | +0.0112 |
| Removing deduplication | +0.0294 *(with 10–48% test→train leakage)* |

The split matters **8.5 times** more than dropping leaky features.

After remediation: Accuracy **0.8186 → 0.9050**, FPR **0.2569 → 0.0561**, F1 **0.7932 → 0.8660**.
But this must be read correctly: ~85% of the improvement comes from **resetting the operating
point**, not from a stronger model.

---

## PART 1 — IMPLEMENTATION AUDIT: NO BUGS FOUND

Every step was redone from scratch, stating its role + expected outcome, then verified with
numbers.

| Step | Role | Verification | Result |
|---|---|---|---|
| Read raw data | Get the exact official split | size, NaN | train 175,341×45, test 82,332×45, 0 NaN — **PASS** |
| `df_shrink` | Reduce memory, keep content unchanged | duplicate row count before/after | identical — **PASS (conditionally)** |
| Drop columns | Remove leaky features + metadata | column list | drops 11 columns, 31 features remain — **PASS** |
| Drop duplicate / contradictory rows | Prevent leakage and memorization | assert | none remain — **PASS** |
| Cross-check against `data/cleaned` | The function must be a faithful copy | value-by-value comparison | **EXACT MATCH** 98,934×33 and 50,567×33 |
| One-Hot | Encode categoricals, no leakage | where the encoder is fit, unseen values | 183 columns; `state`=`ACC`/`CLO` → zero vector; fit **only** on train-fit — **PASS** |
| Split | Separate the selection set from the reporting set | sizes | 79,147 / 19,787 / 25,283 / 25,284 — **PASS** |
| Reproduce the baseline | Is the old figure correct | Accuracy test-final | **0.8186** — matches the earlier report |

**Honest note on `df_shrink`:** it downcasts `float64` → `float32`, so it is **not** bit-preserving
— largest absolute error 6.2×10⁻², relative error ~10⁻⁷. The duplicate row count measured is
identical before and after, so the deduplication step is unaffected. This is a potential risk that
was checked, not a bug.

### Is the model underfitting or overfitting?

| Split | PR-AUC | Accuracy @0.5 |
|---|---|---|
| train-fit (memorized) | 0.9985 | 0.9775 |
| CV 5-fold within train-fit | 0.9830 (±0.0015) | — |
| validation (same distribution as train) | 0.9849 | 0.9322 |
| test-dev (test distribution) | 0.9429 | 0.8154 |
| test-final (test distribution) | 0.9414 | 0.8186 |

- **No underfitting.** Within the train distribution, Random Forest reaches PR-AUC ~0.98 and
  Accuracy ~0.93. Model capacity is more than sufficient.
- **Not memorization-style overfitting either.** train-fit 0.9775 vs. validation 0.9322 — a normal
  gap for a random forest.
- **The entire drop happens exactly at the train → test boundary:** Accuracy −11.4 points, PR-AUC
  −0.0416, i.e. **28 times** the standard deviation across CV folds.

---

## PART 2 — THE CAUSE, MEASURED WITH A 2×2×2 DESIGN

Three suspected factors, separated with a full factorial design. Same algorithm, same
parameters, same seed in all 8 cells. For a fair comparison, both split methods use **the same
row set**: train+test are pooled, deduplicated globally, then assigned to train/test either by
origin or randomly.

### Accuracy @0.5

| | official split | random split |
|---|---|---|
| deduplicated, 31 features | **0.8145** | 0.9102 |
| deduplicated, 42 features | 0.8259 | 0.9211 |
| not deduplicated, 31 features | 0.8633 | 0.9400 |
| not deduplicated, 42 features | 0.8711 | **0.9505** |

### PR-AUC

| | official split | random split |
|---|---|---|
| deduplicated, 31 features | 0.9259 | 0.9693 |
| deduplicated, 42 features | 0.9466 | 0.9778 |
| not deduplicated, 31 features | 0.9840 | 0.9941 |
| not deduplicated, 42 features | 0.9859 | **0.9958** |

### FPR

| | official split | random split |
|---|---|---|
| deduplicated, 31 features | 0.2476 | 0.0717 |
| deduplicated, 42 features | 0.2562 | 0.0663 |

Notice the FPR column: with the official split, FPR sits around 0.25 regardless of features or
deduplication. With a random split, it drops to 0.06–0.07. This is the fingerprint of distribution
shift, not of a weak model.

### Breaking down the gap caused by the split

Within the +0.0955 of the "split" factor, **about half is a class-ratio shift**:

| | Accuracy | FPR | Precision | Recall |
|---|---|---|---|---|
| Baseline @0.5 | 0.8186 | 0.2569 | 0.6813 | 0.9491 |
| **Only the class ratio corrected**, still @0.5 | **0.8673** | **0.1470** | 0.7784 | 0.8921 |

No change to the model, no change to the threshold — just correcting probabilities for the test
domain's class ratio: **+4.87 points of Accuracy**, FPR nearly halved.

The other half is a genuine feature distribution shift:

- Mean KS over 39 numeric features: overall 0.0530 · **Normal class only 0.1097** · Attack only
  0.0385. The shift is concentrated in the Normal class, **2.8 times** that of Attack.
- The 6 most-shifted features (KS, Normal only): `sttl` 0.2763 · `ct_state_ttl` 0.2559 ·
  `ackdat` 0.2383 · `dload` 0.2348 · `dttl` 0.2055 · `tcprtt` 0.2023.
- `attack_cat` composition: the Normal share changes from 0.3194 (train) to 0.4494 (test),
  **+0.13** — exactly matching the class-ratio shift. The attack categories keep roughly the same
  relative proportions among themselves.

In other words: the official split samples Normal and Attack at different rates, **and** the
Normal rows in the test set have a markedly different feature distribution (median `ackdat`
0.0000 → 0.0001; `dload` 1,447 → 2,113; `sjit` 0.00 → 17.62).

### The mechanism of the deduplication step (new finding)

| Split | % of Normal rows removed | % of Attack rows removed | Ratio |
|---|---|---|---|
| training | 10.5% (5,862/56,000) | **58.6%** (69,913/119,341) | 5.6x |
| testing | 13.1% (4,846/37,000) | **58.8%** (26,677/45,332) | 4.5x |

Attack flows (especially Generic) repeat almost identically, so they get collapsed heavily. This
is why the Attack ratio drops from 0.6806 → 0.4964 (train) and 0.5506 → 0.3665 (test).

**Re-confirming a point that must be corrected in the earlier report and slide:** the cleaning
step does **not** create the class-ratio shift. The 0.1300 shift already exists in the raw data;
after cleaning it is 0.1299. The drop in train (0.1842) and in test (0.1841) differ by only 0.0001.

---

## PART 3 — IS THE ALGORITHM A LEVER? NO

Five algorithm families, same 31 features, same split, same seed, one reasonable configuration
per family.

| Algorithm | PR-AUC validation | PR-AUC test-final | Acc @0.5 | Acc @chosen threshold | F1 |
|---|---|---|---|---|---|
| Random Forest | 0.9849 | 0.9414 | 0.8186 | 0.8925 | 0.8448 |
| HistGradientBoosting | 0.9833 | **0.9423** | 0.8215 | 0.8930 | 0.8433 |
| Soft Voting (RF+ET+HGB) | 0.9847 | 0.9419 | 0.8038 | **0.8950** | **0.8462** |
| Extra Trees | 0.9812 | 0.9285 | 0.7694 | 0.8798 | 0.8250 |
| Logistic Regression | 0.9238 | 0.7281 | 0.7270 | 0.7298 | 0.6091 |

- The four tree-based families sit within **0.0138** PR-AUC of each other on test-final, while the
  drop from validation to test-final is **0.0752** — **5 times** larger. Switching algorithms is
  not a lever.
- HistGradientBoosting (comparable to LightGBM) beats Random Forest by exactly **+0.0009** PR-AUC.
  Not meaningful.
- The Soft Voting ensemble gives the highest Accuracy at the operating point (0.8950), but PR-AUC
  stays in the same range — it doesn't break the ceiling, just ranks slightly more smoothly.
- **Logistic Regression collapses outright** (0.9238 → 0.7281). The hypothesis "a simpler model
  handles distribution shift better" **does not hold** for this problem.

XGBoost/LightGBM/CatBoost were not available in the environment. Scikit-learn's
HistGradientBoosting is in the same algorithm family (histogram-based boosting) and already
performed on par with Random Forest, so the odds that a different boosting library would produce
a breakthrough are low — but this is an inference, not a measurement.

---

## PART 4 — REMEDIATION APPROACHES

Every configuration: fit on `train-fit`, select the threshold on `validation` or `test-dev`,
report only on `test-final`.

| # | Configuration | Threshold | Accuracy | F1 | FPR | PR-AUC | Needs test labels? |
|---|---|---|---|---|---|---|---|
| 0 | RF 31f @0.5 (baseline) | 0.500 | 0.8186 | 0.7932 | 0.2569 | 0.9414 | — |
| 1 | + threshold chosen on validation | 0.535 | 0.8335 | 0.8046 | 0.2254 | 0.9414 | **No** |
| 2 | + prior corrected by EM | 0.500 | 0.8310 | 0.8026 | 0.2309 | 0.9414 | **No** |
| 3 | + prior correction + threshold on test-dev | 0.794 | 0.8925 | 0.8447 | 0.0528 | 0.9414 | Yes |
| 4 | + distribution alignment (quantile) | 0.500 | 0.7314 | 0.6984 | 0.3363 | **0.7736** | No |
| 5 | + alignment + prior correction | 0.775 | 0.7617 | 0.6600 | 0.1628 | 0.7736 | Yes |
| 6 | RF 24f (drop the most-shifted feature group) | 0.500 | 0.8200 | 0.7948 | 0.2557 | 0.9393 | No |
| 7 | RF 24f + prior correction | 0.780 | 0.8903 | 0.8432 | 0.0600 | 0.9393 | Yes |
| 8 | HGB 31f @0.5 | 0.500 | 0.8215 | 0.7959 | 0.2527 | 0.9423 | No |
| 9 | HGB 31f + prior correction | 0.841 | 0.8930 | 0.8433 | 0.0451 | 0.9423 | Yes |
| 10 | RF 42f (keep the leaky features) @0.5 | 0.500 | 0.8353 | 0.8124 | 0.2442 | 0.9530 | No |
| 11 | RF 42f + prior correction | 0.817 | 0.9048 | 0.8667 | 0.0603 | 0.9530 | Yes |
| **12** | **HGB 42f + prior correction** | 0.859 | **0.9050** | 0.8660 | 0.0561 | **0.9544** | Yes |

### Two approaches that DID NOT work — reported in full

- **Distribution alignment by quantile (#4, #5): FAILS BADLY.** PR-AUC drops 0.9414 → 0.7736.
  Reason: a row's quantile depends on the composition of the set it belongs to; when two sets have
  different class ratios, this alignment destroys the discriminative information. A reasonable
  idea on paper, wrong in this case.
- **Dropping the most-shifted feature group (#6, #7): NO CHANGE.** 0.8186 → 0.8200. Those
  features are simultaneously the most shifted and the most useful; dropping them gains nothing.

### Honest limitations of the "prior correction" approach

The EM algorithm (Saerens–Latinne–Decaestecker 2002) estimates the test domain's Attack ratio from
**unlabeled** data. Results:

| Configuration | π train | π test, EM estimate | π test, true |
|---|---|---|---|
| RF 31f | 0.4964 | **0.4684** | **0.3665** |
| HGB 31f | 0.4964 | 0.4709 | 0.3665 |
| RF 42f | 0.4964 | 0.4778 | 0.3665 |

**EM under-corrects significantly.** It assumes *only* a class-ratio shift (P(x|y) unchanged);
here there is also a feature distribution shift, so the assumption is violated. Consequences:

- The **entirely label-free** option only recovers **+1.2 to +1.5 points** of Accuracy.
- To recover the full **+7 points**, a **labeled** sample from the deployment distribution (here,
  `test-dev`) is needed to set the threshold — exactly what notebook 04 did in its third run.

This is an important finding that runs against the initial expectation: the shift is **not** a
pure prior shift.

### Statistical test — configuration 12 vs. baseline

Paired bootstrap, 1,000 iterations, on test-final:

| | Mean | 95% CI | p |
|---|---|---|---|
| Δ Accuracy | **+0.0863** | [+0.0812 ; +0.0914] | ≈ 0 |
| Δ PR-AUC | **+0.0130** | [+0.0109 ; +0.0150] | ≈ 0 |

**This must be read correctly:** ΔAccuracy is +0.086 but ΔPR-AUC is only +0.013. This means about
**85% of the improvement comes from resetting the operating point**, only ~15% from the model
actually ranking better — and that 15% comes from the 11 kept features, not from switching
algorithms.

### Confusion matrix (test-final, 25,284 rows)

| | TN | FP | FN | TP |
|---|---|---|---|---|
| Baseline RF 31f @0.5 | 11,903 | 4,114 | 472 | 8,795 |
| Configuration 12 (HGB 42f + prior correction) | 15,119 | 898 | 1,505 | 7,762 |

False alarms drop from 4,114 to 898 (−78%), while missed attacks rise from 472 to 1,505.
Figure: `reports/audit06/confusion_before_after.png`.

### Recall by attack type at configuration 12

Worms 1.000 · Reconnaissance 0.986 · Generic 0.976 · Backdoor 0.970 · DoS 0.969 ·
Exploits 0.962 · Shellcode 0.924 · Analysis 0.911 · **Fuzzers 0.430**

Fuzzers remains the only weakness, and no configuration in this round addresses it.

---

## PART 5 — WHY DO THE PUBLISHED PAPERS REACH 97–98%?

Reading directly from the PR-AUC table in Part 2: simply **skipping deduplication** raises PR-AUC
to 0.984–0.996 and Accuracy to 0.863–0.951 — while 10–48% of test rows at that point are **exact
duplicates** of a train row. Adding a random split instead of the official one raises it further
to 0.9505 Accuracy / 0.9958 PR-AUC.

The gap between the team's numbers and the published figures is mainly a gap in **evaluation
protocol**, not in model capability. The team is running a stricter protocol and paying for it
with lower numbers.

---

## PART 6 — RECOMMENDATIONS

1. **Keep the official split and keep the deduplication step.** Both are methodologically
   correct. But when reporting numbers, state clearly that this is a distribution-shifted
   benchmark, with the 2×2×2 table from Part 2 as evidence — it turns "the number is low" from a
   weakness into an explainable result.
2. **Fix the 0.5-threshold operational bug.** This is the cheapest and most real fix. At minimum:
   select the threshold on validation (+1.5 points, no test labels needed). If using a labeled
   `test-dev` as a sample from the deployment distribution is acceptable: +7.4 points and FPR
   0.2569 → 0.0528.
3. **Don't switch algorithms looking for a breakthrough.** Evidence in Part 3: the spread among
   tree-based algorithm families is 5 times smaller than the drop caused by distribution shift.
4. **On the 11 dropped features:** they are worth +0.0112 Accuracy by the 2×2×2 scale (averaged
   over both splits), and +0.0167 Accuracy / +0.0116 PR-AUC when comparing configuration #0
   directly against #10. If the team wants to keep D'hooge et al.'s argument, keep dropping them
   and accept that cost — it's small, and is now measured rather than estimated. Additional note:
   `sttl` and `ct_state_ttl` are also the two **most distribution-shifted** features (KS, Normal
   only, 0.2763 and 0.2559), so keeping them also carries risk.
5. **Report Balanced Accuracy and PR-AUC alongside Accuracy.** On an imbalanced,
   distribution-shifted set, Accuracy alone is misleading — it is the very reason the question
   "why is accuracy low" comes up.
6. **Fix 2 spots in the earlier documents** (re-confirmed with numbers in Part 2): the sentence
   "the cleaning step itself creates a 13-point class-ratio shift" in
   `reports/Report_Comparison_3_Runs.txt` item 3.2 and
   `reports/Presentation_Slide_Content_Detailed.md` slide 2.

---

## PART 7 — WHAT CANNOT BE CONCLUDED FROM THIS ROUND

- **Cannot** conclude that the official split is "wrong." It is a hard, distribution-shifted
  benchmark; using it is a deliberately strict choice and should be kept.
- **Cannot** conclude that no algorithm can beat this ceiling. Only 5 families were tried, one
  reasonable configuration each, no wide hyperparameter search, and no XGBoost/LightGBM/CatBoost
  available in the environment.
- **Cannot** conclude that every domain-adaptation method is useless. Only two approaches were
  tried (quantile alignment, EM prior correction). Not yet tried: CORAL, domain-adversarial
  training, self-training on unlabeled test data.
- **Cannot** conclude that configuration 12 is the one that should be deployed. It uses 11
  features the team deliberately excluded under a methodological argument, and its threshold was
  chosen on a labeled `test-dev`.
- This notebook's figures use 300 trees and seed 42; robustness across multiple seeds has not been
  checked the way `reports/Report_Model_Improvement.txt` did for the multiclass experiment.

---

## DATA SOURCES

| File | Contents |
|---|---|
| `notebooks/06_Root_Cause_Audit.ipynb` | All code, run sequentially, with output |
| `reports/audit06/confusion_matrix_2x2x2.csv` | The 8 cells of the factorial design |
| `reports/audit06/remediation_options.csv` | The 13 remediation configurations |
| `reports/audit06/algorithm_comparison.csv` | The 5 algorithms |
| `reports/audit06/results_audit06.json` | Every measurement from the notebook |
| `reports/audit06/confusion_before_after.png` | Confusion matrix before/after |

`data/`, `models/`, and `notebooks/01..05` **were not modified**.
