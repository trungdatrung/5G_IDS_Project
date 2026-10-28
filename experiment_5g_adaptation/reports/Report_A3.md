# Technical Report A3: Leave-One-Attack-Out Protocol (Zero-Day 5G Detection)

**Execution Date:** October 27, 2026 · **Configuration:** FULL (300 estimators, random seed 42) · **Runtime:** ~20 minutes  
**Experimental Specification:** [`docs/Plan_A_5G_Supervised_Adaptation.md`](../docs/Plan_A_5G_Supervised_Adaptation.md) §4  
**Execution Script:** `src/A3_loao.py`  
**Underlying Data Artifacts:**
- Tables: `results/A3_loao/tables/A3_loao.csv`, `A3_ket_qua.json`
- Figures: `results/A3_loao/figures/A3_loao.png`
- Execution Log: `results/A3_loao/logs/A3_log.txt`

---

## 0. Executive Summary

| Research Question / Pre-Registered Hypothesis | Empirical Outcome |
|---|---|
| **Can the model intercept unseen 5G attack classes?** | **Dichotomy by attack profile.** Raw-packet floods and scans (UDPFlood, SYNFlood, ICMPFlood, SYNScan) are intercepted with **100% Recall** even when withheld during training. However, attacks mimicking legitimate application semantics suffer severe evasion: **HTTPFlood (49.8% Recall)**, **UDPScan (47.4% Recall)**, and **TCPConnectScan (0.6% Recall)**. |
| **Hypothesis H4: Does legacy UNSW data assist unseen detection?** | **REJECTED (False).** Adding legacy enterprise data improved recall by $\ge 0.05$ on only 1 of 8 attacks (SlowrateDoS: +0.0718), failing the pre-registered threshold of $\ge 2$ classes. For HTTPFlood, adding UNSW degraded local ROC-AUC from 0.7776 to 0.7003. |
| **Pre-Registered Prediction Accuracy** | 0 of 8 exact intervals matched. Predictions were overly pessimistic regarding raw flood/scan attacks, and overly optimistic regarding application-level attacks. |
| **Stopping Rule Trigger** | Not triggered. Detection recall on seen attacks remained $\ge 0.9985$ across all withheld trials. |
| **Operational Significance for SOCs** | The ~99.9% recall of model A1-2 applies strictly to attack families represented in training telemetry. Detecting novel application-layer 5G threats requires multi-tiered anomaly detection. |

---

## 1. Empirical Results on 5G BS2 (Threshold Calibrated on Withheld 5G-val, $\text{FPR} \le 0.10$)

| Withheld Attack ($T$) | Flow Count ($n$) | Pre-Reg Expected Range | Recall $T$ (A3-a Pure 5G) | Recall $T$ (A3-b Merged) | Benign FPR (A3-a / A3-b) | ROC Benign vs $T$ (A3-a / A3-b) | Seen Attack Recall (A3-a / A3-b) |
|---|---|---|---|---|---|---|---|
| **HTTPFlood** | 64,691 | High ($\ge 0.90$) | **0.4979** | 0.4799 | 0.0729 / 0.0809 | 0.7776 / 0.7003 | 1.0000 / 0.9999 |
| **SlowrateDoS** | 37,032 | High ($\ge 0.90$) | 0.8769 | **0.9487** | 0.0675 / 0.0718 | 0.9457 / 0.9393 | 0.9992 / 0.9994 |
| **UDPFlood** | 30,656 | Med–High ($0.60\text{--}0.95$) | **1.0000** | 1.0000 | 0.0775 / 0.0823 | 0.9228 / 0.9350 | 0.9985 / 0.9994 |
| **TCPConnectScan** | 10,028 | Low–Med ($0.20\text{--}0.60$) | **0.0057** | 0.0053 | **0.1201** / **0.0245** | 0.8601 / 0.6474 | 1.0000 / 0.9997 |
| **SYNFlood** | 4,929 | Med–High ($0.60\text{--}0.95$) | **1.0000** | 1.0000 | 0.0788 / 0.0819 | 0.9253 / 0.9928 | 0.9990 / 0.9999 |
| **SYNScan** | 519 | Medium ($0.40\text{--}0.80$) | **1.0000** | 1.0000 | 0.0769 / 0.0691 | 0.9968 / 0.9935 | 0.9995 / 0.9994 |
| **ICMPFlood** | 462 | Low ($< 0.40$) | **1.0000** | 1.0000 | 0.0768 / 0.0789 | 0.9989 / 0.9990 | 0.9993 / 0.9997 |
| **UDPScan** | 209 | Low ($< 0.40$) | 0.4737 | 0.4737 | 0.0772 / 0.0804 | 0.7019 / 0.8022 | 0.9996 / 0.9999 |

---

## 2. Key Diagnostic Findings

1. **Learning the Benign Mobile Manifold:** The supervised 5G model effectively constructs an envelope around authentic mobile traffic. Volumetric floods and scans emitting raw packets (40–60 bytes without payload) diverge radically from normal mobile patterns, yielding 100% recall even when unseen.
2. **The Application Evasion Vulnerability:** Cyberattacks utilizing authentic application-layer semantics (HTTP transactions, full TCP handshakes) blend into legitimate smartphone browsing and streaming telemetry. When novel, these attacks evade detection unless represented in training data.
3. **The Benign False Alarm Trade-Off:** In A3-b, withholding TCPConnectScan causes benign FPR to plummet from 0.0789 to 0.0245. This demonstrates that approximately 70% of false alarms on legitimate 5G traffic are induced by stretching decision boundaries to cover TCPConnectScan flows.

