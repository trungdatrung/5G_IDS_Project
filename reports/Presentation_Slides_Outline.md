# Presentation Slides Outline (Capstone Defense Deck)

## Machine Learning-Based Intrusion Detection System for 5G Networks: Cross-Validation & Supervised Domain Adaptation from UNSW-NB15 to 5G-NIDD

---

### SLIDE 1 — Title & Front Matter
- **Topic:** Machine Learning-Based Intrusion Detection System for 5G Networks: From UNSW-NB15 to 5G-NIDD and Supervised Domain Adaptation.
- **Subtitle:** Why models trained on synthetic enterprise networks collapse on 5G, and how domain adaptation restores operational efficacy.
- **Student Team & Advisor:** [Student Names & Academic Supervisor]
- **Academic Context:** Capstone Graduation Project Defense 2025–2026.

---

### SLIDE 2 — Context & Motivation
- **5G Network Revolution:** High mobility, dynamic radio propagation, GTP-U tunneling, dominance of modern transport protocols (QUIC/UDP streaming, SCTP signaling).
- **The Telemetry Scarcity Dilemma:** Commercial 5G telemetry is scarce; academic and industrial models are predominantly trained on legacy synthetic datasets like UNSW-NB15.
- **Core Research Question:** Can a machine learning model trained purely on synthetic enterprise LAN traffic protect an operational 5G cellular network?

---

### SLIDE 3 — The UNSW-NB15 Baseline & Sanitization Pipeline
- **Dataset Sanitization:** 31 clean features (F31) across 149,501 cleaned records (98,934 train / 50,567 test).
- **Methodological Hygiene:** Excised 8 contaminated Time-to-Live (TTL) shortcuts (D'hooge et al., 2022).
- **Pre-Registered Optimization:** Random Forest tuned strictly on `test-dev` under operational constraint $\text{FPR} \le 0.10$.
- **Baseline Metrics on `test-final`:** Accuracy = 0.8186 (Baseline F31 @0.5) $\rightarrow$ Accuracy = 0.8952, ROC-AUC = 0.9684, FPR = 0.1058 (Winning F39 @0.7311).

---

### SLIDE 4 — Discovery of the 5G-NIDD Ground-Truth Mislabeling Defect
- **Dataset Audit:** Forensic analysis of the world's first operational 5G benchmark (5G-NIDD, Fairdata release).
- **Critical Defect Uncovered:** 281,529 flows (58.91% of the published Benign class) were corrupted duplicates of UDP flood attacks mirrored at BS1 and falsely tagged as Benign.
- **Decontamination:** Sanitized dataset to 379,563 clean, verified flows (208,021 BS1 / 171,542 BS2).
- **Strict Spatial Partitioning:** BS1 for training/validation, BS2 reserved as a single-blind test set.

---

### SLIDE 5 — Zero-Shot Cross-Dataset Transfer: Catastrophic Collapse
- **Experimental Protocol P1:** Deploying the UNSW-trained model directly to 5G-NIDD without target labels.
- **Empirical Collapse:** ROC-AUC drops from 0.9594 on UNSW to **0.3990 on 5G-NIDD** (BS2: 0.3537).
- **Severe Inversion:** PR-AUC (0.7473) falls below the attack base rate ($\pi = 0.8333$), proving inverse probability ranking.
- **False Alarm Explosion:** Benign FPR surges to 61.10% (SCTP 90.2% false alarms; UDP 78.2% false alarms).

---

### SLIDE 6 — Root Cause Diagnostics: Why Did Zero-Shot Transfer Fail?
- **Not a Mapping Artifact:** Round-trip validation on UNSW yields ROC-AUC = 0.9525 ($\Delta = -0.007$).
- **Profound Concept Shift:** In UNSW, attacks are complete application sessions with payloads. In 5G-NIDD, attacks are raw, payload-free packets (40–58 bytes). Trees learned that small packets without replies are normal DNS/ARP flows.
- **Radio Latency Shortcuts:** Synthetic LAN latency `ackdat >= 10 ms` indicated attack server saturation. In 5G cellular channels, authentic smartphone handshakes naturally experience 10–50 ms latency.

---

### SLIDE 7 — Plan A: Supervised 5G Adaptation (Experiment A1 Merged Model)
- **Shortcut-Free LOI18 Schema:** Excises Time-to-Live, sliding window counters, and radio latency metrics.
- **Unified Dual-Domain Model (A1-2):** Co-trained on UNSW train-fit + 5G-train BS1 with equal weighting.
- **Outstanding Performance on 5G BS2:** ROC-AUC = **0.9976**, Recall = **0.9995**, FPR = **0.0789** (constrained under $\le 0.10$).
- **Zero Catastrophic Forgetting:** UNSW test-final ROC-AUC = **0.9554** (only a 0.0015 decrease).
- **Feature Router:** `proto` Gini importance surges from 0.009 to 0.085, acting as an implicit domain dispatcher.

---

### SLIDE 8 — 5G Label Complexity & Few-Shot Learning Curves (Experiment A2)
- **Label Acquisition Target:** Operational maturity requires **~2,000 labelled 5G flows** (+ ~500 validation flows).
- **Hypothesis H1 (Accepted):** When labels are scarce ($n \le 200$), legacy data causes negative transfer (pure 5G outperforms merged by +0.108 ROC-AUC at $n=50$).
- **Hypothesis H2 (Accepted):** 50/50 domain balancing recovers up to 65% of the performance deficit.
- **The Core Bottleneck:** Threshold estimation variance on small validation sets, rather than algorithm ranking discrimination.

---

### SLIDE 9 — Detection of Novel, Unseen 5G Threats (Experiment A3 LOAO)
- **Leave-One-Attack-Out Evaluation:** Testing resilience against unseen zero-day attacks across 8 classes.
- **Sharp Performance Dichotomy:**
  - Raw-Packet Floods & Scans (UDP/SYN/ICMP Flood, SYN Scan): **100% Recall** even when completely withheld.
  - Application-Mimicking Cyberattacks: Severe evasion (HTTPFlood 49.8% Recall; TCPConnectScan 0.6% Recall).
- **Hypothesis H4 (Rejected):** Legacy data does not assist unseen 5G attacks (improved only 1 of 8 classes).
- **SOC False Alarm Trade-Off:** 70% of false alarms on benign 5G traffic stem from decision boundaries covering TCPConnectScan.

---

### SLIDE 10 — Actionable SOC Guidelines & Future Work
- **Takeaway 1:** Never deploy legacy enterprise models zero-shot into operational 5G infrastructures.
- **Takeaway 2:** Operators need ~2,000 in-domain labelled flows to achieve operational stability.
- **Takeaway 3:** Implement multi-tiered security combining flow classifiers for volumetric floods with anomaly detection and stateful inspection for application-layer attacks.
- **Future Directions:** Release deliverable Model Card (A4), automated 5G testbed collector (A5), and unsupervised domain adaptation (CORAL/DANN).

