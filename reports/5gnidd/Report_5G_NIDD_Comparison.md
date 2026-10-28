# Comprehensive Technical Report: 5G-NIDD vs. UNSW-NB15 Cross-Dataset Generalization & Ground-Truth Quality Audit

**Project:** Machine Learning-Based Intrusion Detection for 5G Cellular Networks  
**Baseline Model:** Random Forest with 31 clean features (`reports/exp05/rf_A_trainfit.joblib`, exactly reproducing NB07 test-final Accuracy = 0.818620)  
**Evaluation Target:** The 5G-NIDD dataset (Fairdata Open Access, CC BY 4.0 license)  
**Replication Pipeline:**
- Harmonization: `python -I -X utf8 reports/5gnidd/build_5gnidd_unsw31.py .`
- Evaluation: `python -I -X utf8 reports/5gnidd/eval_5gnidd.py .`
- Diagnostics: `python -I -X utf8 reports/5gnidd/diagnose_similarity.py .`

---

## 0. Executive Summary

| Evaluation Inquiry | Empirical Finding |
|---|---|
| **Can 5G-NIDD be evaluated directly by the baseline model?** | **YES.** The harmonized dataset `data/5gnidd/cleaned/5gnidd_unsw31.parquet` contains **exactly 31 features, identical column names, data types, and physical units** matching cleaned UNSW-NB15. It encompasses 379,563 clean flows (63,283 Benign, 316,280 Attack) partitioned across BS1 and BS2. |
| **Is the feature harmonization mapping reliable?** | **YES.** 19 of 31 features (accounting for 83% of tree importance) match 1-to-1 or follow verified Argus formulas. A round-trip validation experiment on UNSW test-final proved that applying all feature approximations and conversions reduced ROC-AUC by only **0.007** (0.9594 $\rightarrow$ 0.9525), confirming that mapping artifacts cannot account for transfer failure. |
| **Can the baseline model detect intrusions in 5G telemetry?** | **NO. Catastrophic Transfer Failure.** ROC-AUC collapses to **0.3990** (substantially worse than random guessing 0.5000), Balanced Accuracy @0.5 is **0.4461**, and MCC is **−0.0804**. The model assigns high attack probabilities to benign mobile traffic (FPR 61.1%) while missing virtually 100% of UDP floods, SYN floods, ICMP floods, and port scans (Recall $\approx 0.000$). |
| **What is the root cause of this zero-shot failure?** | **Profound Concept Shift.** The two benchmarks assign identical attack category names to fundamentally divergent network behaviors. In UNSW, 'Reconnaissance' flows are complete application sessions with FIN flags and 354 reply bytes; in 5G-NIDD, scans and floods are raw single packets (40–58 bytes) without payloads. Having learned that small packets without replies represent normal enterprise traffic, the model misclassifies real 5G attacks as Benign. |
| **Forensic Quality Audit of 5G-NIDD** | **281,529 flows (58.91% of the published Benign class) were corrupted mislabelled attack duplicates.** Specifically, UDP flood attacks launched against BS2 were mirrored at BS1 and falsely recorded under the label 'Benign'. Furthermore, inter-packet arrival times and jitter fields are 100% empty in the raw Argus release. |

---

## 1. Zero-Shot Transfer Metrics Breakdown

Deploying the UNSW-NB15 baseline Random Forest model (F31) directly to 5G-NIDD partitions yields the following metrics:

| Partition / Split | Base Rate ($\pi$) | Operating Threshold | ROC-AUC | PR-AUC | Accuracy | Balanced Acc | MCC | Precision | Recall | FPR |
|---|---|---|---|---|---|---|---|---|---|---|
| **5G Combined** | 0.8333 | 0.5000 | 0.3990 | 0.7473 | 0.4839 | 0.4461 | -0.0804 | 0.8054 | 0.5032 | 0.6110 |
| **5G Combined** | 0.8333 | 0.6949 (UNSW $\theta^*$) | 0.3990 | 0.7473 | 0.1992 | 0.3567 | -0.2859 | 0.5962 | 0.1200 | 0.4067 |
| **5G Combined** | 0.8333 | EM Recalibration | 0.3990 | 0.7473 | 0.8197 | 0.5026 | 0.0128 | 0.8336 | 0.9782 | 0.9730 |
| **5G BS1** | 0.8063 | 0.5000 | 0.4252 | 0.7248 | 0.4767 | 0.4537 | -0.0736 | 0.7782 | 0.4914 | 0.5840 |
| **5G BS2** | 0.8658 | 0.5000 | 0.3537 | 0.7763 | 0.4928 | 0.4295 | -0.0964 | 0.8351 | 0.5169 | 0.6579 |
| **5G BS2** | 0.8658 | 0.6949 (UNSW $\theta^*$) | 0.3537 | 0.7763 | 0.1675 | 0.3325 | -0.3058 | 0.6945 | 0.1225 | 0.4575 |

---

## 2. Disaggregation of Zero-Shot Recall by Attack Category

| Traffic / Cyberattack Category | Cleaned Flows ($n$) | Recall @0.50 | Recall @0.6949 | Behavioral Divergence Mechanism |
|---|---|---|---|---|
| **Benign (= False Alarm Rate)** | 63,283 | 0.6110 | 0.4067 | Normal mobile traffic: UDP streaming incurs 78.2% false alarms; SCTP S1-AP signaling incurs 90.2% false alarms. |
| **HTTPFlood** | 140,811 | 0.6944 | 0.2448 | Complete TCP handshakes with HTTP payloads; mirrors synthetic DoS profiles. |
| **SlowrateDoS** | 73,123 | 0.8340 | 0.0442 | Extended connection durations and elevated handshake latency; partially detected. |
| **UDPScan** | 584 | 0.4007 | 0.3305 | Sparse UDP port probing; partially identified via destination port numbers. |
| **UDPFlood** | 69,921 | 0.0033 | 0.0000 | 42-byte raw hping3 packets; misclassified as benign UDP DNS/ARP. |
| **TCPConnectScan** | 20,042 | 0.0010 | 0.0000 | Completed TCP handshake immediately terminated; misclassified as normal mobile TCP. |
| **SYNFlood** | 9,721 | 0.0000 | 0.0000 | Raw TCP SYN packets without payload; misclassified as normal TCP handshake attempts. |
| **SYNScan** | 1,048 | 0.0000 | 0.0000 | Half-open SYN probes; misclassified as normal connection requests. |
| **ICMPFlood** | 1,030 | 0.0000 | 0.0000 | Raw echo requests; misclassified as normal ICMP reachability checks. |

---

## 3. The 5G-NIDD Ground-Truth Mislabeling Defect

During forensic quality auditing of the raw Argus telemetry (`BTS1_BTS2_fields_preserved.csv`), cross-referencing timestamps and 5-tuple socket addresses against attacking node orchestration scripts uncovered an egregious ground-truth labeling error:
- An automated attacking node executing high-volume UDP flood attacks against BS2 had its packets captured concurrently across both base station monitoring interfaces.
- At the target interface (BS2), flows were correctly labelled as `UDPFlood`.
- Concurrently, at the BS1 monitor, 281,529 duplicate flows of this identical attack were erroneously tagged as `Benign`.
- This corrupted 58.91% of the published Benign class, creating massive data leakage and rendering uncleaned cross-station evaluations invalid.
- Our sanitization pipeline successfully expunged these 281,529 contaminated flows, restoring the true distribution of authentic human user smartphone activity.

