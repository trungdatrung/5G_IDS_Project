# PRESENTATION SLIDE CONTENT (10-slide version)
## 5G IDS Project — Intrusion Detection on UNSW-NB15


## SLIDE 1 — Title

**[SLIDE]**

# Comparing 3 Intrusion Detection Models on UNSW-NB15
### When "Accuracy went up" doesn't mean "the model got better"


## SLIDE 2 — Data and the cleaning step

**[SLIDE]**

### The problem
Binary classification of network flows: `label` = 0 (Normal) / 1 (Attack)

### Data after cleaning — **31 features → 183 columns** after One-Hot

| | Row count | Attack ratio |
|---|---|---|
| Train | 98,934 | 49.64% |
| Test | 50,567 | **36.65%** |

### 13 columns dropped
- `id` + **8 leaky features** (`sttl`, `dttl`, `ct_state_ttl`…) — D'hooge et al., PST 2022
- 3 features with no discriminative power
- `attack_cat` is **not** used as a feature

### Consequence: the Attack ratio changes differently in the two splits

| | Before cleaning | After cleaning |
|---|---|---|
| Train | 68.06% | 49.64% |
| Test | 55.06% | 36.65% |

> ⚠️ The cleaning step itself creates a **13-point class-ratio shift**

**[SPEAKER NOTES]**

Two points to make:

1. Many papers reach 97–98% on this dataset because they **keep** `sttl`, `ct_state_ttl` —
   features that leak from how the data was generated, not from the nature of the attack.
   Our team drops them, accepting a lower but honest number.
2. This 13-point shift will come back in Slide 8 as a main cause.

*If asked "prove the leaky features claim":* be honest — the team followed the paper's
argument, **has not run a controlled experiment**. That's a gap worth filling in.

---

## SLIDE 3 — Three models and the comparison conditions

**[SLIDE]**

### All 3 are Random Forest — **same features, same preprocessing**

| | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| Number of trees | 100 | 300 | 300 |
| `max_depth` | **None** | 20 | 20 |
| `max_features` | `'sqrt'` (~13) | 0.5 (~91) | 0.5 (~91) |
| Calibration | — | — | isotonic |
| **Threshold** | **0.500** | **0.515** | **0.711** |
| `random_state` | 42 | 42 | 42 |

> Any difference in results can **only** come from: forest parameters, calibration, or the threshold

### Shared evaluation set: `test-final`
- **25,284 rows** (16,017 Normal / 9,267 Attack)
- The **only** set no model used for training / parameter selection / threshold selection
- Unified rule: `Attack if P(Attack) ≥ threshold`

**[SPEAKER NOTES]**

Emphasize the callout line: because features and preprocessing are identical, every other
cause is ruled out — this is a clean experimental design.

On the evaluation set: notebooks 02–03 report on the full test set, notebook 04 splits it in
half and uses the first half to choose the threshold. So our team standardized on evaluating
all 3 on the remaining half.

---

## SLIDE 4 — Results of the 3 runs

**[SLIDE]**

### On `test-final` (25,284 rows), same decision rule

| | Accuracy | Precision | Recall | F1 | FPR |
|---|---|---|---|---|---|
| **Run 1** | 0.8156 | 0.6773 | 0.9491 | 0.7905 | 26.2% |
| **Run 2** | 0.8287 | 0.6965 | 0.9438 | 0.8015 | 23.8% |
| **Run 3** | 0.8820 | 0.8251 | 0.8605 | 0.8424 | 10.6% |

### Confusion matrix

| | TN | FP | FN | TP |
|---|---|---|---|---|
| Run 1 | 11,827 | 4,190 | 472 | 8,795 |
| Run 2 | 12,206 | 3,811 | 521 | 8,746 |
| Run 3 | 14,327 | 1,690 | **1,293** | 7,974 |

Accuracy **+6.6 points** · Precision **+14.8 points** · but Recall **−8.9 points**

> ❓ Where does this gain come from? Did the model get better, or did the decision rule just change?

**[SPEAKER NOTES]**

**Don't draw any conclusion on this slide.** Just raise the question in the last line and move
on — this is the cliffhanger leading into the next three analysis slides.

Insert the figure `reports/confusion_matrices.png` if there's room.

---

## SLIDE 5 — Looking again through the lens of error structure

**[SLIDE]**

| | Total errors | FP share | Alerts fired | Real attacks |
|---|---|---|---|---|
| Run 1 | 4,662 | **89.9%** | 12,985 | 9,267 |
| Run 2 | 4,332 | **88.0%** | 12,557 | 9,267 |
| Run 3 | 2,983 | **56.7%** | 9,664 | 9,267 |

### How to read this
- Run 1 fires **12,985** alerts for **9,267** real attacks → **40% excess**
- In runs 1–2, nearly **90%** of errors are **false alarms**
- The Normal class is **63.35%** of the test set → cutting FPR by 1 point pulls Accuracy up by
  ~0.63 points

> 💡 **Accuracy went up not because the model got smarter, but because it cut the error type that
> dominates**

### The price paid

| Step | FP reduced | FN added | Ratio |
|---|---|---|---|
| Run 1 → 2 | −379 | +49 | **1 : 7.7** |
| Run 2 → 3 | −2,121 | +772 | **1 : 2.7** |

**[SPEAKER NOTES]**

The clearest and most persuasive slide — spend time on it.

> "If you only look at Accuracy, you'd think the model improved steadily. But break it down and
> nearly 90% of run 1 and 2's errors are false alarms. And since Normal dominates the test set,
> just cutting false alarms makes Accuracy go up on its own — no better model needed."

Business meaning: **FN = an intrusion that goes undetected. FP = an analyst's wasted time.**
The two error types have very different costs; Accuracy lumps them together.

---

## SLIDE 6 — Run 1 → Run 2: a REAL but small improvement

**[SLIDE]**

### What changed
`max_depth`: None → **20** · `max_features`: `'sqrt'` → **0.5** · 100 → **300 trees**

### Evidence of real improvement — metrics that do NOT depend on the threshold

| | Run 1 | Run 2 |
|---|---|---|
| ROC-AUC | 0.9548 | 0.9600 |
| **PR-AUC** | 0.9264 | **0.9420** (+1.56 points) |

### Overfitting has decreased

| | Accuracy on the fit data | Validation | Gap |
|---|---|---|---|
| Run 1 config | **1.0000** | 0.9268 | 7.3 points |
| Run 2 config | 0.9775 | 0.9322 | **4.5 points** |

### But why only +1.3 points of Accuracy?
- The 10 best configurations have CV PR-AUC **0.9822–0.9829**, std ~0.0015 → **within noise**
- The validation → test gap is still ~**10 points**

**[SPEAKER NOTES]**

Explain the **1.0000** figure: with `max_depth=None` and `min_samples_leaf=1`, trees grow until
every leaf is pure for one class, even leaves with just 1 sample. The model memorizes the entire
train set — FP = 0, FN = 0. Setting `max_depth=20` prevents this.

Closing line: *"Parameter tuning fixes **overfitting**, but doesn't fix **distribution shift**.
That's the ceiling of this step."*

---

## SLIDE 7 — Run 2 → Run 3: the twist

**[SLIDE]**

### What changed
Forest parameters **unchanged** · added isotonic calibration · threshold 0.515 → **0.711**

### ⚠️ Threshold-independent metrics do NOT change

| | Run 2 | Run 3 |
|---|---|---|
| ROC-AUC | 0.9600 | **0.9595** |
| PR-AUC | 0.9420 | **0.9416** |

### Isolating the evidence — same `test-final` set

| | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| Run 2 @0.515 | 0.8287 | 0.6965 | 0.9438 | **0.8015** |
| Run 3 calibrated **@0.5** | 0.8289 | 0.6976 | 0.9413 | **0.8013** |
| Run 3 calibrated **@0.711** | 0.8820 | 0.8251 | 0.8605 | 0.8424 |

> ✅ At **the same operating point**, calibration changes nothing (0.8013 vs 0.8015)
> ✅ The entire gain comes from **moving the threshold**, not a better model

**[SPEAKER NOTES]** — The most important slide of the talk.

The mathematical reason:

> "ROC-AUC depends only on **ranking order**, not on the probability values. Isotonic
> calibration is a **non-decreasing monotonic** function, and a monotonic transform **preserves
> order**. So, in principle, calibration **cannot** change ROC-AUC. The measured numbers match
> the theory exactly."

Why moving the threshold works: FPs sit close to the boundary (median `P(Attack)` = 0.648) while
TPs sit far from it (median 0.992). 63% of FPs fall within [0.50; 0.70). So cutting at 0.711
removes 55.7% of FPs while losing only 8.8% of TPs.

Additional note: Brier score on test goes from 0.10673 to 0.10688 — calibration got **slightly
worse**, if anything.

---

## SLIDE 8 — Root cause: the problem is in the DATA

**[SLIDE]**

### The "slow TCP handshake" region (`tcprtt > 0.01 s`)

| | % of Normal that is slow | Attack:Normal ratio |
|---|---|---|
| **Train** | 19.0% | **4.01 : 1** |
| **Test** | 41.5% | **1.04 : 1** |

- Train: `P(Attack \| slow)` = **0.80** → the model learns this rule very confidently
- Test: `P(Attack \| slow)` = **0.51** → the rule **loses all its value**

### Precision breakdown — `Precision = TPR·π / (TPR·π + FPR·(1−π))`

| | TPR | FPR | π | Precision |
|---|---|---|---|---|
| Validation | 0.9577 | 0.0929 | 0.4964 | **0.9104** |
| Test | 0.9504 | **0.2627** | 0.3665 | **0.6767** |

Precision drops by **0.2337**, of which:
- From the **class-ratio** change: **0.0540** (~23%)
- From **FPR rising** nearly 3-fold: **0.1294** (~55%)

> Recall barely changes (0.9577 → 0.9504) — **the entire problem is in the FPR**

### Independent evidence
**Adversarial validation AUC = 0.8040** — using only the features, it's possible to predict
whether a row belongs to train or test (0.5 = indistinguishable)

**[SPEAKER NOTES]** — The most valuable finding of the talk.

> "The model isn't wrong. It correctly learned a rule that is **real** in the train set: a slow
> handshake makes an attack 4 times more likely. But in the test set, that ratio is only 1.04 —
> almost useless. This isn't an algorithm bug, it's a property of the data. No Random Forest
> parameter can fix it."

Instead of a generic "the data is shifted," our team **separated the causes**: 23% from the
class ratio, 55% from the model genuinely producing more false alarms.

*Terminology, if asked:* this is **concept shift** (the label–feature relationship changes),
not **covariate shift** (only the feature distribution changes).

---

## SLIDE 9 — Weaknesses the team found on its own, and what failed

**[SLIDE]**

### ⚠️ Run 3's threshold was chosen using `test-dev` — **labeled test data**
Runs 1 and 2 **did not** have access to this information

A pre-planned control test — same model, threshold chosen on train's validation set:

| Threshold selection method | Threshold | F1 on `test-final` |
|---|---|---|
| On validation (train distribution) | 0.4636 | **0.7884** |
| On `test-dev` (test distribution) | 0.7106 | 0.8424 |
| *Run 2, for comparison* | 0.5152 | *0.8015* |

> **0.7884 is even lower than run 2** → most of run 3's "improvement" is an **information
> advantage**, not a model advantage

### 3 distribution-shift remedies tried — all WORSE

| | F1 |
|---|---|
| Run 2's main configuration | **0.8005** |
| Threshold chosen on a "test-like validation" | 0.7734 |
| + Importance weighting | 0.7723 |
| Adding 4 ratio features | 0.7968 |

**Why they failed:** these techniques assume **covariate shift**, but the data has
**concept shift** → reweighting the train sample cannot fix it

**[SPEAKER NOTES]**

Proactively disclose the weakness. A sharp reviewer will find it anyway; raising it first turns
it into a point in your favor.

Why the two thresholds are so far apart (0.46 vs. 0.71) for the **same** FPR ≤ 0.10 constraint:
the same probability level carries a different meaning in the two distributions — test's Normal
traffic sits deeper in the region the model considers suspicious.

"Failure" slides are often skipped, but reviewers tend to rate them very highly.

---

## SLIDE 10 — Conclusion and future directions

**[SLIDE]**

### 1. Run 1 → Run 2: the model REALLY got better, but only a little
PR-AUC **+1.56 points** · overfitting drops from 7.3 → 4.5 points · thanks to `max_depth=20`

### 2. Run 2 → Run 3: the model did NOT get better
ROC-AUC 0.9600 vs. 0.9595 — equal within noise.
What changed was the **operating point**, not model quality

### 3. The bottleneck is in the DATA
The rule "slow handshake ⇒ Attack": **4.01:1** (train) → **1.04:1** (test)

### 4. There is no single "best" ranking

| | Recall | True alerts : false alerts |
|---|---|---|
| Runs 1–2 | 0.94 | ~2 : 1 |
| Run 3 | 0.86 | ~5 : 1 |

> **FN** = an intrusion that goes undetected · **FP** = an analyst's time
> → Choosing a point is an **operational** decision, not a technical conclusion

### Next steps
A controlled experiment on leaky features · comparing other algorithms · handling concept
shift · analyzing the **Fuzzers** group (Recall 0.816 — ~81% of total FN)

**[SPEAKER NOTES]**

Close with the exact opening question, to form a closed loop:

> "Back to the opening question: does Accuracy rising from 0.82 to 0.88 mean the model got
> better? The answer: a small part, yes; mostly, no. And our team **measured precisely** which
> part is which."

Accompanying materials: `notebooks/model_comparison_results.csv` ·
`reports/confusion_matrices.png` · `reports/Report_Comparison_3_Runs.txt`

---
---

# BACKUP SLIDES (open only if asked)

## BK-1 — Recall by attack category

| Category | n | Recall run 1 | Recall run 2 |
|---|---|---|---|
| Exploits | 7,559 | 0.9836 | 0.9821 |
| **Fuzzers** | 4,436 | **0.8158** | **0.8102** |
| Reconnaissance | 2,262 | 0.9929 | 0.9929 |
| DoS | 1,677 | 0.9893 | 0.9863 |
| Generic | 1,430 | 0.9930 | 0.9937 |
| Analysis / Backdoor / Worms | 427 / 328 / 44 | 1.0000 | ~1.0000 |
| Shellcode | 370 | 0.9514 | 0.9459 |

> Fuzzers is the only weakness — ~81% of total FN. Reason: it sends random/malformed data to
> probe for bugs, so its network flow looks the most like normal traffic.

## BK-2 — Threshold sweep table (run 3's model, on `test-dev`)

| Threshold | Precision | Recall | F1 | FPR |
|---|---|---|---|---|
| 0.50 | 0.6954 | 0.9417 | 0.8000 | 0.2387 |
| 0.60 | 0.7677 | 0.9005 | 0.8288 | 0.1576 |
| **0.7106** | **0.8328** | **0.8594** | **0.8459** | **0.0998** ← chosen |
| 0.80 | 0.8790 | 0.8256 | 0.8515 | 0.0657 |
| 0.90 | 0.9442 | 0.7485 | 0.8351 | 0.0256 |

> The highest F1 is actually at threshold 0.80 (0.8515), **not** 0.7106. Run 3 optimizes
> **Recall subject to FPR ≤ 0.10**, not F1.

## BK-3 — Why not use SMOTE / data balancing

- Train is already nearly balanced: **49.64%** Attack
- `class_weight='balanced'` **was already** in the search space — CV chose `None`
- The problem isn't class imbalance, it's **distribution shift between train and test**

## BK-4 — Preventing data leakage & ensuring reproducibility

- The encoder lives **inside** the `Pipeline` → only `fit` on train, test only gets `transform`
- Every notebook has an `assert` checking that `attack_cat` and the 13 dropped columns are absent
- One-Hot replaces Label Encoding, avoiding a fake ordering (`tcp=113 > udp=112` is meaningless)
- `handle_unknown='ignore'` handles `state` = `ACC`, `CLO`, which only appear in test
- `random_state=42` across all 3 models · rerunning notebook 01 produces an **identical**
  parquet file
- 5 notebooks run fully, zero cell errors: 9/9 · 8/8 · 15/15 · 18/18 · 10/10
