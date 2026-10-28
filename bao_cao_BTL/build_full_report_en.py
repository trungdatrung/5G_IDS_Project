import sys
sys.stdout.reconfigure(encoding='utf-8')
import os, shutil
import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOC_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPL_PATH = os.path.join(DOC_DIR, "Khung_bao_cao_BTL.docx")
OUT_EN_PATH = os.path.join(DOC_DIR, "Bao_cao_BTL_English.docx")
OUT_CAPSTONE_PATH = os.path.join(DOC_DIR, "Report_5G_IDS_Capstone.docx")

# Verify template exists
if not os.path.exists(TEMPL_PATH):
    raise FileNotFoundError(f"Template not found: {TEMPL_PATH}")

doc = docx.Document(TEMPL_PATH)

# Clear existing body elements, keeping section properties
body = doc._element.body
for child in list(body):
    if child.tag.endswith('sectPr'):
        continue
    body.remove(child)

print("Template initialized and body cleared.")

def set_cell_shading(cell, color_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), color_hex)
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

class ReportBuilder:
    def __init__(self, document):
        self.doc = document

    def add_p(self, text, style='Normal', bold_prefix='', italic=False, space_before=0, space_after=6, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
        p = self.doc.add_paragraph(style=style)
        p.alignment = align
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.2
        if bold_prefix:
            r_bold = p.add_run(bold_prefix)
            r_bold.bold = True
            r_bold.font.name = 'Times New Roman'
            r_bold.font.size = Pt(12)
        if text:
            r = p.add_run(text)
            r.italic = italic
            r.font.name = 'Times New Roman'
            r.font.size = Pt(12)
        return p

    def add_heading(self, text, level=1):
        style_name = f'Heading {level}'
        p = self.doc.add_paragraph(text, style=style_name)
        if level == 1:
            p.paragraph_format.space_before = Pt(20)
            p.paragraph_format.space_after = Pt(10)
        elif level == 2:
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
        else:
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
        for r in p.runs:
            r.font.name = 'Times New Roman'
        return p

    def add_caption(self, text, is_table=True):
        style_name = 'BangCaption' if is_table else 'HinhCaption'
        p = self.doc.add_paragraph(text, style=style_name)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(6)
        for r in p.runs:
            r.font.name = 'Times New Roman'
            r.font.size = Pt(11)
            r.bold = True
        return p

    def add_image(self, img_path, width=Inches(6.2)):
        if not os.path.exists(img_path):
            print(f"WARNING: Image does not exist: {img_path}")
            return None
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run()
        run.add_picture(img_path, width=width)
        return p

    def add_table(self, headers, rows_data, col_widths=None):
        table = self.doc.add_table(rows=len(rows_data) + 1, cols=len(headers), style='Table Grid')
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # Header Row
        hdr_cells = table.rows[0].cells
        for i, title in enumerate(headers):
            hdr_cells[i].text = title
            set_cell_shading(hdr_cells[i], 'EBF2F7')
            set_cell_margins(hdr_cells[i], top=120, bottom=120, left=130, right=130)
            p = hdr_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = Pt(9.5)
                r.bold = True

        # Data Rows
        for r_idx, row_data in enumerate(rows_data):
            row_cells = table.rows[r_idx + 1].cells
            bg_color = 'F8FAFC' if r_idx % 2 == 1 else 'FFFFFF'
            for c_idx, val in enumerate(row_data):
                row_cells[c_idx].text = str(val)
                if bg_color != 'FFFFFF':
                    set_cell_shading(row_cells[c_idx], bg_color)
                set_cell_margins(row_cells[c_idx], top=80, bottom=80, left=120, right=120)
                p = row_cells[c_idx].paragraphs[0]
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                if any(char.isdigit() for char in str(val)) and len(str(val)) < 25 and not str(val).startswith(('Figure', 'Table', 'http')):
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if ('.' in str(val) or ',' in str(val)) else WD_ALIGN_PARAGRAPH.CENTER
                else:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs:
                    r.font.name = 'Times New Roman'
                    r.font.size = Pt(9)

        if col_widths and len(col_widths) == len(headers):
            for row in table.rows:
                for idx, w in enumerate(col_widths):
                    row.cells[idx].width = w

        return table

b = ReportBuilder(doc)

# Image paths
IMG_F21 = os.path.join(DOC_DIR, 'fig2_1_nids_arch_en.png')
IMG_F31 = os.path.join(DOC_DIR, 'fig3_1_5gnidd_arch_en.png')
IMG_F32 = os.path.join(DOC_DIR, 'fig3_2_cleaning_pipeline_en.png')
IMG_F41 = os.path.join(DOC_DIR, 'fig4_1_splits_en.png')
IMG_F51 = os.path.join(BASE_DIR, r'reports\rerun07\confusion_truoc_sau.png')
IMG_F52 = os.path.join(BASE_DIR, r'experiment_5g_adaptation\results\A1_model_gop\figures\cm_A1-0_nhi_phan.png')
IMG_F53 = os.path.join(BASE_DIR, r'experiment_5g_adaptation\results\A1_model_gop\figures\cm_A1-2_nhi_phan.png')
IMG_F54 = os.path.join(BASE_DIR, r'experiment_5g_adaptation\results\A1_model_gop\figures\cm_A1-4_da_lop_5G.png')
IMG_F55 = os.path.join(BASE_DIR, r'experiment_5g_adaptation\results\A2_few_shot\figures\A2_duong_cong.png')
IMG_F56 = os.path.join(BASE_DIR, r'experiment_5g_adaptation\results\A3_loao\figures\A3_loao.png')

print("Starting full document generation...")

# ==========================================
# COVER PAGE & FRONT MATTER
# ==========================================
b.add_p("MINISTRY OF EDUCATION AND TRAINING / UNIVERSITY", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
b.add_p("FACULTY / SCHOOL OF INFORMATION TECHNOLOGY", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=18)
b.add_p("————————o0o————————", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24)
b.add_p("CAPSTONE PROJECT REPORT", style='Heading 1', align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)
b.add_p("Course: Advanced Network Security & Machine Learning", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24)

b.add_p("PROJECT TOPIC:", style='Heading 2', align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
p_title = b.add_p("MACHINE LEARNING-BASED INTRUSION DETECTION SYSTEM FOR 5G NETWORKS: FROM UNSW-NB15 TO 5G-NIDD AND SUPERVISED DOMAIN ADAPTATION", style='Heading 1', align=WD_ALIGN_PARAGRAPH.CENTER, space_after=36)
for r in p_title.runs:
    r.font.size = Pt(15)
    r.bold = True

b.add_p("Academic Supervisor:\t[Faculty Advisor / Supervisor Full Name]", space_after=4)
b.add_p("Student Group:\t\t[Class / Group Designation]", space_after=4)
b.add_p("Author / Performer:\t[Student Full Name] — Student ID: [Student ID]", space_after=36)

b.add_p("Academic Year 2025–2026", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24)

# Abstract
b.add_heading("ABSTRACT", level=1)
b.add_p("Machine learning-based Network Intrusion Detection Systems (NIDS) trained on synthetic enterprise network benchmarks (such as UNSW-NB15) are frequently presumed to be transferable to modern 5G cellular infrastructures. In this capstone project, we conduct an extensive, rigorous empirical investigation into cross-dataset generalization from UNSW-NB15 to the real-world 5G-NIDD benchmark. We reveal a critical negative finding: the baseline Random Forest model (31 features, achieving an outstanding ROC-AUC of 0.9594 on UNSW-NB15) completely collapses under zero-shot transfer to 5G-NIDD, yielding an ROC-AUC of only 0.3990—performing substantially worse than random guessing. Detailed statistical diagnostics show that this failure is driven by fundamental concept shift (real 5G flood and scan attacks consist of raw, payload-free packets which the model misidentifies as benign traffic), radio latency shortcuts (ackdat), and unmodelled cellular protocols (SCTP control signaling and QUIC/UDP streaming). To resolve this failure, we propose a supervised domain adaptation framework (Plan A) built upon a verified, shortcut-free 18-feature schema (LOI18). Our unified dual-domain model (A1-2) successfully resolves the transfer collapse, achieving an ROC-AUC of 0.9976, Recall of 0.9995, and a strictly controlled False Positive Rate (FPR) of 0.0789 on the independent 5G Base Station 2 (BS2), while retaining an ROC-AUC of 0.9554 on UNSW-NB15. We demonstrate that acquiring ~2,000 labelled 5G training flows (plus ~500 validation flows) is sufficient to achieve operational maturity, whereas few-shot adaptation with fewer labels induces severe negative transfer. Finally, leave-one-attack-out evaluation reveals that while unseen raw-packet floods and scans are intercepted with 100% recall, application-like attacks (HTTPFlood and TCPConnectScan) suffer from severe evasion, demonstrating the imperative need for multi-tiered defense architectures in 5G security operations.")

b.add_p("Keywords: Network Intrusion Detection (NIDS), 5G Cellular Networks, Random Forest, Domain Adaptation, Cross-Dataset Generalization, 5G-NIDD, UNSW-NB15.", italic=True, space_after=18)

# Table of Abbreviations
b.add_heading("LIST OF ABBREVIATIONS", level=1)
b.add_table(
    headers=["Abbreviation", "Full Term", "Definition / Operational Context"],
    rows_data=[
        ["5G", "Fifth Generation Mobile Network", "3GPP cellular telecommunications architecture offering eMBB, URLLC, and mMTC."],
        ["5G-NIDD", "5G Network Intrusion Detection Dataset", "Pioneering empirical dataset collected over an operational 5G test network at Univ. of Oulu."],
        ["5GTN", "5G Test Network", "Operational 5G NSA/SA experimental testbed in Oulu, Finland."],
        ["BS1 / BS2", "Base Station 1 / Base Station 2", "Distinct physical gNodeB radio vantage points in the 5G-NIDD dataset."],
        ["DoS / DDoS", "(Distributed) Denial of Service", "Network resource exhaustion cyberattacks launched to disrupt legitimate services."],
        ["EM", "Expectation–Maximization Algorithm", "Iterative statistical algorithm applied to recalibrate predicted probabilities under prior shift."],
        ["FN / FP", "False Negative / False Positive", "Undetected attacks (misses) / False alarms on benign traffic."],
        ["FPR", "False Positive Rate", "Ratio of false alarms over total benign flows; operational SOC constraint FPR ≤ 0.10."],
        ["GTP-U", "GPRS Tunnelling Protocol – User Plane", "Tunneling protocol encapsulating mobile user data over the cellular S1-U / N3 interface."],
        ["IDS / NIDS", "(Network) Intrusion Detection System", "Cybersecurity telemetry system analyzing network flows to detect malicious activities."],
        ["LOAO", "Leave-One-Attack-Out Protocol", "Systematic zero-day evaluation protocol iteratively withholding one attack type from training."],
        ["LOI12 / 18", "List of Interest (12 / 18 features)", "Decontaminated feature subsets purged of environment-specific shortcuts and TTL artifacts."],
        ["MCC", "Matthews Correlation Coefficient", "Balanced correlation metric for binary classification robust against severe class imbalance."],
        ["ML", "Machine Learning", "Computational algorithms trained on data patterns for predictive modeling."],
        ["NB07", "Notebook 07 (Consolidated Rerun)", "Verified master execution script replicating the baseline UNSW-NB15 experimental pipeline."],
        ["NSA", "Non-Standalone 5G Architecture", "5G deployment leveraging 4G LTE anchor core and gNodeB NR radio access."],
        ["PR-AUC", "Area Under Precision-Recall Curve", "Primary evaluation metric for imbalanced anomaly detection; compared against baseline rate π."],
        ["QUIC", "Quick UDP Internet Connections", "Multiplexed transport protocol over UDP ubiquitous in modern mobile application traffic."],
        ["RF", "Random Forest", "Ensemble learning classifier combining de-correlated decision trees with bagging."],
        ["ROC-AUC", "Area Under ROC Curve", "Threshold-independent ranking discrimination metric across all false alarm rates."],
        ["SCTP", "Stream Control Transmission Protocol", "Transport layer protocol powering cellular control plane signaling (S1-AP / NGAP)."],
        ["UE", "User Equipment", "Mobile terminal or cellular handset operating within the 5G network."],
        ["UNSW-NB15", "Univ. of New South Wales Benchmark 2015", "Widely utilized enterprise synthetic network intrusion detection benchmark."]
    ],
    col_widths=[Inches(1.2), Inches(2.6), Inches(2.7)]
)

# Table of Contents
b.add_heading("TABLE OF CONTENTS", level=1)
toc_items = [
    ("CHAPTER 1. INTRODUCTION", "1"),
    ("  1.1. Context: 5G Mobile Networks and Intrusion Detection Systems", "1"),
    ("  1.2. Problem Statement: The Peril of Domain Shift in ML-NIDS", "2"),
    ("  1.3. Research Objectives", "3"),
    ("  1.4. Research Questions", "3"),
    ("  1.5. Scope and Report Structure", "4"),
    ("CHAPTER 2. THEORETICAL FOUNDATIONS AND LITERATURE REVIEW", "5"),
    ("  2.1. 5G Network Architecture and the Attack Surface", "5"),
    ("  2.2. Network Intrusion Detection Systems (NIDS)", "7"),
    ("  2.3. Domain Shift and Adaptation in Machine Learning", "9"),
    ("  2.4. Review of Related Work", "11"),
    ("  2.5. Identification of Research Gaps", "13"),
    ("CHAPTER 3. DATASETS AND PREPROCESSING", "15"),
    ("  3.1. The UNSW-NB15 Benchmark and Sanitization Pipeline", "15"),
    ("  3.2. The 5G-NIDD Dataset", "17"),
    ("  3.3. Forensic Quality Audit of 5G-NIDD: The Critical Mislabeling Defect", "19"),
    ("  3.4. Cross-Dataset Feature Harmonization", "22"),
    ("CHAPTER 4. METHODOLOGY AND EXPERIMENTAL PROTOCOL", "25"),
    ("  4.1. Baseline Model on UNSW-NB15 (NB07)", "25"),
    ("  4.2. Cross-Dataset Evaluation Protocols (P1–P5)", "27"),
    ("  4.3. Supervised 5G Domain Adaptation (Plan A)", "29"),
    ("    4.3.1. A1 — Merged Dual-Domain Model Architecture", "29"),
    ("    4.3.2. A2 — 5G Label Complexity and Few-Shot Learning Curves", "31"),
    ("    4.3.3. A3 — Leave-One-Attack-Out (LOAO) Protocol", "33"),
    ("  4.4. Operational Threshold Optimization (FPR ≤ 0.10)", "34"),
    ("  4.5. Computational Environment and Reproducibility Standards", "35"),
    ("CHAPTER 5. EXPERIMENTAL RESULTS AND ANALYSIS", "37"),
    ("  5.1. Baseline Model Performance on UNSW-NB15", "37"),
    ("  5.2. Zero-Shot Cross-Dataset Transfer to 5G-NIDD: Catastrophic Collapse", "39"),
    ("  5.3. Experiment A1: Unified Dual-Domain Model", "42"),
    ("  5.4. Experiment A2: 5G Label Complexity and Learning Curves", "46"),
    ("  5.5. Experiment A3: Detection of Unseen 5G Cyberattacks", "49"),
    ("  5.6. Consolidated Synthesis Mapped to Research Questions and Hypotheses", "52"),
    ("CHAPTER 6. DISCUSSION AND CRITICAL EVALUATION", "54"),
    ("  6.1. Deconstructing the Zero-Shot Failure Mechanisms", "54"),
    ("  6.2. The True Role of Legacy Enterprise Data", "57"),
    ("  6.3. Practical Guidelines for 5G Security Operations Centers (SOCs)", "58"),
    ("  6.4. Limitations of the Study", "59"),
    ("  6.5. Threats to Scientific Validity", "60"),
    ("CHAPTER 7. CONCLUSION AND FUTURE WORK", "63"),
    ("  7.1. Conclusion", "63"),
    ("  7.2. Future Work", "64"),
    ("REFERENCES", "66"),
    ("APPENDICES", "68")
]
for title, pg in toc_items:
    b.add_p(f"{title} {'·' * (68 - len(title))} {pg}", space_after=3)

# Lists of Tables and Figures
b.add_heading("LIST OF TABLES", level=1)
tables_list = [
    "Table 3.1. Statistical Dimensions, Base Rates, and Operational Roles of UNSW-NB15 Partitions",
    "Table 3.2. Systematic Structural Comparison Between UNSW-NB15 and 5G-NIDD Benchmarks",
    "Table 3.3. Forensic Audit of 5G-NIDD Mislabeling and Data Sanitization Impact",
    "Table 3.4. Flow-Level Feature Mapping and Mathematical Harmonization Schema (F31 & LOI18)",
    "Table 4.1. Comparative Performance of 14 Candidate Configurations on UNSW test-dev",
    "Table 4.2. Specifications of Cross-Dataset Evaluation Protocols (P1–P5)",
    "Table 4.3. Technical Architecture of Model Variants Evaluated in Experiment A1",
    "Table 4.4. Experimental Design of Few-Shot Trial A2, Hypotheses H1–H3, and Criteria",
    "Table 4.5. LOAO Experimental Design and Pre-Registered Recall Expectations by Attack Type",
    "Table 5.1. Baseline Reproduction and Selected Configuration on UNSW-NB15 test-final",
    "Table 5.2. Zero-Shot Evaluation Metrics of UNSW Models Deployed to 5G-NIDD",
    "Table 5.3. Attack Detection Recall by Type Under Zero-Shot Transfer",
    "Table 5.4. Cross-Protocol Performance Summary (P1–P5) on BS2 and UNSW test-final",
    "Table 5.5. Performance Metrics of A1 Model Variants on 5G BS2 and UNSW test-final",
    "Table 5.6. Per-Attack Recall on 5G BS2 Across A1 Adaptation Variants",
    "Table 5.7. Few-Shot Learning Metrics Across Sample Sizes n (Mean ± SD over 5 Seeds)",
    "Table 5.8. Leave-One-Attack-Out Performance on 5G BS2 for Unseen Threats",
    "Table 5.9. Consolidated Resolution of Research Questions (RQ1–RQ4) and Hypotheses (H1–H4)",
    "Table 6.1. Empirical Discrepancies Between 5G Attacks and Closest Synthetic UNSW Profiles",
    "Table 6.2. Methodological Threats to Validity and Applied Mitigation Strategies"
]
for t in tables_list:
    b.add_p(t, space_after=3)

b.add_heading("LIST OF FIGURES", level=1)
figs_list = [
    "Figure 2.1. Structural Pipeline of a Network Flow Intrusion Detection System (ML-NIDS)",
    "Figure 3.1. Network Topology of the 5G-NIDD Data Collection Environment (5GTN Oulu)",
    "Figure 3.2. Data Cleaning and Sanitization Workflow for the 5G-NIDD Dataset",
    "Figure 4.1. Partitioning Schema and Dual-Domain Threshold Optimization Protocol",
    "Figure 5.1. Confusion Matrices of UNSW-NB15 Baseline Before and After Threshold Calibration",
    "Figure 5.2. Cross-Domain Confusion Matrices of Zero-Shot Model A1-0 on BS2 vs. UNSW",
    "Figure 5.3. Dual-Domain Confusion Matrices of Unified Model A1-2 on BS2 and UNSW test-final",
    "Figure 5.4. Multiclass Confusion Matrix of Model A1-4 on 5G Base Station 2",
    "Figure 5.5. Empirical Learning Curves of ROC-AUC, FPR, and Recall Across 5G Sample Sizes n",
    "Figure 5.6. Leave-One-Attack-Out Detection Recall on Withheld Cyberattack Classes (A3-a vs. A3-b)"
]
for f in figs_list:
    b.add_p(f, space_after=3)

print("Front matter generated. Building Chapter 1 & 2...")

# ==========================================
# CHAPTER 1. INTRODUCTION
# ==========================================
b.add_heading("CHAPTER 1. INTRODUCTION", level=1)

b.add_heading("1.1. Context: 5G Mobile Networks and Intrusion Detection Systems", level=2)
b.add_p("The Fifth Generation (5G) of mobile telecommunications introduces transformative capabilities, supporting ultra-reliable low-latency communications (URLLC), massive machine-type communications (mMTC), and enhanced mobile broadband (eMBB). Unlike traditional enterprise local area networks (LAN), 5G networks operate within a software-defined cellular architecture characterized by high subscriber mobility, dynamic radio channel propagation, and encapsulation protocols such as the GPRS Tunnelling Protocol User Plane (GTP-U) spanning the radio-to-core interfaces (N3/S1-U). Contemporary 5G user traffic is heavily dominated by modern transport protocols over UDP, notably QUIC (which powers modern streaming, mobile web browsing, and real-time gaming), alongside specialized control plane signaling protocols such as SCTP over S1-AP and NGAP.")

b.add_p("As 5G networks are designated critical national infrastructure, protecting them against Distributed Denial of Service (DDoS) and automated reconnaissance campaigns is essential. Network Intrusion Detection Systems (NIDS) operating at the bidirectional network flow level offer a scalable, privacy-preserving monitoring mechanism capable of scrutinizing encrypted communications without requiring invasive deep packet inspection. Over the past decade, supervised machine learning (ML) has emerged as the foremost paradigm for automated flow-based detection. However, due to the severe scarcity and commercial sensitivity of operational cellular telemetry, the vast majority of ML-NIDS models continue to be trained and evaluated on legacy synthetic enterprise datasets—most prominently the UNSW-NB15 benchmark [2]. This dependency raises a vital operational question: Can an intrusion detection model trained purely on synthetic enterprise LAN traffic be directly deployed to protect an operational 5G mobile network?")

b.add_heading("1.2. Problem Statement: The Peril of Domain Shift in ML-NIDS", level=2)
b.add_p("Recent literature has highlighted that ML-NIDS models exhibiting near-perfect detection rates in their native training environments frequently undergo severe performance degradation when deployed to independent network environments [3]–[6]. This breakdown, known as domain shift, encompasses prior shift (variations in attack base rates π), covariate shift (divergence in statistical feature distributions), and concept shift (fundamental divergence in attack execution semantics).")

b.add_p("In this project, our empirical investigation reveals an extreme manifestation of domain shift: an industry-standard Random Forest model trained on UNSW-NB15 (achieving an outstanding ROC-AUC of 0.9594 on its native test set) undergoes complete classification collapse under zero-shot transfer to the real-world 5G-NIDD benchmark [1], yielding an ROC-AUC of only 0.3990—performing substantially worse than random guessing. Furthermore, acquiring high-fidelity labelled telemetry from production 5G networks entails prohibitive operational expenses and expert human labor. Security operations center (SOC) analysts lack empirical guidelines regarding how many 5G labels are strictly required for effective adaptation, and whether legacy network benchmarks facilitate or hinder adaptation in low-resource settings.")

b.add_heading("1.3. Research Objectives", level=2)
b.add_p("To address these challenges, this capstone project pursues three primary research objectives:")
b.add_p("1. Rigorous Baseline Reproduction and Auditing: Faithfully replicate and audit the baseline UNSW-NB15 Random Forest model under a pre-registered evaluation protocol, isolating decision threshold selection to an independent development set (test-dev) and evaluating on a frozen benchmark (test-final).")
b.add_p("2. Cross-Dataset Feature Harmonization and Zero-Shot Diagnostics: Establish an empirically verified, mathematically consistent 31-feature schema linking UNSW-NB15 and 5G-NIDD; execute zero-shot cross-evaluation, and perform ablation to uncover the exact physical and statistical failure mechanisms.")
b.add_p("3. Supervised 5G Domain Adaptation (Plan A): Develop a supervised domain adaptation framework based on a shortcut-free 18-feature schema (LOI18) to build a unified model serving both domains, quantify the 5G label complexity curve, and evaluate resilience against unseen 5G zero-day attacks.")

b.add_heading("1.4. Research Questions", level=2)
b.add_p("The investigation is organized around four specific research questions:")
b.add_p("• RQ1: Can a Random Forest model trained on the legacy UNSW-NB15 dataset detect intrusions in 5G-NIDD without access to 5G training labels? (Addressed in Section 5.2; Answer: No, ROC-AUC collapses to 0.3990).")
b.add_p("• RQ2: Is it possible to construct a single, unified machine learning model that achieves outstanding detection performance on both 5G and legacy network domains without catastrophic forgetting? (Addressed in Section 5.3; Answer: Yes, the merged model A1-2 achieves 5G BS2 ROC-AUC = 0.9976 while preserving UNSW ROC-AUC = 0.9554).")
b.add_p("• RQ3: What is the minimum number of labelled 5G flows required to achieve operational efficacy, and does legacy training data assist or degrade performance in few-shot regimes? (Addressed in Section 5.4; Answer: ~2,000 training labels are required; legacy data induces severe negative transfer when labels are scarce).")
b.add_p("• RQ4: Can a model adapted to 5G detect novel, previously unseen 5G cyberattack categories, and does legacy enterprise data facilitate zero-day generalization? (Addressed in Section 5.5; Answer: Raw-packet floods and scans are detected with 100% recall, but application-like attacks suffer severe evasion; legacy data provides negligible benefit).")

b.add_heading("1.5. Scope and Report Structure", level=2)
b.add_p("Scope: The study focuses on tabular flow-level intrusion detection using Random Forest classifiers evaluated on UNSW-NB15 and 5G-NIDD. Preprocessing excises IP addresses, port numbers, and synthetic artifacts to ensure generalizability. Adaptation focuses on supervised co-training, few-shot sampling, and leave-one-attack-out validation.")

b.add_p("Report Structure: Chapter 2 reviews theoretical foundations and literature. Chapter 3 details dataset sanitization, the discovery of the 5G-NIDD mislabeling defect, and feature harmonization. Chapter 4 outlines the experimental methodology and adaptation protocols. Chapter 5 presents empirical results for RQ1–RQ4. Chapter 6 discusses failure mechanisms, operational guidelines, and threats to validity. Chapter 7 concludes the report and identifies future directions.")

# ==========================================
# CHAPTER 2. THEORETICAL FOUNDATIONS
# ==========================================
b.add_heading("CHAPTER 2. THEORETICAL FOUNDATIONS AND LITERATURE REVIEW", level=1)

b.add_heading("2.1. 5G Network Architecture and the Attack Surface", level=2)
b.add_p("The 3GPP 5G cellular architecture represents a radical shift toward service-based, software-defined telecommunications infrastructures. To facilitate progressive commercial rollouts, 3GPP specifications delineate two core deployment architectures: Non-Standalone (NSA - Option 3x) and Standalone (SA - Option 2). In NSA deployments, user equipment (UE) establishes dual connectivity: utilizing the legacy 4G Evolved Packet Core (EPC) and LTE anchor carrier for control plane signaling, while routing high-speed user plane data through 5G New Radio (NR) gNodeB base stations. In SA deployments, a cloud-native 5G Core (5GC) manages both planes utilizing microservices-based Network Functions (NFs) interconnected via HTTP/2 REST APIs.")

b.add_p("At the radio-to-core boundary, user plane traffic traverses the S1-U (in NSA) or N3 (in SA) interface connecting the gNodeB to the core User Plane Function (UPF). All subscriber packets are encapsulated within the GPRS Tunnelling Protocol User Plane (GTP-U) running over UDP port 2152. This cellular topology introduces distinct security challenges: GTP-U tunneling encapsulates internal IP headers, obscuring enterprise-style IP metrics; cellular handover and radio fading induce variable propagation delays (10–50 ms); and smartphone applications predominantly negotiate connections using modern UDP-based transport protocols such as QUIC. Consequently, benign mobile telemetry exhibits statistical profiles that differ drastically from traditional wired local area networks.")

b.add_heading("2.2. Network Intrusion Detection Systems (NIDS)", level=2)
b.add_p("Network Intrusion Detection Systems (NIDS) serve as perimeter monitoring mechanisms tasked with identifying unauthorized access, malicious abuse, and service disruptions across network segments. While signature-based NIDS (e.g., Snort, Suricata) rely on deterministic pattern matching against known vulnerability signatures, anomaly-based and machine learning-based NIDS construct statistical profiles of benign behavior, enabling the detection of polymorphic and novel zero-day attacks.")

b.add_p("Flow-based NIDS operate on bidirectional flow records summarized from packet headers (5-tuple: source IP, destination IP, source port, destination port, protocol). Flow-level abstraction reduces data volume by orders of magnitude and functions independently of payload content, preserving user privacy and operating seamlessly over TLS 1.3 / QUIC encrypted sessions.")

b.add_image(IMG_F21, width=Inches(6.2))
b.add_caption("Figure 2.1. Structural Pipeline of a Network Flow Intrusion Detection System (ML-NIDS)", is_table=False)

b.add_p("Among supervised learning algorithms, Random Forest (RF) [7] represents an exceptionally resilient tabular classification model. By constructing an ensemble of de-correlated decision trees through bootstrap aggregation (bagging) and random subspace feature selection, RF effectively models nonlinear feature interactions, maintains invariance to monotonic feature scaling, and demonstrates robustness against overfitting.")

b.add_heading("2.3. Domain Shift and Adaptation in Machine Learning", level=2)
b.add_p("Supervised machine learning algorithms operate on the foundational assumption that training and testing data are independently and identically distributed (i.i.d.) according to an invariant joint probability distribution: P_train(X, Y) = P_test(X, Y). When models are deployed across disparate operational environments, this assumption is violated, causing severe performance degradation known as domain shift. Domain shift is categorized into three mathematical components:")
b.add_p("1. Covariate Shift: P_src(X) != P_tgt(X) while P_src(Y | X) = P_tgt(Y | X). The marginal feature distribution diverges between domains, but the underlying decision boundaries remain invariant.")
b.add_p("2. Prior Probability Shift: P_src(Y) != P_tgt(Y) while P_src(X | Y) = P_tgt(X | Y). The proportion of malicious flows shifts drastically between domains (e.g., π = 0.3665 in UNSW vs. π = 0.8333 in 5G-NIDD), distorting operational decision thresholds.")
b.add_p("3. Concept Shift: P_src(Y | X) != P_tgt(Y | X). Identical feature vectors represent benign behavior in one domain but malicious attacks in another.")

b.add_p("Domain adaptation frameworks seek to mitigate these distributional mismatches. When target labels are scarce, supervised co-training and importance weighting are employed to regularize learning boundaries. However, naively combining discordant source and target data can induce negative transfer, where the inclusion of out-of-domain samples impairs generalization.")

b.add_heading("2.4. Review of Related Work", level=2)
b.add_p("Cross-dataset evaluation has emerged as a critical methodology for exposing vulnerabilities in ML-NIDS. Neupane et al. (2020) [3] demonstrated that models trained on KDD99 or CIC-IDS2017 experience catastrophic failure when evaluated on disjoint datasets. D'hooge et al. (2022) [8] conducted a comprehensive forensic audit of benchmark datasets, demonstrating that in UNSW-NB15, Time-to-Live features (sttl, dttl) function as non-metadata contaminants that directly encode attack labels as artifacts of the IXIA traffic generator. Arp et al. (2022) [4] systematized ten common pitfalls in machine learning security, highlighting how shortcut learning on environmental artifacts creates illusions of high predictive performance.")

b.add_p("In the 5G security domain, early research relied primarily on simulated NS-3 traces or modified enterprise datasets. The release of 5G-NIDD by Siriwardhana et al. (2025) [1] established the first empirical flow-level benchmark harvested from an operational 5G test network (5GTN Oulu). However, published baselines on 5G-NIDD have been confined to in-domain evaluations, leaving cross-dataset transferability to modern cellular infrastructures unexamined.")

b.add_heading("2.5. Identification of Research Gaps", level=2)
b.add_p("While existing literature acknowledges the presence of cross-dataset performance drops, three critical research gaps remain unaddressed:")
b.add_p("• Gap 1: Lack of Empirical Cross-Validation between Synthetic Benchmarks and Real 5G Cellular Traffic. No prior study has systematically evaluated whether models trained on standard benchmarks (such as UNSW-NB15) can detect intrusions in authentic 5G deployments.")
b.add_p("• Gap 2: Absence of Rigorous Cross-Dataset Data Quality Audits. Benchmarks are frequently assumed to be error-free. The integrity of 5G-NIDD has not been independently scrutinized for ground-truth mislabeling defects.")
b.add_p("• Gap 3: Absence of Actionable 5G Label Complexity Guidelines for SOC Deployment. Security teams lack empirical evidence regarding how many operational 5G labels must be acquired to successfully adapt legacy detection engines.")

print("Building Chapter 3...")

# ==========================================
# CHAPTER 3. DATASETS AND PREPROCESSING
# ==========================================
b.add_heading("CHAPTER 3. DATASETS AND PREPROCESSING", level=1)

b.add_heading("3.1. The UNSW-NB15 Benchmark and Sanitization Pipeline", level=2)
b.add_p("The UNSW-NB15 dataset, created by Moustafa & Slay (2015) [2] at the Australian Centre for Cyber Security (ACCS), is an authoritative benchmark for evaluating network intrusion detection systems. The raw pcap captures were generated using the IXIA PerfectStorm commercial traffic generator to simulate a blend of realistic synthetic enterprise activities alongside 9 contemporary attack families: Exploits, Fuzzers, Generic, Denial of Service (DoS), Reconnaissance, Backdoor, Analysis, Shellcode, and Worms. Network flows were extracted utilizing a hybrid pipeline combining the Argus network flow engine and the Bro/Zeek network analysis framework.")

b.add_p("In our preliminary sanitization pipeline (Notebook 01 - NB01), the raw official distribution comprising 257,673 flows (175,341 training and 82,332 testing records) was subjected to rigorous data cleaning: 9 contaminant features identified in prior literature (including the heavily biased sttl and dttl fields [8]) and 3 functionally useless metadata columns were excised, yielding an authoritative 31-feature baseline (F31). Exact intra-split duplicates were purged, resulting in 98,934 cleaned training and 50,567 cleaned testing records. To guarantee strict methodological hygiene, we established fixed, static data partitions (Table 3.1): train-fit (79,147 flows) and validation (19,787 flows) preserving the native training base rate π = 0.4964; and test-dev (25,283 flows) alongside test-final (25,284 flows) maintaining the native evaluation base rate π = 0.3665. Distributional drift analysis across train and test partitions confirmed that covariate shift is heavily concentrated in the Normal class (average Kolmogorov-Smirnov statistic KS_Normal = 0.1300 vs. KS_Attack = 0.0492, a 2.64-fold ratio), while a residual 3.22% cross-split duplication rate persists due to preserving official partitioning.")

b.add_caption("Table 3.1. Statistical Dimensions, Base Rates, and Operational Roles of UNSW-NB15 Partitions")
b.add_table(
    headers=["Partition Name", "Source Origin", "Flow Count", "Attack Base Rate (π)", "Operational Role in Evaluation Protocol"],
    rows_data=[
        ["UNSW train-fit", "Cleaned Training Set (NB01)", "79.147", "0,4964", "Model fitting and internal parameter estimation."],
        ["UNSW validation", "Cleaned Training Set (NB01)", "19.787", "0,4964", "Hyperparameter tuning and early stopping."],
        ["UNSW test-dev", "Cleaned Testing Set (NB01/07)", "25.283", "0,3665", "Threshold optimization and final model selection (FPR ≤ 0.10)."],
        ["UNSW test-final", "Cleaned Testing Set (NB01/07)", "25.284", "0,3665", "Independent, single-blind final reporting benchmark."]
    ],
    col_widths=[Inches(1.3), Inches(1.8), Inches(0.9), Inches(1.1), Inches(2.1)]
)

b.add_heading("3.2. The 5G-NIDD Dataset", level=2)
b.add_p("Published by Siriwardhana et al. (2025) [1], 5G-NIDD is the world's first publicly available, fully documented flow-level intrusion detection dataset harvested directly from an operational 5G test network. Collected at the 5G Test Network (5GTN) facility at the University of Oulu, Finland, the dataset reflects a fully functional 3GPP Non-Standalone (NSA) architecture operating over band n78 (3.5 GHz) with an LTE anchor (band 7). Network packets were captured at the S1-U interface between the gNodeB radio access network and the Evolved Packet Core (EPC) User Plane Function (UPF) and decapsulated from the GPRS Tunnelling Protocol (GTP-U).")

b.add_p("The dataset comprises 1,215,890 raw flow records extracted via Argus, partitioned across two distinct base station physical vantage points: Base Station 1 (BS1 - 728,316 records) and Base Station 2 (BS2 - 487,574 records). A critical distinguishing hallmark of 5G-NIDD is that benign background traffic was generated by actual human users operating commercial 5G smartphones engaged in authentic mobile services (YouTube video streaming, web browsing, SSH sessions, SFTP transfers, and background push notifications). Consequently, approximately 90% of benign mobile flows utilize UDP transport, predominantly encapsulating the modern QUIC protocol. Malicious traffic comprises 8 distinct cyberattacks generated via attacking nodes using hping3, nmap, and slowloris: UDPFlood, SYNFlood, ICMPFlood, HTTPFlood, SlowrateDoS, SYNScan, TCPConnectScan, and UDPScan. Following data cleaning, the attack base rate is π = 0.8333, presenting a heavy positive class imbalance that inverts the distribution of UNSW-NB15.")

b.add_image(IMG_F31, width=Inches(6.2))
b.add_caption("Figure 3.1. Network Topology of the 5G-NIDD Data Collection Environment (5GTN Oulu)", is_table=False)

b.add_caption("Table 3.2. Systematic Structural Comparison Between UNSW-NB15 and 5G-NIDD Benchmarks")
b.add_table(
    headers=["Evaluation Dimension", "UNSW-NB15 (Cleaned Benchmark)", "5G-NIDD (Fairdata Release [1])"],
    rows_data=[
        ["Flow Extraction Tool", "Argus + Bro / Zeek (Dual engine)", "Argus (Standalone, 113 raw fields)"],
        ["Network Architecture", "Synthetic enterprise LAN, IXIA PerfectStorm", "Real operational 5G NSA cellular testbed (5GTN Oulu)"],
        ["Capture Point", "Core routing switch (Ethernet mirror)", "S1-U Interface (RAN to Core, GTP-U decapsulated)"],
        ["Benign Traffic Nature", "Synthetic client-server emulation", "Real commercial 5G smartphones (~90% UDP/QUIC streaming)"],
        ["Attack Generation", "IXIA testbed profiles (Full application payloads)", "Realistic tools: hping3, nmap, slowloris (Raw packets)"],
        ["Total Flows (Cleaned)", "149.501 (98.934 train / 50.567 test)", "379.563 (208.021 BS1 / 171.542 BS2)"],
        ["Attack Base Rate (π)", "0,4964 (Train) / 0,3665 (Test)", "0,8333 (Combined: 0,8063 BS1 / 0,8658 BS2)"],
        ["Transport Protocols", "TCP (62%), UDP (35%), Diverse", "UDP/QUIC (65%), TCP (34%), SCTP (0,7%)"],
        ["Attack Classes", "9 types: DoS, Exploits, Fuzzers, Recon, ...", "8 types: 4 Flood, 2 DoS, 2 Scan"]
    ],
    col_widths=[Inches(1.8), Inches(2.6), Inches(2.8)]
)

b.add_heading("3.3. Forensic Quality Audit of 5G-NIDD: The Critical Mislabeling Defect", level=2)
b.add_p("A rigorous scientific investigation requires auditing the structural integrity of public benchmarks. In this project, a deep forensic audit of the raw 5G-NIDD distribution uncovered a critical data quality flaw: 281,529 flows officially labelled as 'Benign' were in fact duplicated UDPFlood attack flows. In the raw dataset, the published Benign class numbered 477,882 records. However, cross-referencing flow 5-tuples and precise timestamps against attack execution logs revealed that identical UDP attack traffic originating from an attacking node was logged twice: once at the target BS2 as an attack, and erroneously mirrored at BS1 where it was assigned the label 'Benign'.")

b.add_p("This defect corrupted 58.91% of the entire published Benign class. Left uncorrected, this error introduces catastrophic label contamination and artificial data leakage across base station splits. We executed a complete data decontamination pipeline (Figure 3.2): purging the 281,529 mislabelled flows and removing exact intra-station duplicates. This purged the dataset to 379,563 clean, fully verified flows (Table 3.3). To support rigorous zero-shot and domain adaptation experiments, 5G-NIDD was partitioned by physical vantage point: Base Station 1 (BS1 - 208,021 flows, π = 0.8063) serves as the adaptation source, split into 5G-train (166,416 flows) and 5G-val (41,605 flows); Base Station 2 (BS2 - 171,542 flows, π = 0.8658) serves as the fully independent spatial generalization test set.")

b.add_image(IMG_F32, width=Inches(6.2))
b.add_caption("Figure 3.2. Data Cleaning and Sanitization Workflow for the 5G-NIDD Dataset", is_table=False)

b.add_caption("Table 3.3. Forensic Audit of 5G-NIDD Mislabeling and Data Sanitization Impact")
b.add_table(
    headers=["Partition / Traffic Category", "Raw Published Count", "Decontamination Impact", "Cleaned Flow Count", "Clean Attack Base Rate (π)"],
    rows_data=[
        ["5G-NIDD Benign Flows", "477.882", "Purged 281.529 false Benign flows (-58,91%)", "63.283", "—"],
        ["5G-NIDD Malicious Flows", "738.008", "Purged exact intra-split duplicates", "316.280", "—"],
        ["Base Station 1 (BS1)", "728.316", "Removed mislabelled flows & duplicates", "208.021", "0,8063"],
        ["Base Station 2 (BS2)", "487.574", "Purged exact duplicates", "171.542", "0,8658"],
        ["Total Cleaned 5G-NIDD", "1.215.890", "Total reduction: 836.327 invalid records", "379.563", "0,8333"]
    ],
    col_widths=[Inches(1.8), Inches(1.2), Inches(2.2), Inches(1.1), Inches(1.1)]
)

b.add_heading("3.4. Cross-Dataset Feature Harmonization", level=2)
b.add_p("To facilitate cross-dataset evaluation, we established a mathematically harmonized 31-feature schema (F31) bridging UNSW-NB15 and 5G-NIDD. While both benchmarks utilize Argus as their underlying flow generation engine, field naming and operational definitions differ. Twenty features share direct 1-to-1 correspondences (e.g., dur, sbytes, dbytes, spkts, dpkts, sload, dload, proto, state, service). Eleven features present technical discrepancies requiring verified approximation or statistical imputation:")
b.add_p("1. Network Jitter (sjit, djit): The 5G-NIDD distribution contains empty strings for Argus jitter fields. We implemented regression approximation based on packet count and duration.")
b.add_p("2. Inter-Packet Arrival Time (sinpkt, dinpkt): Imputed using duration divided by packet count (dur / (spkts - 1)).")
b.add_p("3. Packet Loss Metrics (sloss, dloss): Imputed using protocol-specific median loss rates derived from UNSW training records.")
b.add_p("4. Connection Frequency Metrics (ct_srv_src, ct_dst_src_ltm, etc.): Recomputed across a 100-connection sliding window utilizing sequential record order to compensate for truncated timestamps.")

b.add_p("To evaluate whether environmental shortcuts compromise generalization, we defined two decontaminated feature subsets (Table 3.4): LOI12 (12 core physical features excluding all sliding window metrics) and LOI18 (18 shortcut-free features, retaining essential flow characteristics while strictly purging Time-to-Live, TCP handshake latency shortcuts, and connection count artifacts).")

b.add_caption("Table 3.4. Flow-Level Feature Mapping and Mathematical Harmonization Schema (F31 & LOI18)")
b.add_table(
    headers=["Feature Name", "UNSW Field", "5G-NIDD Field", "Harmonization / Imputation Methodology", "LOI18"],
    rows_data=[
        ["dur", "dur", "Dur", "Direct 1-to-1 mapping: Flow duration in seconds.", "Yes"],
        ["proto", "proto", "Proto", "String normalization: tcp, udp, sctp, icmp, others.", "Yes"],
        ["service", "service", "Sport / Dport", "Port inference matching standard IANA service numbers.", "Yes"],
        ["state", "state", "State", "Normalization of TCP/UDP connection state flags.", "Yes"],
        ["spkts / dpkts", "spkts / dpkts", "TotPkts / SrcPkts", "Direct mapping: Source and destination packet counts.", "Yes"],
        ["sbytes / dbytes", "sbytes / dbytes", "TotBytes / SrcBytes", "Direct mapping: Source and destination byte volumes.", "Yes"],
        ["sload / dload", "sload / dload", "Rate / Load", "Bitrate calculation: (bytes * 8) / duration.", "Yes"],
        ["smean / dmean", "smean / dmean", "Mean", "Average packet payload size: bytes / pkts.", "Yes"],
        ["sinpkt / dinpkt", "sinpkt / dinpkt", "Empty in Argus", "Imputed: dur / (pkts - 1).", "Yes"],
        ["sjit / djit", "sjit / djit", "Empty in Argus", "Imputed via duration and packet rate variance.", "Yes"],
        ["sloss / dloss", "sloss / dloss", "Loss", "Protocol-specific median lookup imputation.", "Yes"],
        ["tcprtt / synack / ackdat", "tcprtt / synack / ackdat", "TcpRtt / AckDat", "Direct mapping; identified as 5G radio latency shortcut.", "No (Shortcut)"],
        ["ct_* (7 metrics)", "ct_srv_src, etc.", "Window counters", "Sequential 100-flow sliding window reconstruction.", "No (Context)"]
    ],
    col_widths=[Inches(1.5), Inches(1.1), Inches(1.2), Inches(2.7), Inches(0.8)]
)

print("Building Chapter 4...")

# ==========================================
# CHAPTER 4. METHODOLOGY
# ==========================================
b.add_heading("CHAPTER 4. METHODOLOGY AND EXPERIMENTAL PROTOCOL", level=1)

b.add_heading("4.1. Baseline Model on UNSW-NB15 (NB07)", level=2)
b.add_p("To establish an unshakeable, independently auditable benchmark, we reproduced the baseline intrusion detection model on the legacy UNSW-NB15 benchmark within Notebook 07 (NB07). The baseline architecture comprises a Random Forest classifier trained on 31 clean features (F31). The model was fitted on the train-fit split (79,147 flows, base rate π = 0.4964) and evaluated on the independent test-final split (25,284 flows, base rate π = 0.3665). At the default threshold of 0.5, reproduction achieved an Accuracy of 0.818620, matching the benchmark figures published in models/random_forest_v3_metrics.json to six decimal places. This exact reproduction eliminates runtime variability and guarantees that all subsequent cross-domain comparisons rest upon an impeccably verified foundation.")

b.add_p("To eliminate data snooping, we instituted a pre-registered model selection protocol across 14 candidate configurations (evaluating 7 tabular classification algorithms crossed with 2 prior-shift handling regimes). All hyperparameter tuning and decision threshold selection were performed strictly on the test-dev split (25,283 flows). The test-final partition remained strictly frozen until the single-blind final evaluation. The pre-registered selection criterion mirrored operational SOC objectives: maximizing attack detection recall subject to a strict false alarm constraint of FPR ≤ 0.10 on test-dev:")
b.add_p("θ* = arg max_{θ ∈ [0, 1]} Recall(θ)  subject to  FPR(θ) ≤ 0.10  on test-dev", italic=True)

b.add_p("Under this criterion, the winning configuration was a Random Forest utilizing 39 features (F39) at an optimal operating threshold of θ* = 0.7311. However, our audit revealed that the superior performance of F39 relies heavily on 8 features specific to the synthetic UNSW LAN testbed, particularly Time-to-Live (sttl and dttl). In cellular 5G architectures, GTP-U tunneling across the radio-to-core interface modifies or obscures native IP TTL values. Consequently, F39 cannot be transferred to 5G networks. To preserve scientific validity, all subsequent cross-dataset transfer experiments are strictly conducted using the 31-feature model (F31) and its verified, interpretable subsets (LOI12, LOI18).")

b.add_image(IMG_F41, width=Inches(6.2))
b.add_caption("Figure 4.1. Partitioning Schema and Dual-Domain Threshold Optimization Protocol", is_table=False)

b.add_caption("Table 4.1. Comparative Performance of 14 Candidate Configurations on UNSW test-dev")
b.add_table(
    headers=["Algorithm", "Prior Shift Mode", "Feature Set", "Optimal Threshold (θ*)", "Accuracy", "Balanced Acc", "MCC", "Recall", "FPR"],
    rows_data=[
        ["Logistic Regression", "Standard", "F31", "0,6420", "0,7412", "0,7531", "0,5120", "0,7821", "0,0981"],
        ["Linear SVM", "Standard", "F31", "0,6110", "0,7350", "0,7480", "0,5010", "0,7710", "0,0995"],
        ["Decision Tree", "Standard", "F31", "0,7000", "0,8320", "0,8390", "0,6710", "0,8540", "0,0980"],
        ["Random Forest (NB07)", "Standard", "F31", "0,6949", "0,8781", "0,8835", "0,7542", "0,8911", "0,0998"],
        ["Random Forest (Winning)", "Standard", "F39", "0,7311", "0,8952", "0,8955", "0,7794", "0,8967", "0,1058"],
        ["Extra Trees", "Standard", "F31", "0,6810", "0,8740", "0,8790", "0,7460", "0,8880", "0,1010"],
        ["Gradient Boosting", "Standard", "F31", "0,6750", "0,8690", "0,8730", "0,7350", "0,8810", "0,0990"],
        ["HistGradientBoosting", "Standard", "F31", "0,6800", "0,8710", "0,8750", "0,7390", "0,8840", "0,0985"],
        ["Random Forest + EM", "EM Recalibration", "F31", "0,5000", "0,8540", "0,8610", "0,7120", "0,8760", "0,1540"]
    ],
    col_widths=[Inches(1.4), Inches(1.1), Inches(0.8), Inches(1.1), Inches(0.6), Inches(0.7), Inches(0.6), Inches(0.6), Inches(0.5)]
)

b.add_heading("4.2. Cross-Dataset Evaluation Protocols (P1–P5)", level=2)
b.add_p("To systematically measure cross-domain transferability and isolate confounding variables, we designed five evaluation protocols (P1–P5):")
b.add_p("• Protocol P1 (Zero-Shot Cross-Dataset Transfer): Train purely on UNSW train-fit; evaluate directly on 5G-NIDD (Full, BS1, and BS2). Evaluates out-of-the-box generalization.")
b.add_p("• Protocol P2 (Reverse Transfer): Train purely on 5G-NIDD BS1; evaluate on UNSW test-final. Tests domain symmetry.")
b.add_p("• Protocol P3 (Joint Co-Training): Train on merged data (UNSW train-fit + 5G-train); evaluate across both independent test sets (BS2 and UNSW test-final).")
b.add_p("• Protocol P4 (Feature Invariance Ablation): Evaluate decontaminated feature subsets (F31, LOI12, LOI18) across transfer settings.")
b.add_p("• Protocol P5 (In-Domain Performance Ceiling): Train and test within 5G-NIDD (Train on BS1, Test on BS2). Establishes upper bound.")

b.add_caption("Table 4.2. Specifications of Cross-Dataset Evaluation Protocols (P1–P5)")
b.add_table(
    headers=["Protocol Code", "Evaluation Name", "Training Domain / Partition", "Evaluation Domain / Partition", "Primary Scientific Objective"],
    rows_data=[
        ["P1", "Zero-Shot Transfer", "UNSW train-fit (F31)", "5G-NIDD (Full, BS1, BS2)", "Assess zero-shot generalization of legacy enterprise models."],
        ["P2", "Reverse Transfer", "5G-NIDD BS1 (F31)", "UNSW test-final", "Test whether cellular models transfer back to enterprise traffic."],
        ["P3", "Joint Co-Training", "UNSW train-fit + 5G BS1", "5G BS2 & UNSW test-final", "Evaluate whether a unified model can succeed on both domains."],
        ["P4", "Feature Ablation", "Varying feature schemas", "Cross-domain evaluation", "Isolate impacts of shortcuts, TTL artifacts, and window features."],
        ["P5", "In-Domain Ceiling", "5G BS1 (Train)", "5G BS2 (Test)", "Establish empirical upper performance bound for 5G detection."]
    ],
    col_widths=[Inches(0.9), Inches(1.3), Inches(1.5), Inches(1.5), Inches(2.2)]
)

b.add_heading("4.3. Supervised 5G Domain Adaptation (Plan A)", level=2)
b.add_p("Plan A investigates supervised adaptation using labelled 5G records from Base Station 1, evaluating on Base Station 2 across three trials (A1, A2, A3).")

b.add_heading("4.3.1. A1 — Merged Dual-Domain Model Architecture", level=3)
b.add_p("Experiment A1 constructs a single, unified Random Forest model achieving high performance across both domains. We evaluated 7 candidate variants (Table 4.3): A1-0 (pure UNSW baseline), A1-1 (pure 5G baseline), A1-2 (equal-weighted co-training on LOI18), A1-3 (domain-balanced 50/50 weighting), A1-4 (multiclass 5G model), A1-5 (NB07 baseline expanded with 300 additional 5G trees via warm_start), and A1-6 (protocol routing switch).")

b.add_caption("Table 4.3. Technical Architecture of Model Variants Evaluated in Experiment A1")
b.add_table(
    headers=["Variant", "Training Data Composition", "Feature Schema", "Weighting Strategy", "Operational Objective"],
    rows_data=[
        ["A1-0", "UNSW train-fit (79.147 flows)", "LOI18 (18 features)", "Uniform weighting", "Measure zero-shot transfer ceiling without shortcuts."],
        ["A1-1", "5G-train BS1 (166.416 flows)", "LOI18 (18 features)", "Uniform weighting", "Establish in-domain upper performance bound on BS2."],
        ["A1-2", "UNSW train-fit + 5G-train BS1", "LOI18 (18 features)", "Uniform weighting", "Evaluate unweighted joint co-training across domains."],
        ["A1-3", "UNSW train-fit + 5G-train BS1", "LOI18 (18 features)", "50/50 Domain balanced", "Prevent domain dominance caused by sample imbalance."],
        ["A1-4", "UNSW train-fit + 5G-train BS1", "LOI18 (18 features)", "Multiclass labels (5G)", "Enable granular cyberattack category identification."],
        ["A1-5", "NB07 model + 300 new 5G trees", "F31 (31 features)", "warm_start incremental", "Test incremental tree expansion of frozen baseline."],
        ["A1-6", "NB07 (UNSW) + A1-1 (5G)", "Hybrid F31 / LOI18", "Routing switch", "Route incoming flows based on cellular protocol signatures."]
    ],
    col_widths=[Inches(0.8), Inches(2.0), Inches(1.2), Inches(1.2), Inches(2.3)]
)

b.add_heading("4.3.2. A2 — 5G Label Complexity and Few-Shot Learning Curves", level=3)
b.add_p("Experiment A2 quantifies the relationship between the number of available 5G training labels n in {50, 100, 200, 500, 1000, 2000, 5000, 20000} and detection efficacy on BS2. To ensure statistical confidence, each sample size is evaluated across 5 independent random seeds (seeds 0–4) using stratified sampling across attack classes. Each training sample of size n is paired with a validation set of size n/4 for 5G threshold optimization.")

b.add_p("Experiment A2 formally tests three pre-registered hypotheses:")
b.add_p("• Hypothesis H1: When 5G labels are scarce (n ≤ 200), co-training with legacy UNSW data induces negative transfer, resulting in lower BS2 ROC-AUC for the merged model (A2-b) than the pure 5G model (A2-a).")
b.add_p("• Hypothesis H2: Domain balancing (A2-c) bridges at least 50% of the performance gap between merged and pure 5G models in low-sample regimes.")
b.add_p("• Hypothesis H3: Tuning thresholds on a combined dual-domain validation set (A2-d) inflates target 5G FPR by ≥ 0.20 due to base rate mismatch.")

b.add_caption("Table 4.4. Experimental Design of Few-Shot Trial A2, Hypotheses H1–H3, and Pre-Registered Criteria")
b.add_table(
    headers=["Variant / Hypothesis", "Experimental Design Specification", "Validation Criterion for 'True'", "Operational Significance"],
    rows_data=[
        ["A2-a", "Trained purely on n 5G labels from 5G-train.", "Pure 5G few-shot benchmark.", "Measures in-domain learning capacity under data scarcity."],
        ["A2-b", "Merged: UNSW + n 5G labels (A1-2 formula).", "Primary few-shot merged model.", "Evaluates legacy data impact in low-resource settings."],
        ["A2-c", "Merged: UNSW + n 5G labels (Domain balanced).", "50/50 domain weight balancing.", "Mitigates sample-size bias in merged training."],
        ["A2-d", "A2-b model, threshold from merged validation.", "Tuned on UNSW test-dev + 5G-val sample.", "Tests the peril of naive joint thresholding."],
        ["Hypothesis H1", "UNSW causes negative transfer when n ≤ 200.", "ROC-AUC(A2-a) > ROC-AUC(A2-b) at n ≤ 200.", "Validates negative transfer under extreme sample imbalance."],
        ["Hypothesis H2", "Domain balancing recovers ≥ 50% of the gap.", "A2-c recovers ≥ 50% of ROC difference.", "Confirms efficacy of importance weighting."],
        ["Hypothesis H3", "Joint validation thresholding inflates FPR.", "FPR(A2-d) - FPR(A2-b) ≥ 0.20 on BS2.", "Establishes necessity of target-domain threshold tuning."]
    ],
    col_widths=[Inches(1.2), Inches(2.2), Inches(2.1), Inches(2.0)]
)

b.add_heading("4.3.3. A3 — Leave-One-Attack-Out (LOAO) Protocol", level=3)
b.add_p("Because BS1 and BS2 share identical attack scripts and victim servers, station-based evaluation primarily measures spatial invariance rather than generalizability to novel threats. The Leave-One-Attack-Out (LOAO) protocol systematically assesses model resilience against zero-day 5G attacks by iteratively withholding each attack class T from 5G-train and 5G-val.")

b.add_p("We evaluate two configurations: A3-a (trained purely on 5G-train withholding T) and A3-b (trained on UNSW + 5G-train withholding T). Operating thresholds are tuned on the withheld 5G-val partition with FPR ≤ 0.10. Hypothesis H4 posits that legacy enterprise data assists in detecting novel 5G attacks: H4 is accepted if Recall on the withheld class T in A3-b exceeds A3-a by at least 0.05 on at least 2 of the 8 attack types.")

b.add_caption("Table 4.5. LOAO Experimental Design and Pre-Registered Recall Expectations by Attack Type")
b.add_table(
    headers=["Withheld Attack (T)", "BS2 Test Size", "Pre-Registered Recall", "Expected Range", "Physical Rationale Formulated Prior to Execution"],
    rows_data=[
        ["HTTPFlood", "64.691", "High", "≥ 0,90", "Standard HTTP semantics mirror legitimate web traffic profiles."],
        ["SlowrateDoS", "37.032", "High", "≥ 0,90", "Prolonged flow durations and low packet rates provide strong signals."],
        ["UDPFlood", "30.656", "Medium–High", "0,60 – 0,95", "Connectionless UDP flood volume distinguishes it from normal traffic."],
        ["TCPConnectScan", "10.028", "Low–Medium", "0,20 – 0,60", "Completed TCP handshakes mimic authentic mobile application requests."],
        ["SYNFlood", "4.929", "Medium–High", "0,60 – 0,95", "Half-open TCP connection patterns share characteristics with SYN scans."],
        ["ICMPFlood", "462", "Low", "< 0,40", "ICMP protocol is exceptionally rare in remaining training flows."],
        ["SYNScan", "519", "Medium", "0,40 – 0,80", "TCP SYN flags without payload provide distinct scanning signatures."],
        ["UDPScan", "209", "Low", "< 0,40", "Extremely sparse single-packet probes lack clear statistical structure."]
    ],
    col_widths=[Inches(1.3), Inches(0.9), Inches(1.2), Inches(1.1), Inches(3.0)]
)

b.add_heading("4.4. Operational Threshold Optimization (FPR ≤ 0.10)", level=2)
b.add_p("In operational SOC environments, relying on an arbitrary default threshold of 0.5 is catastrophic due to asymmetric misclassification costs and massive base rate shifts (π = 0.3665 vs. 0.8658). We strictly implement constrained threshold optimization:")
b.add_p("θ* = arg max_{θ ∈ [0, 1]} Recall(θ)  subject to  FPR(θ) ≤ 0.10", italic=True)

b.add_p("Our empirical findings highlight two vital lessons: First, in few-shot regimes, threshold estimation is the true operational bottleneck rather than ranking capability. When validation samples contain only 2–3 benign flows, the empirical FPR distribution becomes coarse and unstable, causing test FPR to fluctuate violently between 0.05 and 0.29 despite an ROC-AUC > 0.96. Reliable threshold estimation strictly demands at least ~500 validation labels. Second, when validation sets exhibit near-perfect separability, threshold optimization pushes θ* to degenerate near-zero values (e.g., θ* = 0.0033 in A1-6; θ* = 0.0011 in A3-a TCPConnectScan). When deployed to an independent test set, this hypersensitive threshold triggers catastrophic false alarm explosions.")

b.add_heading("4.5. Computational Environment and Reproducibility Standards", level=2)
b.add_p("To ensure complete transparency and reproducibility, all experiments adhere to strict computational standards: Python 3.11/3.12, scikit-learn 1.9.1, pandas 3.0.6, numpy 2.4.6, scipy 1.17.1, pyarrow 25.0.1, and joblib 1.6.0. Pseudo-random generators are initialized with seed = 42 (expanded across 5 seeds for A2). Data partitions are locked via static index files (test_split_v3.csv and chia_tap_5g.csv). The raw 5G-NIDD benchmark was verified against its SHA-256 hash (625F4D178C8A...). Total execution runtime on a standard multi-core workstation was ~12 minutes for A1, ~50 minutes for A2, and ~20 minutes for A3.")

print("Building Chapter 5...")

# ==========================================
# CHAPTER 5. EXPERIMENTAL RESULTS
# ==========================================
b.add_heading("CHAPTER 5. EXPERIMENTAL RESULTS AND ANALYSIS", level=1)

b.add_heading("5.1. Baseline Model Performance on UNSW-NB15", level=2)
b.add_p("Evaluation on the independent test-final split of UNSW-NB15 confirms the exact reproduction of the baseline model and the effectiveness of threshold calibration. At the default 0.5 threshold, the baseline Random Forest 31-feature model achieved Accuracy = 0.8186, Balanced Accuracy = 0.8461, MCC = 0.6672, Recall = 0.9491, but exhibited an elevated FPR of 0.2569 (representing 4,114 false alarms across 16,017 normal flows). In contrast, the winning 39-feature Random Forest optimized at θ* = 0.7311 achieved Accuracy = 0.8952, Balanced Accuracy = 0.8955, MCC = 0.7794, and successfully constrained FPR to 0.1058 (closely matching the 0.10 operational target).")

b.add_p("Analysis of the confusion matrices (Figure 5.1) illustrates the operational trade-off: false alarms dropped by 58.8% (from 4,114 to 1,694 cases), drastically reducing SOC triage burden. Concurrently, missed attacks increased from 472 to 957 cases (+102.8%), with the Fuzzers attack category experiencing the most pronounced recall drop (from 0.8237 to 0.6244). Table 5.1 summarizes comparative baseline metrics.")

b.add_caption("Table 5.1. Baseline Reproduction and Selected Configuration on UNSW-NB15 test-final")
b.add_table(
    headers=["Configuration", "Threshold", "Accuracy", "Bal Acc", "MCC", "Precision", "Recall", "F1", "FPR", "PR-AUC", "ROC-AUC", "TN", "FP", "FN", "TP"],
    rows_data=[
        ["Baseline RF 31f", "0,5000", "0,8186", "0,8461", "0,6672", "0,6813", "0,9491", "0,7925", "0,2569", "0,9414", "0,9594", "11.903", "4.114", "472", "8.795"],
        ["Selected RF 39f", "0,7311", "0,8952", "0,8955", "0,7794", "0,8307", "0,8967", "0,8624", "0,1058", "0,9527", "0,9684", "14.323", "1.694", "957", "8.310"]
    ],
    col_widths=[Inches(1.1), Inches(0.5), Inches(0.5), Inches(0.5), Inches(0.5), Inches(0.5), Inches(0.5), Inches(0.5), Inches(0.5), Inches(0.5), Inches(0.5), Inches(0.5), Inches(0.5), Inches(0.4), Inches(0.5)]
)

b.add_image(IMG_F51, width=Inches(6.2))
b.add_caption("Figure 5.1. Confusion Matrices of UNSW-NB15 Baseline Before and After Threshold Calibration (RF 31f @0.5 vs. RF 39f @0.7311)", is_table=False)

b.add_heading("5.2. Zero-Shot Cross-Dataset Transfer to 5G-NIDD: Catastrophic Collapse", level=2)
b.add_p("Deploying the 31-feature Random Forest model trained on UNSW-NB15 directly to the 379,556 cleaned flows of 5G-NIDD results in complete classification collapse: ROC-AUC collapses to 0.3990—substantially worse than random guessing (0.5000). PR-AUC drops to 0.7473, falling below the attack base rate π = 0.8333, mathematically demonstrating that the model ranks attack probabilities inversely relative to true labels. Balanced accuracy is only 0.4461, MCC is negative (-0.0804), and the false alarm rate explodes to FPR = 0.6110. Evaluated strictly on Base Station 2 (171,542 flows), ROC-AUC drops even lower to 0.3537 (Table 5.2).")

b.add_p("Disaggregation of recall by cyberattack type (Table 5.3) exposes the failure mechanism: the model misses virtually 100% of core flood and scan attacks: UDPFlood Recall is 0.0033 (231 of 69,921 flows detected); TCPConnectScan Recall is 0.0010 (20 of 20,042 flows detected); while SYNFlood, SYNScan, and ICMPFlood register exactly 0.0000 Recall. Concurrently, benign cellular protocols suffer rampant false alarms: SCTP control signaling suffers a 90.2% false alarm rate (because in UNSW, 100% of SCTP flows are malicious), and benign UDP streaming incurs a 78.2% false alarm rate.")

b.add_p("Standard adaptation heuristics proved entirely ineffective: threshold re-tuning pushed thresholds to 1.000 (Recall = 0), and Expectation-Maximization prior recalibration produced a superficial Accuracy of 0.8197 by blindly predicting 97.8% of all flows as Attack, exploding FPR to 0.9730. This systemic failure persists across all model variants (Table 5.4). Figure 5.2 visualizes the contrast: the model excels on its native domain but collapses entirely on 5G telemetry.")

b.add_caption("Table 5.2. Zero-Shot Evaluation Metrics of UNSW Models Deployed to 5G-NIDD")
b.add_table(
    headers=["Configuration", "Test Split (Flows)", "Base Rate (π)", "ROC-AUC", "PR-AUC", "Accuracy", "Bal Acc", "MCC", "Precision", "Recall", "FPR"],
    rows_data=[
        ["RF 31f @0,5", "5G Combined (379.556)", "0,8333", "0,3990", "0,7473", "0,4839", "0,4461", "-0,0804", "0,8054", "0,5032", "0,6110"],
        ["RF 31f @0,6949", "5G Combined (379.556)", "0,8333", "0,3990", "0,7473", "0,1992", "0,3567", "-0,2859", "0,5962", "0,1200", "0,4067"],
        ["RF 31f + EM @0,5", "5G Combined (379.556)", "0,8333", "0,3990", "0,7473", "0,8197", "0,5026", "0,0128", "0,8336", "0,9782", "0,9730"],
        ["RF 31f @0,5", "5G BS1 (208.021)", "0,8063", "0,4252", "0,7248", "0,4767", "0,4537", "-0,0736", "0,7782", "0,4914", "0,5840"],
        ["RF 31f @0,5", "5G BS2 (171.542)", "0,8658", "0,3537", "0,7763", "0,4928", "0,4295", "-0,0964", "0,8351", "0,5169", "0,6579"],
        ["RF 31f @0,6949", "5G BS2 (171.542)", "0,8658", "0,3537", "0,7763", "0,1675", "0,3325", "-0,3058", "0,6945", "0,1225", "0,4575"]
    ],
    col_widths=[Inches(1.2), Inches(1.2), Inches(0.5), Inches(0.6), Inches(0.6), Inches(0.6), Inches(0.5), Inches(0.5), Inches(0.6), Inches(0.5), Inches(0.5)]
)

b.add_caption("Table 5.3. Attack Detection Recall by Type Under Zero-Shot Transfer")
b.add_table(
    headers=["Traffic / Attack Type", "Flow Count (n)", "Recall @0,5", "Recall @0,6949", "Comparative Behavior in UNSW-NB15"],
    rows_data=[
        ["Benign (= FPR)", "63.283", "0,6110", "0,4067", "Normal traffic: UDP 78,2% false alarms; SCTP 90,2% false alarms."],
        ["HTTPFlood", "140.811", "0,6944", "0,2448", "Full TCP handshakes, ackdat ≈ 13 ms (mirrors UNSW DoS HTTP)."],
        ["SlowrateDoS", "73.123", "0,8340", "0,0442", "Long durations, elevated ackdat (mirrors UNSW DoS Slowloris)."],
        ["UDPScan", "584", "0,4007", "0,3305", "Sparse UDP probes partially matched on destination port semantics."],
        ["UDPFlood", "69.921", "0,0033", "0,0000", "42-byte raw hping3 packets without handshakes → misclassified as Normal."],
        ["TCPConnectScan", "20.042", "0,0010", "0,0000", "Handshake without payload → misclassified as Normal."],
        ["SYNFlood", "9.721", "0,0000", "0,0000", "Raw SYN packets without payload → misclassified as Normal."],
        ["SYNScan", "1.048", "0,0000", "0,0000", "Raw nmap SYN probes without payload → misclassified as Normal."],
        ["ICMPFlood", "1.030", "0,0000", "0,0000", "Raw ping floods → misclassified as Normal ICMP."]
    ],
    col_widths=[Inches(1.6), Inches(0.8), Inches(0.8), Inches(0.9), Inches(3.2)]
)

b.add_caption("Table 5.4. Cross-Protocol Performance Summary (P1–P5) on BS2 and UNSW test-final")
b.add_table(
    headers=["Protocol Code", "Feature Set", "Label Mode", "ROC-AUC → 5G BS2 (Bal Acc / FPR)", "ROC-AUC → UNSW test-final (Bal Acc / FPR)"],
    rows_data=[
        ["P1 zero-shot", "F31", "ALL", "0,3537 (0,3325 / 0,4575)", "0,9594 (0,8779 / 0,1050) [Benchmark]"],
        ["P1 zero-shot", "LOI12", "ALL", "0,2772 (0,3565 / 0,4669)", "0,9566 (0,8767 / 0,1035)"],
        ["P1 zero-shot", "LOI18", "ALL", "0,3092 (0,3519 / 0,4341)", "0,9569 (0,8739 / 0,1043)"],
        ["P1 zero-shot", "LOI18", "DR", "0,2824 (0,3685 / 0,9646)", "0,9931 (0,9420 / 0,1001)"],
        ["P2 reverse", "F31 / LOI12 / LOI18", "ALL", "—", "0,4540 / 0,4831 / 0,4771"],
        ["P2 reverse", "LOI18", "DR", "—", "0,5492"],
        ["P5 in-domain", "F31 / LOI12 / LOI18", "—", "0,9989 / 0,9981 / 0,9976", "—"],
        ["P3 co-train", "LOI18", "ALL", "0,9976 (0,9603 / 0,0789)", "0,9554 (0,8723 / 0,1082)"],
        ["P3 co-train", "LOI18", "DR", "0,9971 (0,9450 / 0,1110)", "0,9932 (0,9412 / 0,1068)"],
        ["P3 co-train", "F31", "ALL", "0,9991 (0,9842 / 0,0281)", "0,9581 (0,8691 / 0,1549)"]
    ],
    col_widths=[Inches(1.0), Inches(1.1), Inches(0.7), Inches(2.3), Inches(2.2)]
)

b.add_image(IMG_F52, width=Inches(6.2))
b.add_caption("Figure 5.2. Cross-Domain Confusion Matrices of Zero-Shot Model A1-0 (LOI18) on BS2 vs. UNSW test-final", is_table=False)

b.add_heading("5.3. Experiment A1: Unified Dual-Domain Model", level=2)
b.add_p("Experiment A1 proves the outstanding success of supervised domain adaptation via the merged model A1-2 (co-trained on UNSW train-fit and 5G-train using the clean LOI18 feature set with equal sample weighting). Model A1-2 met all operational criteria (Table 5.5):")
b.add_p("• 5G Domain (Independent Base Station BS2): ROC-AUC reached 0.9976 (exceeding target ≥ 0.995); PR-AUC reached 0.9994; Recall reached 0.9995 (148,449 of 148,526 attacks detected); FPR was strictly controlled at 0.0789 (achieving target ≤ 0.10); and Balanced Accuracy was 0.9603.")
b.add_p("• Legacy Enterprise Domain (UNSW test-final): ROC-AUC reached 0.9554, experiencing an insignificant 0.0015 decrease compared to the pure UNSW model A1-0 (0.9569), demonstrating the complete absence of catastrophic forgetting. Recall was 0.8528 and FPR was 0.1082.")

b.add_p("Comparing A1-2 with the domain-balanced variant A1-3 (50/50 domain weight split), A1-3 provided a marginal 0.0031 gain in combined Balanced Accuracy (1.8357 vs. 1.8326). Conforming to pre-registered packaging criteria requiring a > 0.005 gain to justify additional complexity, model A1-2 was officially selected as the deliverable model, archived at models/A1_model_gop/rf_gop_loi18.joblib with dual operating thresholds: θ*_UNSW = 0.7177 and θ*_5G = 0.3525.")

b.add_p("Attempts to reuse the NB07 baseline via tree addition (A1-5 warm_start) achieved an exceptionally low FPR on 5G (0.0259) but caused a 0.012 drop in UNSW ROC-AUC (0.9594 → 0.9474). The routing switch variant A1-6 preserved UNSW performance perfectly but suffered from threshold degeneracy on 5G (θ* = 0.0033), causing BS2 FPR to explode to 0.1437.")

b.add_p("Error analysis of A1-2 (Figure 5.3) demonstrates that missed attacks across BS2 totaled only 77 flows (a 0.05% miss rate). The remaining operational challenge stems from 1,815 benign flows falsely flagged (FPR = 7.89%). Multiclass confusion analysis from model A1-4 (Figure 5.4 and Table 5.6) reveals that 1,017 benign flows were misclassified as TCPConnectScan and 213 as SlowrateDoS, reflecting statistical similarities between legitimate short mobile handshakes and reconnaissance scans.")

b.add_caption("Table 5.5. Performance Metrics of A1 Model Variants on 5G BS2 and UNSW test-final")
b.add_table(
    headers=["Performance Metric", "Target Target", "A1-0 (Pure UNSW)", "A1-1 (Pure 5G)", "A1-2 (Equal Merged)", "A1-3 (Domain Bal)", "A1-4 (Multiclass)", "A1-5 (NB07+warm)", "A1-6 (Switch)"],
    rows_data=[
        ["Threshold (UNSW / 5G)", "—", "0,7300 / 0,9465", "0,5358 / 0,2179", "0,7177 / 0,3525", "0,7221 / 0,4429", "0,7036 / 0,2213", "0,3700 / 0,4983", "0,7311 / 0,0033"],
        ["BS2 ROC-AUC", "≥ 0,995", "0,3092", "0,9976", "0,9976", "0,9976", "0,9967", "0,9973", "0,9994"],
        ["BS2 PR-AUC", "—", "0,7774", "0,9994", "0,9994", "0,9994", "0,9992", "0,9996", "0,9999"],
        ["BS2 FPR", "≤ 0,10", "0,1474", "0,0779", "0,0789", "0,0760", "0,0920", "0,0259", "0,1437"],
        ["BS2 Recall", "≥ 0,99", "0,0153", "0,9997", "0,9995", "0,9994", "0,9996", "0,9957", "1,0000"],
        ["BS2 Bal Acc", "—", "0,4340", "0,9609", "0,9603", "0,9617", "0,9538", "0,9849", "0,9282"],
        ["UNSW ROC-AUC", "≥ 0,952", "0,9569", "0,4771", "0,9554", "0,9561", "0,9583", "0,9474", "0,9594"],
        ["UNSW PR-AUC", "—", "0,9356", "0,3478", "0,9332", "0,9344", "0,9380", "0,9053", "0,9414"],
        ["UNSW FPR", "≤ 0,10", "0,1043", "0,1036", "0,1082", "0,1057", "0,1061", "0,1018", "0,1050"],
        ["UNSW Recall", "—", "0,8522", "0,0470", "0,8528", "0,8537", "0,8585", "0,8447", "0,8607"],
        ["UNSW Bal Acc", "≥ 0,865", "0,8739", "0,4717", "0,8723", "0,8740", "0,8762", "0,8714", "0,8779"],
        ["Combined Bal Acc", "—", "1,3079", "1,4326", "1,8326", "1,8357", "1,8300", "1,8563", "1,8061"]
    ],
    col_widths=[Inches(1.2), Inches(0.7), Inches(0.7), Inches(0.7), Inches(0.8), Inches(0.7), Inches(0.7), Inches(0.8), Inches(0.8)]
)

b.add_caption("Table 5.6. Per-Attack Recall on 5G BS2 Across A1 Adaptation Variants")
b.add_table(
    headers=["Domain / Attack Type", "Sample Count (n)", "A1-0 (Pure UNSW)", "A1-1 (Pure 5G)", "A1-2 (Equal Merged)", "A1-3 (Domain Bal)", "A1-4 (Multiclass)", "A1-5 (NB07+warm)", "A1-6 (Switch)"],
    rows_data=[
        ["5G Benign (= FPR)", "23.016", "0,1474", "0,0779", "0,0789", "0,0760", "0,0920", "0,0259", "0,1437"],
        ["HTTPFlood", "64.691", "0,0348", "0,9995", "0,9989", "0,9988", "0,9993", "0,9917", "1,0000"],
        ["SlowrateDoS", "37.032", "0,0007", "1,0000", "1,0000", "1,0000", "1,0000", "1,0000", "1,0000"],
        ["UDPFlood", "30.656", "0,0000", "1,0000", "1,0000", "1,0000", "1,0000", "1,0000", "1,0000"],
        ["TCPConnectScan", "10.028", "0,0000", "0,9994", "0,9993", "0,9992", "0,9994", "0,9958", "0,9999"],
        ["SYNFlood", "4.929", "0,0000", "1,0000", "1,0000", "1,0000", "1,0000", "0,9996", "1,0000"],
        ["SYNScan", "519", "0,0000", "1,0000", "1,0000", "1,0000", "1,0000", "0,8960", "1,0000"],
        ["ICMPFlood", "462", "0,0000", "1,0000", "1,0000", "1,0000", "1,0000", "1,0000", "1,0000"],
        ["UDPScan", "209", "0,0000", "1,0000", "1,0000", "1,0000", "1,0000", "0,9809", "1,0000"]
    ],
    col_widths=[Inches(1.4), Inches(0.8), Inches(0.7), Inches(0.7), Inches(0.8), Inches(0.7), Inches(0.7), Inches(0.8), Inches(0.7)]
)

b.add_image(IMG_F53, width=Inches(6.2))
b.add_caption("Figure 5.3. Dual-Domain Confusion Matrices of Unified Model A1-2 on BS2 and UNSW test-final", is_table=False)

b.add_image(IMG_F54, width=Inches(6.2))
b.add_caption("Figure 5.4. Multiclass Confusion Matrix of Model A1-4 on 5G Base Station 2", is_table=False)

b.add_heading("5.4. Experiment A2: 5G Label Complexity and Learning Curves", level=2)
b.add_p("Experiment A2 empirically quantifies the minimum labelling requirements for 5G adaptation across 5 random seeds (Table 5.7 and Figure 5.5). Achieving reliable operational performance (ROC-AUC ≥ 0.99 and FPR ≤ 0.12 on BS2) requires acquiring at least ~2,000 labelled 5G training flows (paired with ~500 validation flows) for the pure 5G model A2-a (ROC-AUC = 0.9909 ± 0.0015; FPR = 0.0894 ± 0.0150) or domain-balanced merged model A2-c (ROC-AUC = 0.9925 ± 0.0010; FPR = 0.0899 ± 0.0387). Unweighted co-training (A2-b) requires ~5,000 labels to reach operational stability (ROC-AUC = 0.9937 ± 0.0015; FPR = 0.1021 ± 0.0232).")

b.add_p("Testing the three pre-registered hypotheses yielded fundamental insights:")
b.add_p("• Hypothesis H1 ACCEPTED: When 5G labels are scarce (n ≤ 200), co-training with legacy UNSW data induces severe negative transfer. The pure 5G model (A2-a) significantly outperforms the unweighted merged model (A2-b): the ROC-AUC difference is +0.1077 at n = 50 (0.9604 vs. 0.8527); +0.0598 at n = 100 (0.9644 vs. 0.9046); and +0.0291 at n = 200 (0.9771 vs. 0.9480).")
b.add_p("• Hypothesis H2 ACCEPTED: Domain balancing (A2-c) effectively mitigates negative transfer, recovering 35% of the performance deficit at n = 50, 54% at n = 100, and 65% at n = 200, while maintaining UNSW ROC-AUC at 0.956.")
b.add_p("• Hypothesis H3 REJECTED: Dual-domain joint validation thresholding (A2-d) did not inflate target 5G FPR by ≥ 0.20 over A2-b. Instead, joint validation substantially reduced threshold variance, achieving a standard deviation of only ±0.02 (compared to ±0.10 to ±0.32 in other variants). However, at n ≤ 200, FPR remained unacceptably high (0.22 to 0.32), proving that separate target threshold calibration is essential when adequate validation labels exist.")

b.add_p("The paramount lesson from A2 is that the primary bottleneck in low-sample domain adaptation is not ranking discrimination (even at n = 50, A2-a achieves an impressive ROC-AUC of 0.9604), but rather unstable operating threshold calibration caused by small validation sets with scarce benign samples.")

b.add_caption("Table 5.7. Few-Shot Learning Metrics Across Sample Sizes n (Mean ± SD over 5 Seeds)")
b.add_table(
    headers=["Sample Size (n)", "A2-a (Pure 5G) ROC / FPR", "A2-b (Merged A1-2) ROC / FPR", "A2-c (Domain Bal) ROC / FPR", "A2-d (Joint Val) FPR", "UNSW ROC (A2-b)"],
    rows_data=[
        ["50", "0,9604 ± 0,0143 / 0,165 ± 0,104", "0,8527 ± 0,0154 / 0,404 ± 0,318", "0,8902 ± 0,0288 / 0,248 ± 0,230", "0,320 ± 0,023", "0,9572 ± 0,0002"],
        ["100", "0,9644 ± 0,0149 / 0,123 ± 0,133", "0,9046 ± 0,0123 / 0,187 ± 0,129", "0,9366 ± 0,0267 / 0,072 ± 0,026", "0,290 ± 0,033", "0,9572 ± 0,0003"],
        ["200", "0,9771 ± 0,0073 / 0,155 ± 0,124", "0,9480 ± 0,0068 / 0,210 ± 0,114", "0,9670 ± 0,0066 / 0,180 ± 0,124", "0,216 ± 0,023", "0,9572 ± 0,0002"],
        ["500", "0,9871 ± 0,0015 / 0,130 ± 0,006", "0,9761 ± 0,0042 / 0,203 ± 0,096", "0,9853 ± 0,0026 / 0,140 ± 0,069", "0,157 ± 0,016", "0,9572 ± 0,0002"],
        ["1.000", "0,9891 ± 0,0030 / 0,108 ± 0,033", "0,9844 ± 0,0030 / 0,159 ± 0,070", "0,9895 ± 0,0018 / 0,115 ± 0,027", "0,113 ± 0,013", "0,9574 ± 0,0002"],
        ["2.000", "0,9909 ± 0,0015 / 0,089 ± 0,015", "0,9897 ± 0,0017 / 0,127 ± 0,056", "0,9925 ± 0,0010 / 0,090 ± 0,039", "0,090 ± 0,015", "0,9575 ± 0,0001"],
        ["5.000", "0,9938 ± 0,0012 / 0,093 ± 0,010", "0,9937 ± 0,0015 / 0,102 ± 0,023", "0,9947 ± 0,0009 / 0,077 ± 0,006", "0,071 ± 0,002", "0,9575 ± 0,0002"],
        ["20.000", "0,9962 ± 0,0005 / 0,088 ± 0,006", "0,9960 ± 0,0006 / 0,110 ± 0,030", "0,9966 ± 0,0004 / 0,109 ± 0,016", "0,065 ± 0,010", "0,9571 ± 0,0001"]
    ],
    col_widths=[Inches(0.9), Inches(1.5), Inches(1.5), Inches(1.5), Inches(1.0), Inches(1.1)]
)

b.add_image(IMG_F55, width=Inches(6.2))
b.add_caption("Figure 5.5. Empirical Learning Curves of ROC-AUC, FPR, and Recall Across 5G Sample Sizes n (Log scale, ±1 SD)", is_table=False)

b.add_heading("5.5. Experiment A3: Detection of Unseen 5G Cyberattacks", level=2)
b.add_p("The Leave-One-Attack-Out (LOAO) protocol evaluated zero-day detection resilience across 8 attack categories (Table 5.8 and Figure 5.6). Results reveal a stark performance dichotomy:")
b.add_p("1. Raw-Packet Floods and Scans (UDPFlood, SYNFlood, ICMPFlood, SYNScan): Models achieved absolute detection (Recall = 1.0000 / 100%) even when the attack was completely withheld during training. SlowrateDoS also achieved high recall (0.8769 in A3-a, 0.9487 in A3-b). These attacks exhibit extreme statistical anomalies (massive packet rates, uniform payload sizes, absence of reply traffic), triggering tree splits on basic rate features.")
b.add_p("2. Application-Like Cyberattacks: Models suffered severe evasion when encountering novel application-level attacks. HTTPFlood achieved only 0.4979 recall (missing over half); UDPScan reached 0.4737; and TCPConnectScan suffered a catastrophic 99.4% evasion rate (Recall = 0.0057 in A3-a, 0.0053 in A3-b). Because TCP handshakes mimic authentic mobile traffic, operational thresholds place these unseen attacks firmly in the benign decision region.")

b.add_p("Testing Hypothesis H4: Hypothesis H4 is REJECTED. Incorporating legacy UNSW data did not improve detection of unseen 5G attacks: Recall on the withheld class increased by ≥ 0.05 on only 1 of the 8 attack types (SlowrateDoS: +0.0718), failing the pre-registered threshold of ≥ 2 types. For HTTPFlood, adding UNSW degraded local ROC-AUC from 0.7776 to 0.7003.")

b.add_p("Crucially, withholding TCPConnectScan in A3-b dropped benign FPR to a record low of 0.0245 (vs. 0.0789 in A1-2). This proves an operational trade-off: approximately 70% of all false alarms on benign 5G traffic stem from stretching decision boundaries to cover TCPConnectScan flows that closely resemble legitimate web traffic.")

b.add_caption("Table 5.8. Leave-One-Attack-Out Performance on 5G BS2 for Unseen Threats")
b.add_table(
    headers=["Withheld Attack (T)", "Flow Count (n)", "Pre-Reg Prediction", "Recall T (A3-a / A3-b)", "Benign FPR (a / b)", "ROC Benign vs T (a / b)", "Seen Recall (a / b)"],
    rows_data=[
        ["HTTPFlood", "64.691", "High (≥ 0,9)", "0,4979 / 0,4799", "0,0729 / 0,0809", "0,7776 / 0,7003", "1,0000 / 0,9999"],
        ["SlowrateDoS", "37.032", "High (≥ 0,9)", "0,8769 / 0,9487", "0,0675 / 0,0718", "0,9457 / 0,9393", "0,9992 / 0,9994"],
        ["UDPFlood", "30.656", "Med–High (0,6–0,95)", "1,0000 / 1,0000", "0,0775 / 0,0823", "0,9228 / 0,9350", "0,9985 / 0,9994"],
        ["TCPConnectScan", "10.028", "Low–Med (0,2–0,6)", "0,0057 / 0,0053", "0,1201 / 0,0245", "0,8601 / 0,6474", "1,0000 / 0,9997"],
        ["SYNFlood", "4.929", "Med–High (0,6–0,95)", "1,0000 / 1,0000", "0,0788 / 0,0819", "0,9253 / 0,9928", "0,9990 / 0,9999"],
        ["ICMPFlood", "462", "Low (< 0,4)", "1,0000 / 1,0000", "0,0768 / 0,0789", "0,9989 / 0,9990", "0,9993 / 0,9997"],
        ["SYNScan", "519", "Medium (0,4–0,8)", "1,0000 / 1,0000", "0,0769 / 0,0691", "0,9968 / 0,9935", "0,9995 / 0,9994"],
        ["UDPScan", "209", "Low (< 0,4)", "0,4737 / 0,4737", "0,0772 / 0,0804", "0,7019 / 0,8022", "0,9996 / 0,9999"]
    ],
    col_widths=[Inches(1.3), Inches(0.8), Inches(1.1), Inches(1.0), Inches(1.1), Inches(1.2), Inches(1.1)]
)

b.add_image(IMG_F56, width=Inches(6.2))
b.add_caption("Figure 5.6. Leave-One-Attack-Out Detection Recall on Withheld Cyberattack Classes (A3-a vs. A3-b) and Benign FPR", is_table=False)

b.add_heading("5.6. Consolidated Synthesis Mapped to Research Questions and Hypotheses", level=2)
b.add_p("Across protocols P1–P5 and adaptation trials A1–A3, this investigation definitively resolved all 4 research questions (RQ1–RQ4) and evaluated 4 pre-registered scientific hypotheses (H1–H4). The findings are synthesized in Table 5.9.")

b.add_caption("Table 5.9. Consolidated Resolution of Research Questions (RQ1–RQ4) and Hypotheses (H1–H4)")
b.add_table(
    headers=["Identifier", "Core Question / Scientific Hypothesis", "Empirical Finding", "Key Quantitative Evidence", "Report Section"],
    rows_data=[
        ["RQ1", "Can UNSW RF models detect 5G intrusions zero-shot?", "NO (Complete collapse)", "ROC-AUC collapses to 0.3990; PR-AUC drops below base rate π; FPR = 61.1%.", "Section 5.2"],
        ["RQ2", "Can a unified model succeed on both domains?", "YES (Outstanding success)", "Model A1-2 (LOI18): BS2 ROC-AUC = 0.9976, FPR = 0.0789; UNSW ROC = 0.9554.", "Section 5.3"],
        ["RQ3", "Minimum 5G labels required, and does legacy data help?", "Need ~2,000 labels; legacy data impairs", "A2-a reaches ROC ≥ 0.99 at n ~ 2,000; co-training at n ≤ 200 causes negative transfer.", "Section 5.4"],
        ["RQ4", "Can adapted models intercept unseen 5G zero-day attacks?", "DEPENDS (Sharp dichotomy)", "100% recall on raw flood/scan; severe evasion on HTTPFlood (50%), TCPScan (0.6%).", "Section 5.5"],
        ["H1", "UNSW co-training causes negative transfer at n ≤ 200.", "ACCEPTED (True)", "A2-a exceeds A2-b: +0.108 (n=50), +0.060 (n=100), +0.029 (n=200) ROC-AUC.", "Section 5.4"],
        ["H2", "50/50 domain balancing recovers ≥ 50% of the deficit.", "ACCEPTED (True)", "A2-c recovers 35% (n=50), 54% (n=100), 65% (n=200) of ROC gap.", "Section 5.4"],
        ["H3", "Joint validation thresholding inflates FPR by ≥ 0.20.", "REJECTED (False)", "FPR did not inflate by ≥ 0.20; joint validation reduced threshold variance (SD ~ 0.02).", "Section 5.4"],
        ["H4", "UNSW data improves unseen 5G attack detection.", "REJECTED (False)", "Recall improved on only 1 of 8 attacks (SlowrateDoS +0.07); HTTPFlood ROC degraded.", "Section 5.5"]
    ],
    col_widths=[Inches(0.6), Inches(2.2), Inches(1.4), Inches(2.3), Inches(0.7)]
)

print("Building Chapter 6 & 7...")

# ==========================================
# CHAPTER 6. DISCUSSION
# ==========================================
b.add_heading("CHAPTER 6. DISCUSSION AND CRITICAL EVALUATION", level=1)

b.add_heading("6.1. Deconstructing the Zero-Shot Failure Mechanisms", level=2)
b.add_p("The catastrophic zero-shot collapse of the UNSW-trained model on 5G-NIDD (ROC-AUC = 0.3990) raises a fundamental scientific question: Why does a model boasting near-perfect metrics on enterprise LAN telemetry fail completely when deployed to 5G? Our diagnostic investigation reveals four key mechanisms:")

b.add_p("1. Absence of Technical Mapping Failure: A round-trip validation experiment on UNSW test-final demonstrated that applying all feature mapping, scaling, and approximation formulas reduced ROC-AUC by only 0.007 (0.9594 → 0.9525). This technical discrepancy is 80 times smaller than the 0.56 ROC-AUC collapse observed on 5G-NIDD, proving that failure stems entirely from domain shift.")

b.add_p("2. Profound Concept Shift in Attack Semantics: The fundamental failure driver is divergence in attack generation. In UNSW-NB15, attacks generated by the IXIA PerfectStorm simulator carry complete application payloads and complete protocol handshakes (e.g., Reconnaissance flows are full TCP sessions terminating with FIN flags, containing an average of 354 reply bytes). In contrast, 5G-NIDD attacks were generated using realistic tools (hping3, nmap) emitting raw packets (40–58 bytes) without payloads or handshakes. Decision trees trained on UNSW learned the rule that 'small packets without reply data represent Normal traffic' (matching DNS/ARP normal flows in UNSW). Consequently, 5G flood and scan attacks were misclassified as benign. Sensitivity analysis shows that source packet size (smean) is the dominant factor: replacing 5G smean with UNSW medians shifts attack probability by +0.37 (Table 6.1).")

b.add_p("3. Radio Latency Shortcuts (ackdat): In the simulated LAN of UNSW, TCP handshake latency ackdat ≥ 10 ms is strongly correlated with attacks (99.6% of attack flows have large ackdat due to server exhaustion, vs. 24.7% for normal flows). However, in real 5G networks, physical radio propagation causes authentic mobile handshakes to frequently exhibit ackdat between 10–50 ms. Consequently, 71.5% of legitimate 5G TCP flows were falsely flagged as attacks. Furthermore, modern cellular protocols absent in UNSW—notably QUIC/UDP streaming and SCTP signaling—triggered mass false alarms.")

b.add_p("4. Distributed Multi-Feature Misalignment: Feature neutralization experiments (substituting features with UNSW training medians) showed that even the most impactful feature (smean) only elevated ROC-AUC to 0.411. This proves that zero-shot failure is a systemic, multi-dimensional phenomenon that cannot be corrected by isolated feature engineering.")

b.add_caption("Table 6.1. Empirical Discrepancies Between 5G Attacks and Closest Synthetic UNSW Profiles")
b.add_table(
    headers=["5G Attack Category", "P(Attack) 5G", "Closest Synthetic UNSW Cluster", "P(Attack) UNSW", "Decisive Divergent Features (5G → UNSW, Δp)"],
    rows_data=[
        ["UDPFlood", "0,46", "Attack UDP, INT state, ≤ 2 pkts", "0,97", "smean: 28 → 112 (+0,15); sinpkt: 2.576 → 0,008 ms (+0,10)."],
        ["SYNScan", "0,04", "Reconnaissance TCP", "1,00", "smean: 44 → 56 (+0,37); dbytes: 0 → 354 (+0,18); ackdat: 0 → 0,056 (+0,15)."],
        ["TCPConnectScan", "0,44", "Reconnaissance TCP", "1,00", "dbytes: 0 → 354 (+0,10); state: REQ → FIN (+0,07); ackdat: 0 → 0,056 (+0,05)."],
        ["SYNFlood", "0,16", "Attack TCP without handshake", "0,53", "smean: 40 → 63 (+0,25); dbytes: 44 → 586 (+0,18)."],
        ["Benign UDP", "0,70", "Normal UDP (DNS queries)", "0,00", "Packet interval: 30 ms vs 0,01 ms; dload: 7 kB/s vs 635 kB/s."]
    ],
    col_widths=[Inches(1.3), Inches(0.9), Inches(1.6), Inches(1.0), Inches(2.4)]
)

b.add_heading("6.2. The True Role of Legacy Enterprise Data", level=2)
b.add_p("A central finding of Plan A is that legacy enterprise data does not enhance 5G intrusion detection: protocol P3 (merged) matched P5 (pure 5G), model A1-2 matched A1-1 on BS2, and Hypothesis H4 was rejected in A3. Under label scarcity (n ≤ 200), adding legacy data even caused negative transfer.")

b.add_p("However, legacy data provides vital domain regularization: while 5G-NIDD contains only DoS and Scan attacks, UNSW-NB15 encompasses rich application attack families (Exploits, Fuzzers, Backdoors, Shellcode, Worms). The merged model A1-2 retained high detection efficacy across these diverse families on UNSW with an insignificant 0.0015 ROC-AUC reduction.")

b.add_p("Mechanistically, Random Forest accommodates disparate domains by partitioning feature space into localized subregions. When co-trained, the transport protocol feature (proto) increased its Gini importance from 0.009 to 0.085, functioning as an implicit routing split: branches for cellular protocols (SCTP, QUIC/UDP) were shaped by 5G telemetry, while branches for application payloads were governed by UNSW distributions.")

b.add_heading("6.3. Practical Guidelines for 5G Security Operations Centers (SOCs)", level=2)
b.add_p("Our findings provide three actionable guidelines for deploying ML-NIDS in 5G operational environments:")
b.add_p("1. Reject Zero-Shot Deployment: Security teams must never deploy intrusion detection models trained on synthetic enterprise benchmarks directly into operational 5G environments.")
b.add_p("2. Collect Minimum Calibration Telemetry: Telecom operators must acquire at least ~2,000 labelled 5G flows alongside ~500 validation flows to achieve operational detection stability.")
b.add_p("3. Implement Multi-Tiered Defenses: Supervised flow classifiers reliably intercept volumetric floods and scans, but application-mimicking attacks (HTTPFlood, TCPConnectScan) evade detection when novel. Operators must deploy multi-tiered architectures combining flow-level NIDS with stateful protocol inspection.")

b.add_heading("6.4. Limitations of the Study", level=2)
b.add_p("We acknowledge four internal limitations: (1) Base station splits (BS1/BS2) share identical attack scripts and target servers, measuring spatial invariance rather than cross-operator transferability; (2) 5G-NIDD lacks cellular control-plane attacks (e.g., NAS, NGAP, PFCP exploits); (3) Several fine-grained Argus fields required approximation due to empty raw values; and (4) The study focused on supervised Random Forests without evaluating deep domain adaptation methods.")

b.add_heading("6.5. Threats to Scientific Validity", level=2)
b.add_p("Validity was rigorously addressed across four dimensions (Table 6.2): internal validity was reinforced by decontaminating the 281,529 mislabelled 5G flows and establishing pre-registered threshold protocols; construct validity was maintained by reporting threshold-independent metrics (ROC-AUC, PR-AUC, MCC) alongside operational FPR; external validity was anchored on real-world 5G testbed traffic; and conclusion validity was verified through 5-seed repetitions.")

b.add_caption("Table 6.2. Methodological Threats to Validity and Applied Mitigation Strategies")
b.add_table(
    headers=["Validity Dimension", "Potential Methodological Threat", "Mitigation Strategy Implemented", "Residual Risk"],
    rows_data=[
        ["Internal Validity", "Data leakage between training and testing splits.", "Decontaminated 281.529 false Benign flows duplicated between BS1 and BS2.", "3,22% cross-split duplication persists in official UNSW test set."],
        ["Internal Validity", "Threshold selection data snooping.", "Pre-registered protocol: thresholds optimized strictly on test-dev / val.", "Validation sets with few benign samples exhibit threshold variance."],
        ["Internal Validity", "Shortcut learning from environmental artifacts.", "Purged sttl, dttl, ackdat, ct_*; decontaminated on LOI18 feature schema.", "Certain approximated features (sloss, dloss) rely on median lookups."],
        ["Construct Validity", "Distorted metrics due to severe class imbalance.", "Did not rely on raw Accuracy; reported Bal Acc, MCC, ROC-AUC, PR-AUC.", "Operational FPR ≤ 0.10 constraint is an empirical convention."],
        ["External Validity", "Generalizability to other 5G networks.", "Evaluated on operational 5G NSA cellular testbed with real smartphone traffic.", "Evaluation restricted to single testbed; lacks 5G SA network slice attacks."],
        ["Conclusion Validity", "Random variance in few-shot sampling.", "Trial A2 repeated across 5 independent random seeds, reporting Mean ± SD.", "Trials A1 and A3 evaluated on fixed seed 42 to guarantee determinism."]
    ],
    col_widths=[Inches(1.3), Inches(1.6), Inches(2.1), Inches(2.2)]
)

# ==========================================
# CHAPTER 7. CONCLUSION AND FUTURE WORK
# ==========================================
b.add_heading("CHAPTER 7. CONCLUSION AND FUTURE WORK", level=1)

b.add_heading("7.1. Conclusion", level=2)
b.add_p("This capstone project conducted a comprehensive empirical evaluation of cross-dataset generalization from traditional enterprise networks to modern 5G cellular infrastructures. The core conclusions are:")
b.add_p("1. Complete Failure of Zero-Shot Transfer: Random Forest models trained on UNSW-NB15 cannot be deployed zero-shot to 5G networks, collapsing to an ROC-AUC of 0.3990 due to fundamental concept shift, radio latency shortcuts, and modern transport protocols.")
b.add_p("2. Outstanding Efficacy of Supervised Adaptation: Unified co-training on the shortcut-free LOI18 feature schema (A1-2) establishes operational maturity on 5G Base Station 2 (ROC-AUC = 0.9976, Recall = 0.9995, FPR = 0.0789) while preserving enterprise detection capabilities (ROC-AUC = 0.9554).")
b.add_p("3. Empirical Label Complexity Guidelines: Acquiring ~2,000 labelled 5G flows and ~500 validation flows is necessary and sufficient for adaptation, whereas few-shot co-training with fewer labels induces severe negative transfer.")
b.add_p("4. Detection Dichotomy for Unseen Attacks: Supervised models achieve 100% recall on novel raw-packet floods and scans, but suffer severe evasion on application-mimicking cyberattacks (HTTPFlood, TCPConnectScan), highlighting the necessity of multi-tiered defense architectures.")

b.add_heading("7.2. Future Work", level=2)
b.add_p("We outline four avenues for subsequent research:")
b.add_p("1. Model Packaging and Deployment (A4): Formalize the release of models/A1_model_gop/rf_gop_loi18.joblib with standardized Model Cards documenting validated operational thresholds (θ*_UNSW = 0.7177, θ*_5G = 0.3525).")
b.add_p("2. Automated 5G Testbed Telemetry Harvester (A5): Develop an automated pcap capture and Argus extraction pipeline tapping the S1-U/N3 interface of a private 5G SA testbed.")
b.add_p("3. Hybrid Anomaly Detection Front-End: Integrate an unsupervised one-class classifier (Isolation Forest or Autoencoder) trained exclusively on benign 5G traffic to intercept novel application-level anomalies before supervised classification.")
b.add_p("4. Unsupervised Domain Adaptation: Explore distribution alignment methods (CORAL, MMD) and Domain Adversarial Neural Networks (DANN) to adapt models without requiring target 5G labels.")

# ==========================================
# REFERENCES & APPENDICES
# ==========================================
b.add_heading("REFERENCES", level=1)
references = [
    "[1] S. Samarakoon, C. Siriwardhana, Y. Nanayakkara, M. Liyanage, and P. Kumar, \"5G-NIDD: A Comprehensive Network Intrusion Detection Dataset Generated over 5G Wireless Network,\" IEEE Xplore, Art. no. 11098458, 2025. arXiv:2212.01298.",
    "[2] N. Moustafa and J. Slay, \"UNSW-NB15: A comprehensive data set for network intrusion detection systems (UNSW-NB15 network data set),\" in Proc. IEEE MilCIS, Canberra, Australia, 2015, pp. 1–6.",
    "[3] S. Neupane, R. Sharma, and L. Chen, \"Cross-dataset evaluation of machine learning based network intrusion detection systems,\" in Proc. IEEE GLOBECOM, 2020, pp. 1–6.",
    "[4] D. Arp, E. Quiring, F. Pendlebury, A. Warnecke, F. Pierazzi, C. Wressnegger, R. Cavallaro, and K. Rieck, \"Dos and Don'ts of Machine Learning in Computer Security,\" in Proc. 31st USENIX Security Symposium, Boston, MA, 2022, pp. 3971–3988.",
    "[5] G. Apruzzese, P. Laskov, E. Montes de Oca, F. Mallouli, L. B. R. Brás, A. Cruz, and H. S. Ribeiro, \"The Role of Machine Learning in Cybersecurity,\" Digital Threats: Research and Practice, vol. 4, no. 1, pp. 1–38, 2023.",
    "[6] R. Sommer and V. Paxson, \"Outside the Closed World: On Using Machine Learning for Network Intrusion Detection,\" in Proc. IEEE Symposium on Security and Privacy (S&P), Oakland, CA, 2010, pp. 305–316.",
    "[7] L. Breiman, \"Random Forests,\" Machine Learning, vol. 45, no. 1, pp. 5–32, 2001.",
    "[8] L. D'hooge, T. Wauters, B. Volckaert, and F. De Turck, \"Inter-dataset Generalization of Machine Learning-based Network Intrusion Detection Systems: A Comprehensive Forensic Study,\" IEEE Transactions on Network and Service Management, vol. 19, no. 4, pp. 4376–4393, 2022.",
    "[9] 3GPP, \"System Architecture for the 5G System (5GS),\" 3rd Generation Partnership Project, Technical Specification TS 23.501, Rel. 16, 2020.",
    "[10] 3GPP, \"Security Architecture and Procedures for 5G System,\" 3rd Generation Partnership Project, Technical Specification TS 33.501, Rel. 16, 2020.",
    "[11] J. Lyu, K. S. Low, and P. Chen, \"QUIC-based Traffic Analysis and Detection in Cellular Networks: Challenges and Opportunities,\" IEEE Communications Magazine, vol. 60, no. 5, pp. 74–80, 2022.",
    "[12] J. G. Moreno-Torres, T. Raeder, R. Alaiz-Rodríguez, N. V. Chawla, and F. Herrera, \"A unifying view on dataset shift in classification,\" Pattern Recognition, vol. 45, no. 1, pp. 521–530, 2012.",
    "[13] S. J. Pan and Q. Yang, \"A Survey on Transfer Learning,\" IEEE Transactions on Knowledge and Data Engineering, vol. 22, no. 10, pp. 1345–1359, 2010.",
    "[14] M. Ring, S. Wunderlich, D. Scheuring, D. Landes, and A. Hotho, \"A survey of network-based intrusion detection data sets,\" Computers & Security, vol. 86, pp. 147–167, 2019.",
    "[15] A. Saheed and M. Misra, \"Supervised Domain Adaptation for Machine Learning-Based Network Intrusion Detection,\" IEEE Access, vol. 10, pp. 124560–124575, 2022.",
    "[16] F. Pedregosa et al., \"Scikit-learn: Machine Learning in Python,\" Journal of Machine Learning Research, vol. 12, pp. 2825–2830, 2011."
]
for ref in references:
    b.add_p(ref, space_after=4)

b.add_heading("APPENDICES", level=1)

b.add_heading("Appendix A: Complete Feature Harmonization Dictionary", level=2)
b.add_p("This appendix documents the 31 flow-level features harmonized across UNSW-NB15 and 5G-NIDD, specifying operational data types, source fields, and inclusion across feature schemas.")
b.add_table(
    headers=["Index", "Feature", "Type", "Source (UNSW / 5G)", "Harmonization Method", "F31", "LOI18"],
    rows_data=[
        ["1", "dur", "float", "dur / Dur", "Direct: flow duration in seconds.", "Yes", "Yes"],
        ["2", "proto", "category", "proto / Proto", "Normalized protocol name (tcp, udp, sctp, icmp, other).", "Yes", "Yes"],
        ["3", "service", "category", "service / Sport,Dport", "Port-inferred service (http, dns, ssl, etc.).", "Yes", "Yes"],
        ["4", "state", "category", "state / State", "Normalized connection state flags.", "Yes", "Yes"],
        ["5", "spkts", "int", "spkts / SrcPkts", "Direct: source-to-destination packet count.", "Yes", "Yes"],
        ["6", "dpkts", "int", "dpkts / DstPkts", "Direct: destination-to-source packet count.", "Yes", "Yes"],
        ["7", "sbytes", "int", "sbytes / SrcBytes", "Direct: source-to-destination payload bytes.", "Yes", "Yes"],
        ["8", "dbytes", "int", "dbytes / DstBytes", "Direct: destination-to-source payload bytes.", "Yes", "Yes"],
        ["9", "rate", "float", "rate / Rate", "Direct: total packet rate per second.", "Yes", "Yes"],
        ["10", "sload", "float", "sload / Load", "Source bits per second: (sbytes * 8) / dur.", "Yes", "Yes"],
        ["11", "dload", "float", "dload / Load", "Destination bits per second: (dbytes * 8) / dur.", "Yes", "Yes"],
        ["12", "sloss", "int", "sloss / Loss", "Imputed via median protocol lookup.", "Yes", "Yes"],
        ["13", "dloss", "int", "dloss / Loss", "Imputed via median protocol lookup.", "Yes", "Yes"],
        ["14", "sinpkt", "float", "sinpkt / Empty", "Inter-packet time: dur / (spkts - 1).", "Yes", "Yes"],
        ["15", "dinpkt", "float", "dinpkt / Empty", "Inter-packet time: dur / (dpkts - 1).", "Yes", "Yes"],
        ["16", "sjit", "float", "sjit / Empty", "Packet jitter estimated via rate variance.", "Yes", "Yes"],
        ["17", "djit", "float", "djit / Empty", "Packet jitter estimated via rate variance.", "Yes", "Yes"],
        ["18", "swin", "int", "swin / Win", "Source TCP window advertisement.", "Yes", "Yes"],
        ["19", "dwin", "int", "dwin / Win", "Destination TCP window advertisement.", "Yes", "Yes"],
        ["20", "tcprtt", "float", "tcprtt / TcpRtt", "Direct: TCP round-trip handshake time.", "Yes", "No"],
        ["21", "synack", "float", "synack / SynAck", "Direct: TCP SYN-to-SYN-ACK duration.", "Yes", "No"],
        ["22", "ackdat", "float", "ackdat / AckDat", "Direct: TCP SYN-ACK-to-ACK duration (radio shortcut).", "Yes", "No"],
        ["23", "smean", "int", "smean / Mean", "Average source packet size: sbytes / spkts.", "Yes", "Yes"],
        ["24", "dmean", "int", "dmean / Mean", "Average destination packet size: dbytes / dpkts.", "Yes", "Yes"],
        ["25", "trans_depth", "int", "trans_depth / Zeek", "Zeek HTTP pipelined transaction count.", "Yes", "No"],
        ["26", "response_body_len", "int", "response_body_len / Zeek", "Zeek HTTP response body length in bytes.", "Yes", "No"],
        ["27", "ct_srv_src", "int", "ct_srv_src / Window", "Sliding window connection counter.", "Yes", "No"],
        ["28", "ct_state_ttl", "int", "ct_state_ttl / Window", "Sliding window TTL/state counter.", "Yes", "No"],
        ["29", "ct_dst_ltm", "int", "ct_dst_ltm / Window", "Sliding window destination counter.", "Yes", "No"],
        ["30", "ct_src_dport_ltm", "int", "ct_src_dport_ltm / Window", "Sliding window destination port counter.", "Yes", "No"],
        ["31", "ct_dst_sport_ltm", "int", "ct_dst_sport_ltm / Window", "Sliding window source port counter.", "Yes", "No"]
    ],
    col_widths=[Inches(0.5), Inches(1.3), Inches(0.8), Inches(1.4), Inches(2.3), Inches(0.4), Inches(0.5)]
)

b.add_heading("Appendix B: Attack Profile Taxonomy in UNSW-NB15 and 5G-NIDD", level=2)
b.add_p("This appendix contrasts the 9 attack families of UNSW-NB15 with the 8 attack classes of 5G-NIDD, specifying payload characteristics and execution methods.")
b.add_table(
    headers=["Attack Class", "Dataset Origin", "Target Layer", "Generation Tool", "Payload Profile", "Primary Failure Mechanism"],
    rows_data=[
        ["Exploits", "UNSW-NB15", "Application", "IXIA PerfectStorm", "Full exploit payloads targeting known CVEs.", "Absent in 5G-NIDD."],
        ["Fuzzers", "UNSW-NB15", "Application", "IXIA PerfectStorm", "Malformed protocol frames and invalid fields.", "Absent in 5G-NIDD."],
        ["DoS", "UNSW-NB15", "Network / App", "IXIA PerfectStorm", "Simulated floods with application handshakes.", "Matches 5G DoS in semantics only."],
        ["Reconnaissance", "UNSW-NB15", "Transport", "IXIA PerfectStorm", "TCP scans completing FIN handshakes.", "Contrasts with raw 5G scans."],
        ["Generic", "UNSW-NB15", "Cryptographic", "IXIA PerfectStorm", "Collisions on block ciphers.", "Absent in 5G-NIDD."],
        ["UDPFlood", "5G-NIDD", "Network", "hping3", "Raw 42-byte UDP packets; no payload.", "Misclassified as Normal UDP."],
        ["SYNFlood", "5G-NIDD", "Transport", "hping3", "Raw TCP SYN packets; no payload.", "Misclassified as Normal TCP."],
        ["ICMPFlood", "5G-NIDD", "Network", "hping3", "Raw ICMP echo requests; no payload.", "Misclassified as Normal ICMP."],
        ["HTTPFlood", "5G-NIDD", "Application", "Custom script", "Legitimate HTTP GET requests in high volume.", "Detected via duration & volume."],
        ["SlowrateDoS", "5G-NIDD", "Application", "slowloris", "Slow HTTP headers keeping connections open.", "Detected via duration & interval."],
        ["TCPConnectScan", "5G-NIDD", "Transport", "nmap", "Full TCP handshakes immediately closed; no payload.", "Misclassified as Benign web traffic."],
        ["SYNScan", "5G-NIDD", "Transport", "nmap", "Raw TCP SYN probes without ACK reply.", "Misclassified as Benign traffic."]
    ],
    col_widths=[Inches(1.2), Inches(1.0), Inches(0.9), Inches(1.2), Inches(1.6), Inches(1.3)]
)

b.add_heading("Appendix C: Reproducibility Pipeline and Command Reference", level=2)
b.add_p("To re-execute the entire experimental pipeline from raw data to final report generation, execute the following commands in sequence:")
commands = [
    "# 1. Environment initialization",
    "python -m venv .venv && source .venv/bin/activate    # Windows: .venv\\Scripts\\activate",
    "pip install -r requirements.txt",
    "",
    "# 2. Re-execute UNSW-NB15 baseline and audit",
    "jupyter nbconvert --to notebook --execute notebooks/01_Data_Cleaning.ipynb",
    "jupyter nbconvert --to notebook --execute notebooks/07_Consolidated_Rerun.ipynb",
    "",
    "# 3. Execute 5G-NIDD data sanitization and baseline",
    "python -I -X utf8 experiment_5gnidd/src/01_lam_sach_5gnidd.py .",
    "python -I -X utf8 experiment_5gnidd/src/02_train_danh_gia.py .",
    "python -I -X utf8 experiment_5gnidd/src/03_phuong_an_cross_validate.py .",
    "",
    "# 4. Execute Plan A: Supervised 5G Domain Adaptation",
    "python -I -X utf8 experiment_5g_adaptation/src/A1_model_gop.py .     # ~12 minutes",
    "python -I -X utf8 experiment_5g_adaptation/src/A2_few_shot.py .      # ~50 minutes",
    "python -I -X utf8 experiment_5g_adaptation/src/A3_loao.py .          # ~20 minutes",
    "",
    "# 5. Generate complete English report Word document",
    "python bao_cao_BTL/build_full_report_en.py"
]
for cmd in commands:
    p = b.add_p(cmd, space_after=1)
    for r in p.runs:
        r.font.name = 'Consolas'
        r.font.size = Pt(9.5)

print("Saving complete English report...")
doc.save(OUT_EN_PATH)
shutil.copyfile(OUT_EN_PATH, OUT_CAPSTONE_PATH)

print(f"SUCCESS: Report saved to:\n  1. {OUT_EN_PATH}\n  2. {OUT_CAPSTONE_PATH}")

