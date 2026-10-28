# IDS cho mạng 5G: cross-validate UNSW-NB15 ↔ 5G-NIDD

Hệ thống phát hiện xâm nhập (IDS) dựa trên Random Forest, huấn luyện trên **UNSW-NB15**, sau đó kiểm tra khả năng chuyển giao sang lưu lượng mạng 5G thật (**5G-NIDD**) và cho model thích nghi với 5G bằng nhãn 5G.

Repo chỉ chứa **mã nguồn, báo cáo và bảng/hình kết quả**. Dữ liệu và model (`.parquet`, `.zip`, `.joblib`, `.npz`, …) không được đưa lên. Xem mục [Lấy dữ liệu](#lấy-dữ-liệu) để tải và đặt lại dữ liệu.

## Kết quả chính

| Thí nghiệm | Kết quả | Nguồn |
|---|---|---|
| Model RF 31 feature (NB07) trên UNSW-NB15 test-final | accuracy 0,8186 · ROC-AUC 0,9594 | `reports/Bao_cao_ket_qua_notebook07.md` |
| **Zero-shot** UNSW → 5G-NIDD | **Không chuyển giao được.** ROC-AUC 0,399, balanced accuracy 0,446, MCC −0,080, FPR lớp lành tính 61%. Nguyên nhân là hai bộ dữ liệu đặt cùng tên tấn công cho những hành vi khác nhau, không phải do lỗi ánh xạ feature (phép thử round-trip chỉ làm ROC-AUC giảm 0,9594 → 0,9525). | `reports/5gnidd/Bao_cao_doi_chieu_5G-NIDD.md` |
| Chất lượng 5G-NIDD | 281.529 flow (59% lớp Benign) bị gán nhãn sai. Đây là bản sao UDP flood bắt lại ở BS1. Sau làm sạch còn 379.563 flow. | như trên, §5 |
| **A1** Model gộp UNSW + 5G (LOI18, trọng số bằng nhau) | Một model tốt trên cả hai miền: BS2 ROC-AUC 0,9976 · FPR 0,079 · recall 0,9995. UNSW ROC-AUC 0,9554, chỉ giảm 0,0015 so với model chỉ học UNSW. | `experiment_5g_adaptation/reports/Bao_cao_A1.md` |
| **A2** Cần bao nhiêu nhãn 5G | Khoảng 2.000 nhãn nếu chỉ dùng 5G hoặc gộp có cân miền; khoảng 5.000 nhãn nếu gộp với trọng số bằng nhau. Khi ít nhãn, khâu yếu là chọn ngưỡng chứ không phải xếp hạng (50 nhãn đã cho ROC-AUC 0,96 nhưng FPR dao động 0,05–0,29). | `experiment_5g_adaptation/reports/Bao_cao_A2.md` |
| **A3** Tấn công 5G chưa thấy (leave-one-attack-out) | Flood/scan "gói trần" (UDP/SYN/ICMP flood, SYN scan) vẫn bắt được 100%. Tấn công giống lưu lượng ứng dụng bị lọt: HTTPFlood 50%, UDPScan 47%, TCPConnectScan 0,6%. Thêm dữ liệu UNSW không giúp (chỉ cải thiện 1/8 loại). | `experiment_5g_adaptation/reports/Bao_cao_A3.md` |

## Cấu trúc thư mục

```
5G_IDS_Project/
├── Clean_Data.ipynb               notebook làm sạch đầu tiên (bản Colab, tiền thân của notebooks/01)
├── notebooks/                     chuỗi chính trên UNSW-NB15, chạy theo thứ tự 01 → 07
│                                    01 làm sạch · 02–03 huấn luyện RF · 04 cải thiện precision, chia test-dev/test-final
│                                    05 so sánh / cải thiện model · 06 truy nguyên nguyên nhân · 07 chạy lại tổng hợp
├── models/                        chỉ số và feature importance của RF lần 1–3 (.json/.csv; .joblib không đưa lên)
├── reports/                       báo cáo .md/.txt và kết quả của notebook 05–07
│   ├── exp05/  audit06/  rerun07/   bảng .csv/.json theo notebook
│   ├── dedup_vs_nodedup/            so sánh có/không khử trùng lặp
│   └── 5gnidd/                      đối chiếu 5G-NIDD và zero-shot (script + báo cáo)
├── experiment_nodedup/            thí nghiệm không khử trùng lặp UNSW-NB15 (notebook, báo cáo)
├── experiment_5gnidd/             làm sạch 5G-NIDD, train/đánh giá trên 5G, so sánh phương án cross-validate
│   ├── src/                         01_lam_sach → 02_train_danh_gia → 03_phuong_an_cross_validate
│   └── results/                     bảng, log, hình ma trận nhầm lẫn
├── experiment_5g_adaptation/      Kế hoạch A: học có nhãn 5G (A1 model gộp, A2 few-shot, A3 LOAO)
│                                    xem experiment_5g_adaptation/README.md
├── bao_cao_BTL/                   báo cáo bài tập lớn
└── requirements.txt
```

## Lấy dữ liệu

### UNSW-NB15

Tải từ trang chính thức của UNSW: <https://research.unsw.edu.au/projects/unsw-nb15-dataset>. Lấy bộ *Training and Testing Sets* rồi đặt vào:

```
data/raw/CSV Files/Training and Testing Sets/UNSW_NB15_training-set.csv
data/raw/CSV Files/Training and Testing Sets/UNSW_NB15_testing-set.csv
```

Chạy `notebooks/01_Data_Cleaning.ipynb` để sinh `data/cleaned/UNSW_NB15_{training,testing}-set.parquet`. Sau đó chạy `notebooks/04_Precision_Improvement.ipynb` để sinh `data/cleaned/test_split_v3.csv` (bảng chia test-dev/test-final). Các script 5G đều đọc file này.

### 5G-NIDD

Tải từ Fairdata (mã `9d13ef28-2ca7-44b0-9950-225359afac65`, truy cập mở) hoặc IEEE DataPort (dataset 10203). Giấy phép **CC BY 4.0**. **Bắt buộc trích dẫn** bài báo gốc:

> S. Samarakoon et al., "5G-NIDD: A Comprehensive Network Intrusion Detection Dataset Generated over 5G Wireless Network", IEEE Xplore 11098458 · arXiv:2212.01298.

Đặt các file zip vào:

```
experiment_5gnidd/data/raw/BTS1_BTS2_fields_preserved.zip   # bắt buộc
experiment_5gnidd/data/raw/BTS_1.zip                        # bắt buộc (xác định ranh giới trạm BS1/BS2)
data/5gnidd/raw/{BTS1_BTS2_fields_preserved,BTS_1,BTS_2,Combined}.zip   # chỉ cần cho các script trong reports/5gnidd/
```

`experiment_5gnidd/src/01_lam_sach_5gnidd.py` tự giải nén và ghi ra `experiment_5gnidd/data/cleaned/5gnidd_unsw31.parquet`.

## Môi trường

Python 3.11, scikit-learn 1.9.1, pandas 3.0.6, numpy 2.4.6 (đầy đủ trong `requirements.txt`).

```bash
python -m venv .venv && .venv/Scripts/activate      # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## Chạy lại

1. **Notebooks UNSW-NB15:** `notebooks/01` → `07` theo thứ tự (`05_Model_Comparison` và `05_Model_Improvement` là hai nhánh của bước 05). Model và mảng xác suất được ghi lại vào `models/` và `reports/exp05/`.
2. **5G-NIDD:**
   ```bash
   python -I -X utf8 experiment_5gnidd/src/01_lam_sach_5gnidd.py .
   python -I -X utf8 experiment_5gnidd/src/02_train_danh_gia.py .
   python -I -X utf8 experiment_5gnidd/src/03_phuong_an_cross_validate.py .
   ```
3. **Thích nghi 5G (Kế hoạch A):**
   ```bash
   python -I -X utf8 experiment_5g_adaptation/src/A1_model_gop.py .    # ~12 phút
   python -I -X utf8 experiment_5g_adaptation/src/A2_few_shot.py .     # ~50 phút
   python -I -X utf8 experiment_5g_adaptation/src/A3_loao.py .         # ~20 phút
   ```
   Đặt `QUICK=1` để chạy thử nhanh với 40 cây. A1 cần thêm `reports/exp05/rf_A_trainfit.joblib` (model RF 31 feature của NB07). File này không có trong repo nên cần tạo lại từ chuỗi notebook.

Đối số đầu tiên của mọi script là thư mục gốc dự án. Mọi script chỉ ghi vào thư mục thí nghiệm của chính nó.

## Báo cáo

- Chuỗi UNSW-NB15: `reports/Bao_cao_ket_qua_notebook07.md`, `reports/Bao_cao_truy_nguyen_accuracy.md`, `reports/Bao_cao_ra_soat_notebook06.md`, `reports/dedup_vs_nodedup/Bao_cao_dedup_vs_nodedup.md`
- 5G-NIDD: `reports/5gnidd/Bao_cao_doi_chieu_5G-NIDD.md`, `experiment_5gnidd/results/Bao_cao_phuong_an_cross_validate.md`
- Thích nghi 5G: `experiment_5g_adaptation/README.md`, `experiment_5g_adaptation/reports/Bao_cao_A1.md`, `Bao_cao_A2.md`, `Bao_cao_A3.md`
- Bài tập lớn: `bao_cao_BTL/`
