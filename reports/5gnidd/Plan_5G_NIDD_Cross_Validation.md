# Cross-Validation Plan on 5G-NIDD: Feasibility & Generalization Analysis

> **Post-Execution Note (October 26, 2026):** Empirical cross-validation on real 5G-NIDD data has been completed. See [`Report_5G_NIDD_Comparison.md`](Report_5G_NIDD_Comparison.md).  
> Empirical findings updated several preliminary hypotheses from this plan:
> - `SIntPkt` and jitter fields are 100% empty in raw Argus files and require mathematical imputation.
> - Zero-shot transfer yielded an ROC-AUC of 0.3990 (collapsing rather than reaching the projected 0.70–0.90), because real flood and scan attacks are raw packets lacking application payloads.

**Project:** Machine Learning-Based 5G Intrusion Detection  
**Model Architecture:** Random Forest with 31 features trained on UNSW-NB15 (`reports/exp05/rf_A_trainfit.joblib`, reproducing NB07 test-final accuracy = 0.818620)  
**Target Dataset:** 5G-NIDD (Samarakoon et al., University of Oulu, 5GTN) — IEEE DataPort `10203` / Fairdata

---

## 0. Executive Summary

| Evaluation Dimension | Strategic Specification |
|---|---|
| **Data Feasibility** | **Confirmed.** 5G-NIDD utilizes Argus, the identical flow engine underlying UNSW-NB15. 21 of 31 features map directly (representing 87.5% of total tree permutation importance). Missing Bro/Zeek features account for only 0.7% of importance. |
| **Zero-Shot Transfer Operational Feasibility** | **Critically Impaired.** The most important model feature (`ackdat`) functions as a network latency shortcut in UNSW: 99.6% of attack flows have `ackdat >= 10 ms` (due to simulated server saturation), compared to 24.7% for normal flows. In 5G networks, authentic mobile radio propagation causes benign connections to routinely experience latencies in the 10–50 ms range. |
| **Simulated 5G Stress-Test** | Simulating 5G latency shifts on UNSW-NB15 elevated FPR @0.5 from 25.7% to 37.6%–40.7%, while FPR on normal TCP handshakes surged from 28.2% to 43.3%–47.2%. |
| **Mandatory Reporting Paradigm** | Report three distinct empirical metrics: (1) Zero-shot cross-dataset transfer; (2) Domain adaptation with target 5G labels; and (3) In-domain 5G ceiling partitioned by base station. Avoid random 70/30 splits due to temporal correlation and feature leakage. |

---

## 1. 5G-NIDD Benchmark Characteristics

- **Testbed Architecture:** 5GTN Oulu, 3GPP NSA Option 3x with LTE anchor (Band 7) and 5G NR (Band n78, 3.5 GHz). Two pico base stations (BS1, BS2) connected to MEC servers.
- **Monitoring Vantage Point:** S1-U interface between gNodeB and Core UPF. GTP-U tunneling decapsulated.
- **Flow Engine:** Argus standalone flow generator (113 raw fields).
- **Benign Background:** Authentic human users operating commercial 5G smartphones (Motorola g50 5G) engaged in web browsing, video streaming, SSH sessions, SFTP transfers, and push notifications (~90% UDP / QUIC).
- **Attack Generation:** Attacking nodes utilizing hping3 (`--rand-source`), nmap, and slowloris.

---

## 2. Attack Category Comparison

5G-NIDD focuses exclusively on Denial of Service (DoS) and Network Reconnaissance (Scan) attacks. It does not contain application-level Exploits, Fuzzers, Backdoors, Shellcode, Worms, or Generic cryptographic attacks found in UNSW-NB15. Consequently, cross-dataset transfer measures domain generalizability across these specific attack families.

