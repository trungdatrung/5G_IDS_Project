# Kế hoạch A: cho model thích nghi với 5G bằng cách học có nhãn 5G

**Ngày:** 27/10/2026 · **Trạng thái:** A1 đã chạy (`reports/Bao_cao_A1.md`, đạt mọi kỳ vọng) · A2 đã chạy (`reports/Bao_cao_A2.md`: cần ~2.000 nhãn; H1, H2 đúng, H3 sai) · A3 đã chạy (`reports/Bao_cao_A3.md`: H4 sai, 0/8 dự đoán theo loại đúng) · A4, A5 chưa chạy
**Cập nhật 27/10:** thêm A1-5 (NB07 + `warm_start`) và A1-6 (định tuyến hai model) theo thử nghiệm nhanh; sửa số lớp đa lớp (19, không phải 20); chuyển sang thư mục `experiment_5g_adaptation/`.
**Căn cứ:** `experiment_5gnidd/results/Bao_cao_phuong_an_cross_validate.md` (P3, P4, P5) và `experiment_5gnidd/results/02_ket_qua.json` (E1–E4)
**Phạm vi ghi file:** chỉ trong `experiment_5g_adaptation/`. Không sửa `data/`, `models/`, `notebooks/`, `reports/`, `experiment_5gnidd/`.

**Cấu trúc thư mục:**

```
experiment_5g_adaptation/
├── README.md                 hướng dẫn, trạng thái từng bước
├── docs/                     kế hoạch (tài liệu này)
├── src/                      A1_model_gop.py, A2_few_shot.py, A3_loao.py, A4_dong_goi.py
├── results/<bước>/           tables/ (csv, json) · figures/ (png) · logs/ (log chạy)
├── models/<bước>/            model .joblib
└── reports/                  báo cáo từng bước, so với kỳ vọng
```

---

## 0. TÓM TẮT

| Bước | Câu hỏi trả lời | Kỳ vọng chính | Thời gian chạy (ước) |
|---|---|---|---|
| **A1** Model gộp chính thức | Có được **một** model tốt trên cả UNSW lẫn 5G không? | BS2 ROC-AUC ≥ 0,995 · UNSW giảm ≤ 0,005 | ~10 phút |
| **A2** Đường cong số nhãn | Cần **bao nhiêu nhãn 5G**? Ngưỡng chọn thế nào? | ≈ 1.700 nhãn → ROC-AUC ≥ 0,99, FPR ≤ 0,12 | ~45 phút |
| **A3** Leave-one-attack-out | Model có bắt được **loại tấn công 5G chưa thấy** không? UNSW có giúp không? | Chưa biết, đây là câu hỏi mở. Dự đoán scan/ICMP tụt mạnh | ~20 phút |
| **A4** Đóng gói | Bàn giao model và cách dùng | `.joblib` + model card + hàm dự đoán | ~5 phút |
| **A5** *(tuỳ chọn)* Tự sinh nhãn | Đưa dữ liệu testbed riêng vào pipeline | Cần testbed 5G, không chạy được trên máy này | — |

**Giả định đã chốt** (đổi thì báo lại trước khi chạy):
- Bộ feature **LOI18**.
- RF với tham số NB07.
- Hai trạm tách hẳn: **BS1 để train, BS2 để test**.
- **Ngưỡng luôn chọn trên nhãn 5G** (rút từ P4: chọn trên validation gộp làm FPR lên 0,38–0,80).

---

## 1. INPUT CHUNG

| Tệp | Nội dung | Sinh bởi |
|---|---|---|
| `experiment_5gnidd/data/cleaned/5gnidd_unsw31.parquet` | 379.556 flow 5G, 31 feature, `label`, `attack_cat`, `bs` | Bước 01 (đã chạy) |
| `data/cleaned/UNSW_NB15_training-set.parquet` | 98.934 flow UNSW | NB01 (chỉ đọc) |
| `data/cleaned/UNSW_NB15_testing-set.parquet` + `test_split_v3.csv` | UNSW test-dev 25.283 / test-final 25.284 | NB01 / NB07 (chỉ đọc) |

**Chia tập 5G** (cố định, seed 42, stratify theo `attack_cat`):

| Tập | Nguồn | Số dòng | Dùng cho |
|---|---|---|---|
| `5G-train` | 80% BS1 | 166.411 | Train |
| `5G-val` | 20% BS1 | 41.603 | Chọn ngưỡng, chọn trọng số |
| `5G-test` | **100% BS2** | 171.542 | Chỉ để báo cáo, không nhìn khi chọn bất cứ thứ gì |

---

## 2. A1 — MODEL GỘP CHÍNH THỨC

**Script:** `src/A1_model_gop.py`

**Input:** UNSW train-fit (79.147) + `5G-train` (166.411), cột LOI18. A1-5/A1-6 thêm `reports/exp05/rf_A_trainfit.joblib` (model RF 31 feature của NB07, chỉ đọc).

**Biến thể so sánh:**

| Mã | Train | Trọng số mẫu |
|---|---|---|
| A1-0 | Chỉ UNSW, LOI18 | — (mốc UNSW, không thích nghi) |
| A1-1 | Chỉ 5G | — (mốc 5G, mức trần) |
| A1-2 | UNSW + 5G | Bằng nhau (= P3) |
| A1-3 | UNSW + 5G | Cân miền: mỗi miền chiếm 50% tổng trọng số |
| A1-4 | UNSW + 5G, **đa lớp** (19 lớp: Normal + 9 họ UNSW, Benign + 8 loại 5G) | Bằng nhau. Điểm nhị phân = 1 − P(Normal) − P(Benign) |
| A1-5 | **Model NB07 giữ nguyên 300 cây UNSW + thêm 300 cây học trên `5G-train`** (`warm_start`, encoder cũ), F31 | — (bị khoá ở 31 feature của NB07) |
| A1-6 | **Định tuyến:** NB07 nguyên vẹn cho UNSW · RF công thức NB07 học trên `5G-train` cho 5G, F31 | — (cần biết lưu lượng thuộc mạng nào) |

**Ngưỡng:** hai ngưỡng riêng, mỗi miền một ngưỡng.
- UNSW: chọn trên UNSW test-dev, FPR ≤ 0,10, như NB07.
- 5G: chọn trên `5G-val`, FPR ≤ 0,10.

Ngoài ra ghi thêm kết quả @0,5.

**Output:**

| Tệp | Nội dung |
|---|---|
| `results/A1_model_gop/tables/A1_tong_hop.csv` | Mỗi biến thể × {BS2, UNSW test-final}: ROC-AUC, PR-AUC, bal acc, MCC, precision, recall, FPR, TN/FP/FN/TP |
| `results/A1_model_gop/tables/A1_recall_theo_loai.csv` | Recall từng loại tấn công + FPR Benign/Normal, trên cả hai miền |
| `results/A1_model_gop/tables/A1_importance.csv` | Importance của A1-2 và A1-3, so với A1-0 |
| `results/A1_model_gop/tables/A1_ket_qua.json` | Ngưỡng, kích thước tập, kiểm tra điểm dừng, model được chọn |
| `results/A1_model_gop/logs/A1_log.txt` | Log chạy |
| `results/A1_model_gop/figures/cm_A1-*.png` | Ma trận nhầm lẫn nhị phân (UNSW và BS2 cạnh nhau, ngưỡng từng miền) + đa lớp A1-4 |
| `models/A1_model_gop/rf_gop_loi18.joblib` | Model được chọn trong A1-2/A1-3 (xem tiêu chí ở dưới) |
| `reports/Bao_cao_A1.md` | Kết quả so với kỳ vọng |

**Kỳ vọng** (dựa trên P3 và P5 đã đo):

| Chỉ số | A1-0 | A1-1 | A1-2 / A1-3 | A1-5 (NB07 + warm_start) | A1-6 (định tuyến) |
|---|---|---|---|---|---|
| BS2 ROC-AUC | ≈ 0,31 | ≈ 0,998 | **≥ 0,995** | ≈ 0,997 | ≈ 0,999 |
| BS2 FPR @ngưỡng 5G | — | ≈ 0,08 | **≤ 0,10** | ≈ 0,03 | ≈ 0,14 |
| BS2 recall @ngưỡng 5G | — | ≈ 1,0 | **≥ 0,99** | ≈ 0,996 | ≈ 1,0 |
| UNSW test-final ROC-AUC | 0,957 | ≈ 0,48 | **≥ 0,952** (giảm ≤ 0,005 so với A1-0) | ≈ 0,947 (giảm ≈ 0,012 so với NB07 0,9594) | **= 0,9594** (NB07 nguyên vẹn) |
| UNSW bal acc @ngưỡng UNSW | 0,874 | — | **≥ 0,865** | ≈ 0,87 | = NB07 |

Số của A1-5/A1-6 lấy từ thử nghiệm nhanh ngày 27/10 (cùng cách chia, cùng quy tắc ngưỡng). A1 sẽ đo lại chính thức.

**Tiêu chí chọn model đóng gói:**
- Chỉ xét **A1-2 và A1-3** (một model, bộ LOI18 sạch shortcut). A1-5/A1-6 là phương án tham chiếu khi cần dùng lại NB07, không đóng gói ở A1.
- Lấy biến thể có **BS2 bal acc + UNSW bal acc** cao nhất (tính ở ngưỡng riêng từng miền), với điều kiện không miền nào vi phạm ngưỡng kỳ vọng ở bảng trên.
- Nếu A1-3 không hơn A1-2 quá 0,005, chọn A1-2 vì đơn giản hơn.

**Rủi ro:**
- Đa lớp A1-4 có 19 lớp, nên lớp hiếm (UDPScan 583, Worms ~100) có thể kém. Chỉ dùng A1-4 làm tham khảo.

---

## 3. A2 — ĐƯỜNG CONG SỐ NHÃN 5G

> **Cập nhật 27/10 (sau A1):** dùng công thức **A1-2** làm phương án chính. Mục này đã viết chi tiết lại trước khi chạy.

**Mục tiêu**
1. Tìm **số nhãn 5G tối thiểu** để công thức A1-2 đạt BS2 ROC-AUC ≥ 0,99 và FPR ≤ 0,12.
2. Trả lời câu hỏi: khi **ít nhãn**, có nên kèm UNSW không (H1, H2)?
3. Chứng minh ngưỡng 5G phải chọn trên nhãn 5G, không chọn trên validation gộp (H3).

**Công thức model:** giống A1-2. RF tham số NB07 (300 cây, max_depth 20, max_features 0,5, max_samples 0,7), bộ LOI18, OneHot cho `proto`/`state`.

**Script:** `src/A2_few_shot.py`

**Input**

| Dữ liệu | Dùng cho |
|---|---|
| `5G-train` (80% BS1, 166.411), chia y hệt A1 | Lấy mẫu n nhãn train |
| `5G-val` (20% BS1, 41.603) | Lấy mẫu n/4 nhãn để chọn ngưỡng 5G |
| UNSW train-fit (79.147) | Phần UNSW của model gộp |
| UNSW test-dev (25.283) | Chọn ngưỡng UNSW |
| BS2 (171.542), UNSW test-final (25.284) | Chỉ để báo cáo |

**Lấy mẫu**
- n ∈ {50, 100, 200, 500, 1.000, 2.000, 5.000, 20.000}, 5 seed (0–4).
- Mỗi lớp `attack_cat` lấy `round(n × tỷ lệ lớp)`, tối thiểu 1 mẫu.
- Mẫu validation có cỡ n/4, cũng tối thiểu 1 mẫu mỗi lớp.
- Với mỗi cặp (n, seed), mọi biến thể dùng **cùng một mẫu**.

**Biến thể**

| Mã | Train | Ngưỡng 5G chọn trên | Ngưỡng UNSW |
|---|---|---|---|
| A2-a | Chỉ n nhãn 5G | Mẫu 5G-val | — (không đo UNSW) |
| A2-b | **A1-2:** UNSW + n nhãn 5G, trọng số bằng nhau | Mẫu 5G-val | UNSW test-dev |
| A2-c | UNSW + n nhãn 5G, cân miền 50/50 | Mẫu 5G-val | UNSW test-dev |
| A2-d | **Cùng model A2-b** (không train thêm) | UNSW test-dev + mẫu 5G-val **gộp** | UNSW test-dev |

Mốc "toàn bộ nhãn": lấy luôn kết quả A1-1 / A1-2 của A1, không chạy lại.

**Output** (`results/A2_few_shot/`)

| Tệp | Nội dung |
|---|---|
| `tables/A2_tung_lan.csv` | Mỗi dòng là một (n, seed, biến thể, tập test, kiểu ngưỡng): ngưỡng, ROC-AUC, PR-AUC, bal acc, MCC, recall, FPR, TN/FP/FN/TP |
| `tables/A2_tong_hop.csv` | Trung bình ± SD theo (n, biến thể, tập test), ở ngưỡng miền |
| `tables/A2_ket_qua.json` | Số mẫu thực tế mỗi lớp, kết luận H1–H3, n tối thiểu của từng biến thể |
| `figures/A2_duong_cong.png` | 3 ô: ROC-AUC, FPR, recall trên BS2 theo n (trục log). Mỗi biến thể một đường kèm dải ±1 SD; nét đứt là mốc A1-2 |
| `logs/A2_log.txt` | Log chạy |
| `reports/Bao_cao_A2.md` | Kết quả so với kỳ vọng |

**Kỳ vọng** (từ P4 ở `experiment_5gnidd`, khi đó dùng UNSW-DR)

| n nhãn 5G | ROC-AUC BS2 (A2-a) | FPR @ngưỡng 5G | UNSW ROC-AUC (A2-b) |
|---|---|---|---|
| 50–100 | 0,90–0,96, dao động lớn | 0,15–0,30 | ≈ 0,955 |
| 200 | ≈ 0,965 | ≈ 0,12–0,15 | ≈ 0,955 |
| **1.000–2.000** | **≥ 0,99** | **≤ 0,12** | ≈ 0,955 |
| ≥ 5.000 | ≥ 0,994 | ≈ 0,08–0,10 | ≈ 0,955 |

A2-c có thể làm UNSW giảm khi n nhỏ: mỗi mẫu 5G mang trọng số rất lớn nên model dễ học thuộc vài điểm.

**Giả thuyết và cách kết luận** (định nghĩa trước khi chạy)

| | Giả thuyết | Kết luận "đúng" khi |
|---|---|---|
| H1 | Ít nhãn thì UNSW gây chuyển giao âm | ROC-AUC trung bình của A2-a > A2-b ở ít nhất 2/3 mức n ∈ {50, 100, 200} |
| H2 | Cân miền thu hẹp khoảng cách đó | A2-c lấp được ≥ 50% khoảng cách (A2-a − A2-b) ở ít nhất 2/3 mức n ≤ 200 có khoảng cách dương |
| H3 | Chọn ngưỡng trên validation gộp là sai | FPR BS2 trung bình của A2-d − A2-b ≥ 0,2 ở **mọi** n ≤ 1.000 |
| n tối thiểu | — | n nhỏ nhất mà ROC-AUC trung bình ≥ 0,99 **và** FPR trung bình ≤ 0,12, tính riêng cho từng biến thể |

**Điểm dừng:** nếu A2-b ở n = 20.000 có ROC-AUC BS2 < 0,99 thì kết quả mâu thuẫn với A1. Khi đó dừng để chẩn đoán.

**Thời gian ước:** 120 lần fit (8 mức n × 5 seed × 3 model), trong đó 80 lần fit có UNSW, mỗi lần khoảng 40 giây. Tổng khoảng 1 giờ.

---

## 4. A3 — LEAVE-ONE-ATTACK-OUT (khả năng bắt tấn công chưa thấy)

**Mục tiêu**
1. Đo khả năng công thức A1-2 phát hiện **một loại tấn công 5G chưa từng thấy khi train**. BS1 → BS2 không đo được điều này, vì hai trạm dùng chung công cụ.
2. Kiểm tra UNSW có giúp bắt tấn công mới không (H4).
3. Theo dõi báo động giả Benign khi giấu TCPConnectScan, lớp mà Benign hay bị nhầm thành nhất (1.017 flow ở A1-4).

**Công thức model:** giống A1-1 (chỉ 5G) và A1-2 (gộp). RF NB07, LOI18.

**Script:** `src/A3_loao.py`

**Input:** cách chia giống A1. Với mỗi loại T trong 8 loại tấn công 5G:

| Biến thể | Train | Ngưỡng 5G chọn trên |
|---|---|---|
| A3-a | `5G-train` bỏ hết loại T | `5G-val` bỏ T, FPR ≤ 0,10 |
| A3-b | UNSW train-fit + `5G-train` bỏ hết loại T (công thức A1-2) | `5G-val` bỏ T, FPR ≤ 0,10 |

**Test:** BS2. Đo trên ba nhóm:
- Loại T, tức loại bị giấu.
- Benign.
- Các loại tấn công còn lại, để kiểm tra model không bị hỏng chỗ khác.

**Output** (`results/A3_loao/`)

| Tệp | Nội dung |
|---|---|
| `tables/A3_loao.csv` | 8 loại × 2 biến thể: ngưỡng, **recall loại T**, **FPR Benign**, ROC-AUC (Benign vs T), recall các tấn công đã thấy, ROC-AUC toàn BS2 |
| `tables/A3_ket_qua.json` | Kết luận H4, đối chiếu với dự đoán, mốc A1 |
| `figures/A3_loao.png` | Cột: recall loại T bị giấu, A3-a cạnh A3-b. Điểm: FPR Benign. Đường ngang: mốc A1-2 (recall ≈ 1 khi đã thấy T) |
| `logs/A3_log.txt` | Log chạy |
| `reports/Bao_cao_A3.md` | Kết quả so với dự đoán |

**Kỳ vọng** (dự đoán **chưa có số đo**, độ tin cậy thấp)

| Loại bị giấu | Dự đoán recall (A3-a) | Lý do |
|---|---|---|
| HTTPFlood | Cao (≥ 0,9) | Giống SlowrateDoS: TCP cổng 80, đã bắt tay |
| SlowrateDoS | Cao | Giống HTTPFlood |
| UDPFlood | Trung bình–cao | Gói nhỏ, rate cao, gần UDPScan |
| SYNFlood | Trung bình–cao | Gói SYN trần, giống SYNScan |
| SYNScan | Trung bình | Giống SYNFlood nhưng ít gói hơn |
| TCPConnectScan | Thấp–trung bình | Có bắt tay đầy đủ, gói ít, dễ lẫn với Benign TCP. **FPR Benign dự đoán giảm** vì mất lớp hay bị nhầm thành |
| UDPScan | Thấp | Chỉ có 583 flow, hình dạng lạ |
| ICMPFlood | **Thấp** | Là loại ICMP tấn công duy nhất; Benign lại có 5.496 flow ICMP |

Recall các tấn công đã thấy: dự đoán ≥ 0,99 ở mọi lần (như A1).

**Giả thuyết và cách kết luận**

| | Giả thuyết | Kết luận "đúng" khi |
|---|---|---|
| H4 | UNSW giúp bắt tấn công 5G mới | Recall T của A3-b − A3-a ≥ 0,05 ở ít nhất 2/8 loại, và FPR Benign của A3-b không tăng quá 0,02 ở các loại đó |
| Dự đoán theo loại | Bảng trên | Đếm số loại có recall rơi đúng khoảng dự đoán. Cao ≥ 0,9 · Trung bình–cao 0,6–0,95 · Trung bình 0,4–0,8 · Thấp–trung bình 0,2–0,6 · Thấp < 0,4 |

**Điểm dừng:** nếu recall các tấn công **đã thấy** < 0,99 ở một lần chạy nào đó thì ghi lại và chẩn đoán trước khi viết kết luận.

**Thời gian ước:** 16 lần fit (8 lần chỉ 5G khoảng 30 giây, 8 lần gộp khoảng 3 phút). Tổng khoảng 30 phút.

---

## 5. A4 — ĐÓNG GÓI

**Script:** `src/A4_dong_goi.py`

**Input:** model được chọn ở A1, hai ngưỡng, cỡ nhãn khuyến nghị từ A2, giới hạn đã đo ở A3.

**Output:**

| Tệp | Nội dung |
|---|---|
| `models/A4_dong_goi/rf_gop_loi18.joblib` | Dict gồm: `pipeline`, `features` (LOI18), `nguong` {`unsw`, `5g`}, `phien_ban`, `ngay`, `hash_du_lieu` |
| `src/du_doan.py` | Hàm `du_doan(df, mien='5g')` → `proba`, `canh_bao`. Kiểm tra đủ cột LOI18 và đúng kiểu dữ liệu, rồi báo lỗi rõ ràng nếu thiếu |
| `reports/Model_card_rf_gop_loi18.md` | Dữ liệu train, chỉ số trên từng miền, recall theo loại, giới hạn (từ A3), cỡ nhãn cần khi đưa sang một mạng 5G mới (từ A2), cách đặt lại ngưỡng |
| `reports/Bao_cao_ke_hoach_A.md` | Kết quả A1–A3, so với kỳ vọng ở tài liệu này. Ghi rõ dự đoán nào đúng, dự đoán nào sai |

**Kiểm tra trước khi bàn giao:**
- Nạp lại file `.joblib` và chạy trên BS2: kết quả phải khớp `A1_tong_hop.csv` đến 1e-9.
- Chạy `du_doan` trên 5 dòng thiếu cột: phải báo lỗi rõ ràng, không được trả kết quả sai.

---

## 6. A5 — (TUỲ CHỌN) TỰ SINH NHÃN TRÊN TESTBED 5G RIÊNG

Bước này chỉ cần khi model sẽ được triển khai trên một mạng 5G **khác** 5GTN Oulu. A2 cho biết cần khoảng bao nhiêu nhãn.

| | |
|---|---|
| **Input** | pcap bắt trên giao diện N3/S1-U của testbed, gồm (a) lưu lượng UE bình thường và (b) tấn công chạy có kịch bản (hping3, nmap, slowloris…), ghi lại IP máy tấn công và mốc thời gian |
| **Xử lý** | Bóc GTP-U → Argus → CSV với các trường như 5G-NIDD → ánh xạ bằng logic của `01_lam_sach_5gnidd.py` → gán nhãn theo IP máy tấn công + khoảng thời gian |
| **Output** | `experiment_5g_adaptation/data/<ten_testbed>_loi18.parquet` cùng schema → dùng làm "5G-train" mới ở A1/A2 |
| **Lưu ý** | Bật thống kê jitter và độ dài payload khi chạy Argus: 5G-NIDD thiếu hai thứ này nên `sinpkt`/`sjit` đang phải xấp xỉ. Giữ timestamp đầy đủ, để không lặp lại lỗi `ct_*` theo thứ tự dòng của 5G-NIDD |

Không chạy được trên máy này vì không có testbed. Mình sẽ viết script ánh xạ khi có pcap.

---

## 7. THỨ TỰ CHẠY VÀ ĐIỂM DỪNG

1. **A1.** Nếu BS2 ROC-AUC < 0,99 hoặc UNSW giảm > 0,01: **dừng** để chẩn đoán trước khi làm tiếp. Điều này mâu thuẫn với P3 đã đo.
2. **A2** và **A3** độc lập, chạy song song được.
3. **A4** sau cùng, dùng kết quả của cả ba.

Tổng thời gian máy ước khoảng 1,5 giờ. Mỗi script có chế độ `QUICK=1` (40 cây) để thử nhanh trước.
