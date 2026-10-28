# Báo cáo A1: model gộp UNSW-NB15 + 5G-NIDD

**Ngày chạy:** 27/10/2026 · bản FULL (300 cây, seed 42) · thời gian chạy khoảng 12 phút
**Kế hoạch:** `docs/Ke_hoach_A_hoc_co_nhan_5G.md` §2
**Script:** `src/A1_model_gop.py`
**Số liệu gốc:**
- `results/A1_model_gop/tables/`: `A1_tong_hop.csv`, `A1_recall_theo_loai.csv`, `A1_importance.csv`, `A1_ket_qua.json`, `A1-4_cm_da_lop_*.csv`
- `results/A1_model_gop/figures/`: 9 hình ma trận nhầm lẫn
- `results/A1_model_gop/logs/A1_log.txt`

**Kiểm tra đầu vào:**
- Model NB07 tái lập accuracy UNSW test-final = 0,818620.
- Kích thước các tập đúng kế hoạch: UNSW train-fit 79.147 · 5G-train 166.411 · 5G-val 41.603 · BS2 171.542.

---

## 0. TÓM TẮT

| Câu hỏi | Kết quả |
|---|---|
| Có được **một** model tốt trên cả UNSW lẫn 5G không? | **Có.** A1-2 (LOI18, gộp, trọng số bằng nhau) đạt **mọi** kỳ vọng: BS2 ROC-AUC 0,9976 · FPR 0,079 · recall 0,9995. UNSW ROC-AUC 0,9554, chỉ giảm 0,0015 so với model chỉ học UNSW. |
| Điểm dừng (§7) | Không kích hoạt. BS2 ROC-AUC ≥ 0,99 và UNSW giảm ≤ 0,01 ở cả A1-2 lẫn A1-3. |
| Model được lưu | **A1-2**, lưu tại `models/A1_model_gop/rf_gop_loi18.joblib`. A1-3 hơn 0,003 điểm bal acc tổng, dưới mức 0,005, nên theo quy tắc chọn bản đơn giản hơn. |
| Dùng lại model NB07 | A1-5 (thêm cây 5G vào NB07) cho FPR trên 5G thấp nhất (0,026), nhưng UNSW mất 0,012 ROC-AUC. A1-6 (định tuyến) giữ nguyên NB07, nhưng ngưỡng 5G không ổn định (FPR 0,144). |

---

## 1. KẾT QUẢ SO VỚI KỲ VỌNG (ngưỡng riêng từng miền, FPR ≤ 0,10 chọn trên dev/val)

| Chỉ số | Kỳ vọng | A1-0 chỉ UNSW | A1-1 chỉ 5G | **A1-2 gộp** | A1-3 cân miền | A1-4 đa lớp | A1-5 NB07+warm | A1-6 định tuyến |
|---|---|---|---|---|---|---|---|---|
| BS2 ROC-AUC | ≥ 0,995 | 0,309 | 0,9976 | **0,9976** ✅ | 0,9976 ✅ | 0,9967 | 0,9973 | 0,9994 |
| BS2 FPR | ≤ 0,10 | 0,147 | 0,078 | **0,079** ✅ | 0,076 ✅ | 0,092 | **0,026** | 0,144 ❌ |
| BS2 recall | ≥ 0,99 | 0,015 | 0,9997 | **0,9995** ✅ | 0,9994 ✅ | 0,9996 | 0,9957 | 1,0000 |
| BS2 bal acc | — | 0,434 | 0,961 | **0,960** | 0,962 | 0,954 | **0,985** | 0,928 |
| UNSW ROC-AUC | giảm ≤ 0,005 | 0,9569 (mốc) | 0,477 | **0,9554** ✅ (−0,0015) | 0,9561 ✅ | 0,9583 | 0,9474 (−0,012 so với NB07) | **0,9594** (= NB07) |
| UNSW bal acc | ≥ 0,865 | 0,874 | 0,472 | **0,872** ✅ | 0,874 ✅ | 0,876 | 0,871 | 0,878 |
| UNSW FPR | ≈ 0,10 | 0,104 | 0,104 | 0,108 | 0,106 | 0,106 | 0,102 | 0,105 |

**Dự báo nào đúng, dự báo nào sai:**

| Dự báo trong kế hoạch | Thực tế | |
|---|---|---|
| A1-0 trên BS2 ≈ 0,31 | 0,309 | ✅ |
| A1-1 trên UNSW ≈ 0,48 | 0,477 | ✅ |
| A1-2/A1-3 đạt mọi kỳ vọng | Đạt | ✅ |
| A1-5: BS2 ≈ 0,997, FPR ≈ 0,03, UNSW giảm ≈ 0,012 | 0,9973 / 0,026 / −0,012 | ✅ |
| A1-6: BS2 ≈ 0,999, FPR ≈ 0,14, UNSW = NB07 | 0,9994 / 0,144 / 0,9594 | ✅ |

Không có dự báo nào sai. Kết quả này đã được lường trước, vì A1 lặp lại có hệ thống các phép đo P3, P5 và thử nghiệm nhanh trước đó.

---

## 2. RECALL THEO LOẠI TẤN CÔNG (ngưỡng từng miền)

**5G BS2:**

| Loại | n | A1-0 | **A1-2** | A1-5 | A1-6 |
|---|---|---|---|---|---|
| **Benign (= FPR)** | 23.016 | 0,147 | **0,079** | **0,026** | 0,144 |
| HTTPFlood | 64.691 | 0,035 | 0,999 | 0,992 | 1,000 |
| SlowrateDoS | 37.032 | 0,001 | 1,000 | 1,000 | 1,000 |
| UDPFlood | 30.656 | 0,000 | 1,000 | 1,000 | 1,000 |
| TCPConnectScan | 10.028 | 0,000 | 0,999 | 0,996 | 1,000 |
| SYNFlood | 4.929 | 0,000 | 1,000 | 1,000 | 1,000 |
| SYNScan | 519 | 0,000 | 1,000 | **0,896** | 1,000 |
| ICMPFlood | 462 | 0,000 | 1,000 | 1,000 | 1,000 |
| UDPScan | 209 | 0,000 | 1,000 | 0,981 | 1,000 |

**UNSW test-final:** A1-2 gần như trùng A1-0 ở mọi họ, chênh tối đa 0,02. Ví dụ Fuzzers 0,565 → 0,575, Shellcode 0,703 → 0,724. Học thêm 5G **không làm hỏng** khả năng bắt tấn công UNSW.

---

## 3. NHẬN XÉT

1. **Mô hình gộp không làm mất kiến thức về UNSW.** Thêm 166 nghìn flow 5G chỉ làm UNSW giảm 0,0015 ROC-AUC. Hai "khái niệm tấn công" cùng tồn tại được trong một RF, vì chúng nằm ở các vùng feature khác nhau.
2. **Cân miền (A1-3) gần như không khác gì (+0,003 điểm).** Với RF và lượng dữ liệu này, chênh lệch 79k so với 166k không gây vấn đề.
3. **Phần còn sai chủ yếu là báo động giả trên Benign 5G** (1.815 / 23.016 flow). Ma trận đa lớp A1-4 cho thấy Benign bị nhầm nhiều nhất thành **TCPConnectScan (1.017 flow)**, rồi SlowrateDoS (213) và HTTPFlood (194). Lý do: kết nối TCP ngắn của điện thoại trông giống một lần quét connect.
4. **Ngoài lỗi ở trên, A1-4 gần như không lẫn giữa hai miền.** Trên BS2 chỉ khoảng 60 flow bị gán vào lớp của UNSW. Trong 5G, chỉ có SlowrateDoS → HTTPFlood (2.300 flow, 6%) là lẫn đáng kể, mà cả hai đều là DoS trên HTTP.
5. **`proto` tăng importance từ 0,009 lên 0,085** khi gộp. Model dùng giao thức một phần để phân biệt miền, ví dụ SCTP và ICMP có tỷ lệ khác hẳn giữa hai bộ. Chưa thấy tác hại, nhưng A3 nên kiểm tra thêm.
6. **A1-5 (thêm cây vào NB07) có FPR 5G thấp nhất, nhưng có hai cái giá:**
   - UNSW mất 0,012 ROC-AUC.
   - Ngưỡng UNSW phải chọn lại: ở @0,5 recall UNSW chỉ còn 0,42, vì 300 cây 5G kéo điểm xuống. Ngưỡng đúng là 0,37.

   SYNScan cũng chỉ đạt 0,896. Phương án này hữu ích nếu mục tiêu là **ít báo động giả trên 5G**.
7. **Ngưỡng của A1-6 không ổn định.** Model 5G riêng (F31) tách BS1-val gần như hoàn hảo, nên ngưỡng được chọn rất thấp (0,0033). Sang BS2, FPR lên 0,144, vượt giới hạn 0,10. Đây là dấu hiệu quá khớp vào `ct_*` (shortcut theo thứ tự dòng), đúng như cảnh báo trong kế hoạch.

---

## 4. KẾT LUẬN VÀ VIỆC TIẾP THEO

| | |
|---|---|
| **Model mang sang A2–A4** | `rf_gop_loi18.joblib` (A1-2). Ngưỡng UNSW = 0,7177 · ngưỡng 5G = 0,3525 |
| **Nếu bắt buộc giữ NB07** | Dùng A1-5 (một model) hoặc A1-6 (hai model). A1-6 cần chọn lại ngưỡng 5G cho chắc hơn, hoặc bỏ `ct_*` |
| **Giới hạn** | BS2 dùng chung công cụ tấn công và server nạn nhân với BS1, nên các con số 0,997–0,999 là **lạc quan**. A3 (leave-one-attack-out) sẽ đo khả năng bắt tấn công mới |
| **Bước tiếp theo theo kế hoạch** | A2 (cần bao nhiêu nhãn 5G) và A3 (tấn công chưa thấy). Hai bước độc lập, chạy song song được |
