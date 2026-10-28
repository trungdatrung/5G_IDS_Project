# Cross-Validation Strategy Comparison: UNSW-NB15 ↔ 5G-NIDD

**Date:** October 27, 2026 · **Module:** `experiment_5gnidd/`  
**Model Architecture:** Random Forest matching NB07 (300 estimators, max_depth 20, max_features 0.5, max_samples 0.7, random seed 42), OneHot encoding for `proto`, `service`, `state`.  
**Operating Threshold Protocol:** Calibrated strictly on the source domain development/validation split under $\text{FPR} \le 0.10$ without peeking at target labels.

---

## 0. Executive Summary

| Dimension | Quantitative Summary |
|---|---|
| **Data Integrity** | Evaluated on Fairdata release of 5G-NIDD (CC BY 4.0, SHA-256 verified). 1,215,890 raw flows $\rightarrow$ **379,556 clean flows** after removing 281,529 false Benign duplicates, 554,789 exact intra-station duplicates, and 16 contradictory records. |
| **Feature Mapping** | 31 features harmonized with UNSW naming and physical units. Baseline model reproduction matches NB07: UNSW `test-final` Accuracy = 0.81862. |
| **Zero-Shot Transfer (UNSW $\rightarrow$ 5G)** | **Infeasible.** ROC-AUC ranges between 0.21 and 0.40 across all feature subsets and label alignment schemes. Reverse transfer (5G $\rightarrow$ UNSW) yields ROC-AUC 0.45–0.55. |
| **Most Feasible Strategy** | **Protocol P3 (Merged Co-Training):** Train jointly on UNSW + 5G Base Station 1 (BS1); test on Base Station 2 (BS2, held strictly separate) and UNSW `test-final`, utilizing the decontaminated **LOI18** schema. Outcome: **BS2 ROC-AUC 0.998**, **UNSW test-final 0.955** (vs. 0.957 baseline). A single model serves both domains without catastrophic forgetting. |
| **Key Scientific Caveats** | (1) BS2 evaluation is somewhat optimistic because BS1 and BS2 share identical attack scripts and victim servers. (2) Legacy UNSW data does not boost 5G detection: P3 performance matches P5 (pure 5G). Few-shot co-training with scarce labels induces negative transfer. |

---

## 1. Comparative Dimensions

### Feature Schemas
- **F31:** Standard 31 harmonized features (benchmark baseline).
- **LOI12:** 12 physical features (`dur`, `proto`, `state`, `spkts`, `dpkts`, `sbytes`, `dbytes`, `rate`, `sload`, `dload`, `smean`, `dmean`) verified 99.6–100% consistent across both datasets.
- **LOI18:** LOI12 + 6 decontaminated approximated features (`sinpkt`, `dinpkt`, `sjit`, `djit`, `sloss`, `dloss`).

*Excised Contaminants & Shortcuts:*
- Handshake latencies (`ackdat`, `synack`, `tcprtt`): Encode cellular radio latency rather than attack signatures.
- Sliding window counters (`ct_src_ltm`, `ct_src_dport_ltm`): Reconstructed from record order; in E1, these accounted for 58% of feature importance, acting as an ordering shortcut rather than learning generalizable patterns.

### Label Alignment
- **ALL:** Retains all UNSW attack categories.
- **DR (DoS & Reconnaissance):** Filters UNSW to Normal, DoS, and Reconnaissance to match 5G-NIDD categories.

### Evaluation Protocols
- **P1:** Zero-shot transfer from UNSW to 5G.
- **P2:** Reverse transfer from 5G BS1 to UNSW `test-final`.
- **P3:** Joint co-training on UNSW + 5G BS1.
- **P4:** Few-shot curve with $k\%$ of BS1 labels.
- **P5:** In-domain ceiling (Train on BS1, Test on BS2).

---

## 2. Experimental Results Summary

Operating threshold chosen on source validation under $\text{FPR} \le 0.10$:

| Protocol | Feature Schema | Alignment | ROC-AUC $\rightarrow$ 5G BS2 (Bal Acc / FPR) | ROC-AUC $\rightarrow$ UNSW test-final (Bal Acc / FPR) |
|---|---|---|---|---|
| **P1 Zero-Shot** | F31 | ALL | 0.3537 (0.3325 / 0.4575) | 0.9594 (0.8779 / 0.1050) [Benchmark] |
| **P1 Zero-Shot** | LOI12 | ALL | 0.2772 (0.3565 / 0.4669) | 0.9566 (0.8767 / 0.1035) |
| **P1 Zero-Shot** | LOI18 | ALL | 0.3092 (0.3519 / 0.4341) | 0.9569 (0.8739 / 0.1043) |
| **P1 Zero-Shot** | LOI18 | DR | 0.2824 (0.3685 / 0.9646) | 0.9931 (0.9420 / 0.1001) |
| **P2 Reverse** | F31 / LOI12 / LOI18 | ALL | — | 0.4540 / 0.4831 / 0.4771 |
| **P5 In-Domain** | F31 / LOI12 / LOI18 | — | 0.9989 / 0.9981 / 0.9976 | — |
| **P3 Co-Training** | LOI18 | ALL | **0.9976 (0.9603 / 0.0789)** | **0.9554 (0.8723 / 0.1082)** |
| **P3 Co-Training** | LOI18 | DR | 0.9971 (0.9450 / 0.1110) | 0.9932 (0.9412 / 0.1068) |
| **P3 Co-Training** | F31 | ALL | 0.9991 (0.9842 / 0.0281) | 0.9581 (0.8691 / 0.1549) |

