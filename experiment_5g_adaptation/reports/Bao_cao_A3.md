# Báo cáo A3: Leave-one-attack-out (bắt tấn công 5G chưa thấy)

**Ngày chạy:** 27/10/2026 · bản FULL (300 cây, seed 42) · khoảng 20 phút
**Kế hoạch:** `docs/Ke_hoach_A_hoc_co_nhan_5G.md` §4
**Script:** `src/A3_loao.py`
**Số liệu gốc:** `results/A3_loao/tables/A3_loao.csv`, `A3_ket_qua.json` · hình `results/A3_loao/figures/A3_loao.png` · log `results/A3_loao/logs/A3_log.txt`

---

## 0. TÓM TẮT

| Câu hỏi | Kết quả |
|---|---|
| Model có bắt được loại tấn công 5G **chưa thấy** không? | **Tuỳ loại, chia thành hai nhóm rõ rệt.** Flood và scan "gói trần" (UDPFlood, SYNFlood, ICMPFlood, SYNScan) vẫn bắt được **100%**. Tấn công **giống lưu lượng ứng dụng thật** thì bị lọt: **HTTPFlood 50%**, **UDPScan 47%**, **TCPConnectScan 0,6%**. |
| UNSW có giúp không (H4)? | **Không.** Chỉ giúp 1/8 loại (SlowrateDoS +0,07), cần ≥ 2 loại. Các loại còn lại chênh 0 hoặc âm. |
| Dự đoán theo loại trong kế hoạch | **Đúng 0/8** theo khoảng đã định. Kế hoạch đánh giá **quá bi quan** với flood/scan gói trần và **quá lạc quan** với HTTPFlood, TCPConnectScan. |
| Điểm dừng | Không kích hoạt. Recall các tấn công **đã thấy** thấp nhất là 0,9985 (≥ 0,99). Việc giấu một loại không làm hỏng các loại khác. |
| Ý nghĩa với A1 | Con số ≈ 99,9% recall của A1-2 trên BS2 **chỉ đúng với các loại tấn công đã có trong train**. Với tấn công mới dạng ứng dụng, model có thể lọt một nửa hoặc gần hết. |

---

## 1. KẾT QUẢ (BS2, ngưỡng chọn trên 5G-val bỏ T, FPR ≤ 0,10)

| Loại bị giấu | n (BS2) | Dự đoán (A3-a) | **Recall T, A3-a** | **Recall T, A3-b** | FPR Benign a / b | ROC-AUC Benign vs T, a / b | Recall tấn công đã thấy a / b |
|---|---|---|---|---|---|---|---|
| HTTPFlood | 64.691 | Cao (≥ 0,9) | **0,498** ❌ | 0,480 | 0,073 / 0,081 | 0,778 / 0,700 | 1,000 / 1,000 |
| SlowrateDoS | 37.032 | Cao (≥ 0,9) | 0,877 ❌ (sát) | **0,949** | 0,068 / 0,072 | 0,946 / 0,939 | 0,999 / 0,999 |
| UDPFlood | 30.656 | TB–cao (0,6–0,95) | **1,000** ❌ (cao hơn) | 1,000 | 0,078 / 0,082 | 0,923 / 0,935 | 0,999 / 0,999 |
| TCPConnectScan | 10.028 | Thấp–TB (0,2–0,6) | **0,006** ❌ (thấp hơn) | 0,005 | **0,120** / **0,025** | 0,860 / 0,647 | 1,000 / 1,000 |
| SYNFlood | 4.929 | TB–cao (0,6–0,95) | **1,000** ❌ (cao hơn) | 1,000 | 0,079 / 0,082 | 0,925 / 0,993 | 0,999 / 1,000 |
| SYNScan | 519 | TB (0,4–0,8) | **1,000** ❌ (cao hơn) | 1,000 | 0,077 / 0,069 | 0,997 / 0,994 | 1,000 / 0,999 |
| ICMPFlood | 462 | Thấp (< 0,4) | **1,000** ❌ (cao hơn) | 1,000 | 0,077 / 0,079 | 0,999 / 0,999 | 0,999 / 1,000 |
| UDPScan | 209 | Thấp (< 0,4) | 0,474 ❌ (cao hơn) | 0,474 | 0,077 / 0,080 | 0,702 / 0,802 | 1,000 / 1,000 |

Mốc A1 (khi đã thấy loại đó): recall ≈ 1,0 ở mọi loại · FPR Benign A1-1 0,078 / A1-2 0,079.

**Ghi chú về cách chấm dự đoán:** tiêu chí là "recall rơi đúng khoảng". UDPFlood và SYNFlood đạt 1,0, vượt mức trên 0,95 của khoảng "Trung bình–cao", nên bị tính là sai. Về **hướng**, kế hoạch đúng ở SlowrateDoS (cao) và sai ở 6 loại còn lại.

---

## 2. ĐỌC KẾT QUẢ

1. **Model 5G thực chất đã học "thế nào là Benign 5G".** Bất cứ thứ gì lệch xa hồ sơ Benign đều bị bắt, kể cả loại chưa từng thấy. Flood và scan dùng gói trần (40–60 byte, không payload, rate cao hoặc rất ít gói) nằm rất xa Benign, nên recall vẫn 100%. Đây là phần **tổng quát hoá tốt**.
2. **Lỗ hổng là tấn công bắt chước lưu lượng ứng dụng.**
   - **HTTPFlood** gồm kết nối TCP hoàn chỉnh tới cổng 80, giống duyệt web của điện thoại. Khi không có HTTPFlood trong train, model chỉ bắt được một nửa (nhờ gần SlowrateDoS).
   - **TCPConnectScan** có bắt tay đầy đủ và ít gói, gần như không phân biệt được với kết nối TCP ngắn của Benign. Recall 0,6%.
   - **UDPScan** chỉ có 209 flow, và một nửa trông như UDP Benign.

   ROC-AUC Benign vs T vẫn ở mức 0,65–0,86, tức có thông tin xếp hạng. Nhưng ở ngưỡng FPR ≤ 0,10 thì không đủ tách.
3. **Ngưỡng của A3-a khi giấu TCPConnectScan rất thấp (0,0011).** Không có lớp TCPConnectScan, 5G-val tách gần như tuyệt đối nên ngưỡng tụt sát 0. Sang BS2, FPR Benign lên **0,12**, vượt giới hạn. Đây cùng hiện tượng với A1-6: tập val "quá dễ" làm ngưỡng không ổn định.
4. **A3-b khi giấu TCPConnectScan có FPR Benign chỉ 0,025,** thấp hơn hẳn mọi cấu hình khác (A1-2 là 0,079), trong khi recall các tấn công đã thấy vẫn ≈ 1,0. Hai điều suy ra:
   - Phần lớn báo động giả Benign của A1-2 **đến từ lớp TCPConnectScan**. Cùng kết luận với ma trận đa lớp A1-4: 1.017 flow Benign bị nhầm thành TCPConnectScan.
   - Bỏ lớp đó thì gần như không còn báo động giả, nhưng cũng mất khả năng bắt quét TCP-connect. Đây là **đánh đổi trực tiếp**, không có lời giải miễn phí với bộ feature hiện tại.
5. **UNSW không giúp bắt tấn công 5G mới (H4 sai).** Ngoại lệ duy nhất là SlowrateDoS (+0,07). Có thể vì UNSW có nhiều kết nối HTTP dài dạng DoS/Exploits, gần với slowloris. Với HTTPFlood, UNSW còn làm giảm (−0,02), ROC-AUC từ 0,78 xuống 0,70.

---

## 3. KẾT LUẬN

| | |
|---|---|
| **Khả năng bắt tấn công mới** | Tốt với tấn công volumetric hoặc gói trần. **Kém** với tấn công dạng ứng dụng hoặc kết nối hoàn chỉnh (HTTPFlood 50%, TCPConnectScan ≈ 0%) |
| **Vai trò của UNSW** | Không giúp tổng quát hoá sang tấn công 5G mới. Giá trị của nó trong model gộp chỉ là **giữ được khả năng bắt tấn công kiểu UNSW** (A1) |
| **Hệ quả khi báo cáo** | Phải ghi rõ: con số 99,9% recall của A1-2 là cho **các loại tấn công đã có nhãn**. Tấn công mới dạng ứng dụng cần có nhãn mới (A5) hoặc một lớp phát hiện riêng (ngoài phạm vi kế hoạch A) |
| **Ghi nhận cho A4** | Model card phải nêu giới hạn này, kèm bảng recall khi chưa thấy từng loại. Ngưỡng 5G nên kiểm tra lại trên dữ liệu độc lập, vì ngưỡng chọn trên val "quá dễ" có thể tụt sát 0 |
