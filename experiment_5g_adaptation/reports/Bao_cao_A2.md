# Báo cáo A2: cần bao nhiêu nhãn 5G

**Ngày chạy:** 27/10/2026 · bản FULL (300 cây, 5 seed) · khoảng 50 phút
**Kế hoạch:** `docs/Ke_hoach_A_hoc_co_nhan_5G.md` §3
**Script:** `src/A2_few_shot.py`
**Số liệu gốc:**
- `results/A2_few_shot/tables/`: `A2_tung_lan.csv` (từng lần chạy), `A2_tong_hop.csv` (trung bình ± SD), `A2_ket_qua.json`
- `results/A2_few_shot/figures/A2_duong_cong.png`
- `results/A2_few_shot/logs/A2_log.txt`

> **Ghi chú quy trình:** lần chạy song song đầu tiên lỗi đường dẫn (A2 không chạy, A3 vẫn chạy đúng). Các bảng lúc đó là của bản thử QUICK. A2 đã được chạy lại riêng với đường dẫn tuyệt đối; mọi số dưới đây là bản FULL.

---

## 0. TÓM TẮT

| Câu hỏi | Kết quả |
|---|---|
| **Cần bao nhiêu nhãn 5G?** | **~2.000 nhãn** nếu chỉ dùng 5G (A2-a) hoặc gộp có cân miền (A2-c). Gộp kiểu A1-2 với trọng số bằng nhau (A2-b) cần **~5.000 nhãn**. Cả hai đều cộng thêm ~n/4 nhãn validation để chọn ngưỡng. |
| H1: ít nhãn thì UNSW gây hại? | **Đúng.** ROC-AUC A2-a − A2-b = +0,108 (n = 50), +0,060 (100), +0,029 (200). |
| H2: cân miền thu hẹp khoảng cách? | **Đúng.** A2-c lấp được 35% / 54% / 65% khoảng cách ở n = 50 / 100 / 200. |
| H3: chọn ngưỡng trên val gộp là sai? | **Sai.** FPR của A2-d **không** cao hơn A2-b ≥ 0,2, ở nhiều mức n còn thấp hơn. Bất ngờ là ngưỡng gộp **ổn định hơn nhiều** (SD FPR 0,02 so với 0,1–0,3). |
| Nút thắt khi ít nhãn | **Không phải xếp hạng mà là ngưỡng.** Với 50 nhãn, A2-a đã đạt ROC-AUC 0,96, nhưng FPR dao động 0,05–0,29 giữa các seed, vì ngưỡng chọn trên chỉ ~2 flow Benign. |
| UNSW có bị ảnh hưởng? | **Không.** UNSW test-final giữ 0,957 (A2-b) và 0,956 (A2-c) ở mọi n. |
| Điểm dừng | Không kích hoạt. A2-b ở n = 20.000 đạt BS2 ROC-AUC 0,996 ≥ 0,99. |

---

## 1. KẾT QUẢ (BS2, ngưỡng miền; trung bình ± SD qua 5 seed)

| n nhãn 5G | A2-a chỉ 5G: ROC / FPR | A2-b UNSW+5G (A1-2): ROC / FPR | A2-c cân miền: ROC / FPR | A2-d (ngưỡng gộp): FPR | UNSW ROC (A2-b) |
|---|---|---|---|---|---|
| 50 | **0,960** ± 0,014 / 0,16 ± 0,10 | 0,853 ± 0,015 / **0,40 ± 0,32** | 0,890 / 0,25 ± 0,23 | 0,32 ± 0,02 | 0,957 |
| 100 | 0,964 / 0,12 ± 0,13 | 0,905 / 0,19 ± 0,13 | 0,937 / 0,07 ± 0,03 | 0,29 ± 0,03 | 0,957 |
| 200 | 0,977 / 0,16 ± 0,12 | 0,948 / 0,21 ± 0,11 | 0,967 / 0,18 ± 0,12 | 0,22 ± 0,02 | 0,957 |
| 500 | 0,987 / 0,13 ± 0,01 | 0,976 / 0,20 ± 0,10 | 0,985 / 0,14 ± 0,07 | 0,16 ± 0,02 | 0,957 |
| 1.000 | 0,989 / 0,11 ± 0,03 | 0,984 / 0,16 ± 0,07 | 0,990 / 0,12 ± 0,05 | 0,12 ± 0,02 | 0,957 |
| **2.000** | **0,991 / 0,089** ✅ | 0,990 / 0,127 | **0,993 / 0,090** ✅ | 0,090 ± 0,015 | 0,958 |
| **5.000** | 0,994 / 0,093 | **0,994 / 0,102** ✅ | 0,995 / 0,077 | **0,071 ± 0,002** | 0,958 |
| 20.000 | 0,996 / 0,088 | 0,996 / 0,110 | 0,997 / 0,109 | 0,065 ± 0,010 | 0,957 |
| *Mốc A1-2 (166.411)* | *0,9976 / 0,079 (A1-1)* | *0,9976 / 0,079* | | | *0,955* |

Recall trên BS2 ≥ 0,99 từ n = 1.000 với A2-a, A2-c, và từ n = 2.000 với A2-b.

**n tối thiểu đạt mục tiêu** (ROC-AUC ≥ 0,99 và FPR ≤ 0,12, theo trung bình):

| A2-a | A2-b | A2-c | A2-d |
|---|---|---|---|
| **2.000** | 5.000 | **2.000** | 5.000 |

---

## 2. SO VỚI KỲ VỌNG

| Kỳ vọng trong kế hoạch | Thực tế | |
|---|---|---|
| n = 50–100: ROC-AUC 0,90–0,96 (A2-a) | 0,960 / 0,964 | ✅ (ở cận trên) |
| n = 50–100: FPR 0,15–0,30 | 0,16 / 0,12 | ✅ gần đúng, nhưng SD rất lớn |
| n = 200: ROC-AUC ≈ 0,965 | 0,977 | ✅ (tốt hơn) |
| **n = 1.000–2.000: ROC-AUC ≥ 0,99, FPR ≤ 0,12** | 1.000: 0,989 / 0,108 · 2.000: 0,991 / 0,089 | ✅ đạt ở 2.000, sát nút ở 1.000 |
| n ≥ 5.000: ROC-AUC ≥ 0,994, FPR 0,08–0,10 | 0,994–0,996 / 0,088–0,093 | ✅ |
| UNSW ROC-AUC (A2-b) ≈ 0,955 ở mọi n | 0,957 | ✅ |
| A2-c có thể làm UNSW giảm khi n nhỏ | 0,9565 so với 0,9572 | ❌ không giảm đáng kể |
| H1 đúng | Đúng | ✅ |
| H2 đúng | Đúng | ✅ |
| **H3 đúng** | **Sai** | ❌ (xem §3.3) |

---

## 3. ĐỌC KẾT QUẢ

1. **Khi ít nhãn, UNSW là gánh nặng (H1).** Với 50 nhãn 5G, model gộp có 79.147 dòng UNSW so với 50 dòng 5G, nên cây gần như chỉ học UNSW. ROC-AUC 0,853, thấp hơn hẳn 0,960 của model chỉ 5G. Khoảng cách biến mất từ ~2.000 nhãn.
2. **Cân miền gỡ lại phần lớn (H2).** Cho 5G 50% tổng trọng số giúp A2-c đạt mục tiêu ở **2.000 nhãn**, giống A2-a, trong khi **vẫn giữ UNSW 0,956**. Nếu phải dùng một model chung cho cả hai miền mà nhãn 5G ít, đây là cách nên dùng.
3. **Chọn ngưỡng trên val gộp không tệ như dự đoán (H3 sai).**
   - Dự đoán dựa trên P4 ở `experiment_5gnidd`, nơi UNSW-DR có tỷ lệ tấn công chỉ 0,11, khác với ở đây.
   - Ở A2, val gộp có ~16.000 Normal UNSW nên ngưỡng **rất ổn định** (~0,73, SD FPR ≤ 0,03). Nhưng ngưỡng đó do UNSW quyết định, nên với n ≤ 200 FPR vẫn **0,22–0,32**, cao hơn mục tiêu.
   - Từ ~2.000 nhãn trở lên, ngưỡng gộp lại cho FPR **thấp nhất** (0,065–0,09), đổi lại recall thấp hơn chút (0,993–0,996).
4. **Nút thắt thật khi ít nhãn là chọn ngưỡng, không phải học xếp hạng.** Với 50–200 nhãn, ROC-AUC đã 0,96–0,98, nhưng FPR giữa các seed dao động rất mạnh: ví dụ n = 200, A2-a có FPR từ 0,011 đến 0,353. Nguyên nhân là mẫu validation n/4 chỉ có 2–10 flow Benign. Từ **n = 500 (125 nhãn val, ~25 Benign)**, SD của FPR với A2-a giảm còn 0,01.

---

## 4. KẾT LUẬN VÀ GHI NHẬN CHO A4

| | |
|---|---|
| **Số nhãn khuyến nghị khi đưa sang mạng 5G mới** | **~2.000 nhãn train + ~500 nhãn validation** (đã có tỷ lệ Benign tự nhiên, ~19%). Dùng model chỉ 5G hoặc model gộp **cân miền** |
| **Nếu giữ đúng công thức A1-2 (trọng số bằng nhau)** | Cần ~5.000 nhãn. Model đóng gói ở A1 học trên 166.411 nhãn nên không bị ảnh hưởng |
| **Ngưỡng** | Chọn trên nhãn 5G khi có ≥ ~500 nhãn val. Dưới mức đó, ngưỡng không tin được; nên ghi rõ trong model card |
| **Giới hạn** | Kết quả đo trên BS2, dùng chung công cụ tấn công với BS1. Số nhãn cần cho một mạng 5G khác hẳn có thể lớn hơn. A3 cho thấy tấn công dạng ứng dụng chưa có nhãn sẽ bị lọt bất kể số nhãn của các loại khác |
