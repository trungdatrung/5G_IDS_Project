import sys
sys.stdout.reconfigure(encoding='utf-8')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

OUT_DIR = r'G:\.shortcut-targets-by-id\1C2Fd9KvthwrCJvr4mxV0l6w7K1lsUbNE\5G_IDS_Project\bao_cao_BTL'

# Figure 2.1: General Flow-based NIDS Architecture
def make_fig2_1():
    fig, ax = plt.subplots(figsize=(10, 4), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis('off')

    stages = [
        ("Network Traffic\nCapture (pcap)", "Raw packets\nTap / Mirror port"),
        ("Bidirectional Flow\nExtraction", "Argus / Zeek\n5-tuple grouping"),
        ("Feature Engineering\n& Preprocessing", "Statistical metrics\nOne-Hot / Normalization"),
        ("Machine Learning\nModel (Random Forest)", "Trained trees\nProbability scoring"),
        ("Decision & Alerting\n(Threshold θ*)", "Recall vs. FPR constraint\nSOC Alert Dispatch")
    ]
    colors = ['#e0f2fe', '#bae6fd', '#7dd3fc', '#38bdf8', '#0284c7']
    text_colors = ['#0369a1', '#0369a1', '#075985', '#0c4a6e', '#ffffff']

    for i, (title, desc) in enumerate(stages):
        x = 0.4 + i * 1.9
        p = patches.FancyBboxPatch((x, 0.8), 1.5, 2.4, boxstyle="round,pad=0.15", fc=colors[i], ec='#0284c7', lw=1.5)
        ax.add_patch(p)
        ax.text(x + 0.75, 2.3, title, ha='center', va='center', fontsize=9.5, fontweight='bold', color=text_colors[i])
        ax.text(x + 0.75, 1.3, desc, ha='center', va='center', fontsize=8, color=text_colors[i])
        if i < 4:
            ax.annotate('', xy=(x + 1.85, 2.0), xytext=(x + 1.55, 2.0),
                        arrowprops=dict(arrowstyle="->", lw=2, color='#0369a1'))

    plt.title("Figure 2.1. Architectural Overview of a Flow-Based Network Intrusion Detection System", fontsize=11, fontweight='bold', pad=15)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig2_1_nids_arch_en.png")
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print("Generated", path)

# Figure 3.1: 5G-NIDD Network Topology
def make_fig3_1():
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.5)
    ax.axis('off')

    # Radio Access Network
    p_ran = patches.FancyBboxPatch((0.5, 0.5), 3.8, 3.5, boxstyle="round,pad=0.2", fc='#f0fdf4', ec='#16a34a', lw=1.5)
    ax.add_patch(p_ran)
    ax.text(2.4, 3.6, "5G Radio Access Network (5GTN Oulu)", ha='center', fontsize=10, fontweight='bold', color='#166534')

    # BS1 & BS2
    p_bs1 = patches.Rectangle((0.8, 2.0), 3.2, 1.2, fc='#dcfce7', ec='#15803d', lw=1.2)
    ax.add_patch(p_bs1)
    ax.text(2.4, 2.75, "Base Station 1 (BS1)", ha='center', fontsize=9, fontweight='bold', color='#14532d')
    ax.text(2.4, 2.3, "Benign (Smartphones) + Attacks\n(hping3, nmap from UE1)", ha='center', fontsize=7.5, color='#14532d')

    p_bs2 = patches.Rectangle((0.8, 0.7), 3.2, 1.1, fc='#dcfce7', ec='#15803d', lw=1.2)
    ax.add_patch(p_bs2)
    ax.text(2.4, 1.35, "Base Station 2 (BS2)", ha='center', fontsize=9, fontweight='bold', color='#14532d')
    ax.text(2.4, 0.95, "Attacks (hping3 from UE2: 10.155.15.7)", ha='center', fontsize=7.5, color='#14532d')

    # Capture Point
    p_cap = patches.FancyBboxPatch((4.7, 1.5), 1.6, 1.8, boxstyle="round,pad=0.1", fc='#fef3c7', ec='#d97706', lw=1.5)
    ax.add_patch(p_cap)
    ax.text(5.5, 2.6, "Capture Point\n(S1-U Interface)", ha='center', fontsize=8.5, fontweight='bold', color='#78350f')
    ax.text(5.5, 1.9, "GTP-U Decapsulation\nArgus Flow Extraction\n(113 fields)", ha='center', fontsize=7.5, color='#92400e')

    # Core & Victim
    p_core = patches.FancyBboxPatch((6.8, 0.5), 2.8, 3.5, boxstyle="round,pad=0.2", fc='#eff6ff', ec='#2563eb', lw=1.5)
    ax.add_patch(p_core)
    ax.text(8.2, 3.6, "5G Core & Target Server", ha='center', fontsize=10, fontweight='bold', color='#1e40af')

    p_upf = patches.Rectangle((7.1, 2.2), 2.2, 1.0, fc='#dbeafe', ec='#1d4ed8', lw=1.2)
    ax.add_patch(p_upf)
    ax.text(8.2, 2.7, "5G Core (UPF / EPC)", ha='center', fontsize=8.5, fontweight='bold', color='#1e3a8a')

    p_vic = patches.Rectangle((7.1, 0.9), 2.2, 1.0, fc='#fee2e2', ec='#dc2626', lw=1.2)
    ax.add_patch(p_vic)
    ax.text(8.2, 1.5, "Victim Server", ha='center', fontsize=8.5, fontweight='bold', color='#991b1b')
    ax.text(8.2, 1.15, "IP: 10.41.150.68", ha='center', fontsize=8, color='#991b1b')

    # Arrows
    ax.annotate('', xy=(4.7, 2.5), xytext=(4.0, 2.5), arrowprops=dict(arrowstyle="->", lw=1.5, color='#0284c7'))
    ax.annotate('', xy=(4.7, 2.2), xytext=(4.0, 1.5), arrowprops=dict(arrowstyle="->", lw=1.5, color='#dc2626'))
    ax.annotate('', xy=(6.8, 2.4), xytext=(6.3, 2.4), arrowprops=dict(arrowstyle="->", lw=1.5, color='#0284c7'))

    plt.title("Figure 3.1. Topology of the 5G-NIDD Dataset Data Collection Environment (5GTN Oulu)", fontsize=11, fontweight='bold', pad=15)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig3_1_5gnidd_arch_en.png")
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print("Generated", path)

# Figure 3.2: 5G-NIDD Data Cleaning Pipeline
def make_fig3_2():
    fig, ax = plt.subplots(figsize=(10, 3.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3.5)
    ax.axis('off')

    steps = [
        ("Raw 5G-NIDD", "1,215,890 flows\n(BS1: 728k, BS2: 487k)\n113 Argus fields", "#f1f5f9", "#475569"),
        ("Remove Cross-BS\nDuplicate Captures", "Drop 281,529 flows\n(BS2 attacker captured\nat BS1 as Benign)", "#fee2e2", "#dc2626"),
        ("Intra-File Deduplication\n& Conflict Resolution", "Drop 554,789 duplicates\n& 16 label conflicts\nSame 5-tuple + timestamps", "#fef3c7", "#d97706"),
        ("Cleaned 5G-NIDD\nStandardized Dataset", "379,556 clean flows\n(BS1: 208,014 / BS2: 171,542)\nAttack ratio π = 0.833", "#dcfce7", "#16a34a")
    ]

    for i, (title, desc, bg, ec) in enumerate(steps):
        x = 0.5 + i * 2.35
        p = patches.FancyBboxPatch((x, 0.5), 1.9, 2.3, boxstyle="round,pad=0.15", fc=bg, ec=ec, lw=1.5)
        ax.add_patch(p)
        ax.text(x + 0.95, 2.2, title, ha='center', va='center', fontsize=8.5, fontweight='bold', color=ec)
        ax.text(x + 0.95, 1.2, desc, ha='center', va='center', fontsize=7.5, color='#334155')
        if i < 3:
            ax.annotate('', xy=(x + 2.3, 1.65), xytext=(x + 1.95, 1.65),
                        arrowprops=dict(arrowstyle="->", lw=2, color='#475569'))

    plt.title("Figure 3.2. Data Cleaning and Label Sanitization Workflow for 5G-NIDD", fontsize=11, fontweight='bold', pad=15)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig3_2_cleaning_pipeline_en.png")
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print("Generated", path)

# Figure 4.1: Dataset Splits and Evaluation Protocols (English)
def make_fig4_1():
    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7.5)
    ax.axis('off')

    # UNSW Domain
    r_unsw = patches.FancyBboxPatch((0.5, 4.0), 10, 3.0, boxstyle="round,pad=0.2", fc='#f8fafc', ec='#94a3b8', lw=1.5)
    ax.add_patch(r_unsw)
    ax.text(0.8, 6.7, "LEGACY NETWORK DOMAIN (UNSW-NB15 Synthetic LAN Traffic)", fontsize=10.5, fontweight='bold', color='#1e3a8a')

    # Splits UNSW
    splits_unsw = [
        ("train-fit (79,147)\nπ = 0.4964", "Model Training", 1.0, 2.4, '#dbeafe', '#2563eb'),
        ("validation (19,787)\nπ = 0.4964", "Internal Tuning", 3.7, 1.9, '#e0e7ff', '#4f46e5'),
        ("test-dev (25,283)\nπ = 0.3665", "THRESHOLD SELECTION\n(Constraint FPR ≤ 0.10)", 5.9, 2.3, '#fef3c7', '#d97706'),
        ("test-final (25,284)\nπ = 0.3665", "FINAL EVALUATION\n(Single-blind freeze)", 8.5, 1.8, '#fee2e2', '#dc2626')
    ]
    for name, role, x, w, bg, ec in splits_unsw:
        p = patches.Rectangle((x, 4.8), w, 1.3, fc=bg, ec=ec, lw=1.2)
        ax.add_patch(p)
        ax.text(x + w/2, 5.7, name, ha='center', va='center', fontsize=8.5, fontweight='bold', color=ec)
        ax.text(x + w/2, 5.15, role, ha='center', va='center', fontsize=7.5, color='#1e293b')

    # 5G Domain
    r_5g = patches.FancyBboxPatch((0.5, 0.5), 10, 3.0, boxstyle="round,pad=0.2", fc='#f8fafc', ec='#94a3b8', lw=1.5)
    ax.add_patch(r_5g)
    ax.text(0.8, 3.2, "5G NETWORK DOMAIN (5G-NIDD Real Mobile Traffic at 5GTN Oulu)", fontsize=10.5, fontweight='bold', color='#14532d')

    splits_5g = [
        ("5G-train (166,411 flows)\n80% BS1 · π = 0.8063", "Domain Adaptation Training", 1.0, 2.8, '#dcfce7', '#16a34a'),
        ("5G-val (41,603 flows)\n20% BS1 · π = 0.8063", "5G THRESHOLD TUNING\n(Constraint FPR ≤ 0.10)", 4.2, 2.5, '#fef9c3', '#ca8a04'),
        ("5G-test = BS2 (171,542 flows)\n100% Station BS2 · π = 0.8658", "INDEPENDENT EVALUATION\n(Target Vantage Point)", 7.1, 3.2, '#ffe4e6', '#e11d48')
    ]
    for name, role, x, w, bg, ec in splits_5g:
        p = patches.Rectangle((x, 1.2), w, 1.4, fc=bg, ec=ec, lw=1.2)
        ax.add_patch(p)
        ax.text(x + w/2, 2.15, name, ha='center', va='center', fontsize=8.5, fontweight='bold', color=ec)
        ax.text(x + w/2, 1.55, role, ha='center', va='center', fontsize=7.5, color='#1e293b')

    # Arrows
    ax.annotate('', xy=(8.5, 5.45), xytext=(8.2, 5.45), arrowprops=dict(arrowstyle="->", lw=1.5, color='#475569'))
    ax.annotate('', xy=(7.1, 1.9), xytext=(6.7, 1.9), arrowprops=dict(arrowstyle="->", lw=1.5, color='#475569'))

    plt.title("Figure 4.1. Data Partitioning and Dual-Domain Threshold Optimization Workflow", fontsize=11, fontweight='bold', pad=15)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig4_1_splits_en.png")
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print("Generated", path)

make_fig2_1()
make_fig3_1()
make_fig3_2()
make_fig4_1()
