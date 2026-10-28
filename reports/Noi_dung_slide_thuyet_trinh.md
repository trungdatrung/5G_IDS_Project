# NỘI DUNG SLIDE THUYẾT TRÌNH (bản 10 slide)
## Dự án 5G IDS — Phát hiện xâm nhập trên UNSW-NB15


## SLIDE 1 — Trang bìa

**[SLIDE]**

# So sánh 3 model phát hiện xâm nhập trên UNSW-NB15
### Khi "Accuracy tăng" không có nghĩa là "model tốt hơn"


## SLIDE 2 — Dữ liệu và bước làm sạch

**[SLIDE]**

### Bài toán
Phân loại nhị phân luồng mạng: `label` = 0 (Normal) / 1 (Attack)

### Dữ liệu sau làm sạch — **31 feature → 183 cột** sau One-Hot

| | Số dòng | Tỷ lệ Attack |
|---|---|---|
| Train | 98.934 | 49,64% |
| Test | 50.567 | **36,65%** |

### Đã loại 13 cột
- `id` + **8 feature ô nhiễm** (`sttl`, `dttl`, `ct_state_ttl`…) — D'hooge et al., PST 2022
- 3 feature không có khả năng phân biệt
- **Không** dùng `attack_cat` làm feature

### Hệ quả: tỷ lệ Attack thay đổi khác nhau ở 2 tập

| | Trước làm sạch | Sau làm sạch |
|---|---|---|
| Train | 68,06% | 49,64% |
| Test | 55,06% | 36,65% |

> ⚠️ Bước làm sạch tự nó tạo ra **lệch tỷ lệ lớp 13 điểm**

**[NÓI]**

Hai ý phải nói:

1. Nhiều bài báo đạt 97–98% trên bộ này vì **giữ lại** `sttl`, `ct_state_ttl` —
   những feature rò rỉ từ cách sinh dữ liệu chứ không phải bản chất tấn công.
   Nhóm em bỏ đi, chấp nhận số thấp hơn nhưng trung thực.
2. Lệch 13 điểm này sẽ quay lại ở Slide 8 như một nguyên nhân chính.

*Nếu thầy hỏi "chứng minh feature ô nhiễm đi":* nói thật — nhóm làm theo bài báo,
**chưa chạy thí nghiệm đối chứng**. Đó là việc nên bổ sung.

---

## SLIDE 3 — Ba model và điều kiện so sánh

**[SLIDE]**

### Cả 3 đều là Random Forest — **cùng feature, cùng tiền xử lý**

| | Lần 1 | Lần 2 | Lần 3 |
|---|---|---|---|
| Số cây | 100 | 300 | 300 |
| `max_depth` | **None** | 20 | 20 |
| `max_features` | `'sqrt'` (~13) | 0,5 (~91) | 0,5 (~91) |
| Calibration | — | — | isotonic |
| **Ngưỡng** | **0,500** | **0,515** | **0,711** |
| `random_state` | 42 | 42 | 42 |

> Mọi khác biệt kết quả **chỉ** có thể đến từ: tham số rừng, calibration, hoặc ngưỡng

### Tập đánh giá chung: `test-final`
- **25.284 dòng** (16.017 Normal / 9.267 Attack)
- Tập **duy nhất** không model nào dùng để huấn luyện / chọn tham số / chọn ngưỡng
- Quy tắc thống nhất: `Attack nếu P(Attack) ≥ ngưỡng`

**[NÓI]**

Nhấn mạnh dòng trích dẫn: vì feature và tiền xử lý giống hệt nhau, ta loại trừ được
mọi nguyên nhân khác — đây là thiết kế thí nghiệm sạch.

Về tập đánh giá: notebook 02–03 báo cáo trên toàn tập test, notebook 04 chia đôi và
dùng nửa đầu để chọn ngưỡng. Nên nhóm em thống nhất đánh giá cả 3 trên nửa còn lại.

---

## SLIDE 4 — Kết quả 3 lần chạy

**[SLIDE]**

### Trên `test-final` (25.284 dòng), cùng quy tắc quyết định

| | Accuracy | Precision | Recall | F1 | FPR |
|---|---|---|---|---|---|
| **Lần 1** | 0,8156 | 0,6773 | 0,9491 | 0,7905 | 26,2% |
| **Lần 2** | 0,8287 | 0,6965 | 0,9438 | 0,8015 | 23,8% |
| **Lần 3** | 0,8820 | 0,8251 | 0,8605 | 0,8424 | 10,6% |

### Ma trận nhầm lẫn

| | TN | FP | FN | TP |
|---|---|---|---|---|
| Lần 1 | 11.827 | 4.190 | 472 | 8.795 |
| Lần 2 | 12.206 | 3.811 | 521 | 8.746 |
| Lần 3 | 14.327 | 1.690 | **1.293** | 7.974 |

Accuracy **+6,6 điểm** · Precision **+14,8 điểm** · nhưng Recall **−8,9 điểm**

> ❓ Mức tăng này đến từ đâu? Model tốt lên, hay chỉ đổi cách quyết định?

**[NÓI]**

**Đừng kết luận gì ở slide này.** Chỉ đặt câu hỏi ở dòng cuối rồi chuyển slide —
đây là điểm treo dẫn vào ba slide phân tích tiếp theo.

Chèn hình `reports/confusion_matrices.png` nếu còn chỗ.

---

## SLIDE 5 — Nhìn lại bằng cấu trúc lỗi

**[SLIDE]**

| | Tổng lỗi | FP chiếm | Cảnh báo bắn ra | Tấn công thật |
|---|---|---|---|---|
| Lần 1 | 4.662 | **89,9%** | 12.985 | 9.267 |
| Lần 2 | 4.332 | **88,0%** | 12.557 | 9.267 |
| Lần 3 | 2.983 | **56,7%** | 9.664 | 9.267 |

### Đọc hiểu
- Lần 1 bắn ra **12.985** cảnh báo cho **9.267** tấn công thật → **thừa 40%**
- Ở lần 1–2, gần **90%** số lỗi là **báo động giả**
- Lớp Normal chiếm **63,35%** tập test → giảm 1 điểm FPR kéo Accuracy lên ~0,63 điểm

> 💡 **Accuracy tăng không phải vì model giỏi hơn, mà vì cắt bớt loại lỗi chiếm đa số**

### Giá phải trả

| Bước | Giảm FP | Thêm FN | Tỷ lệ |
|---|---|---|---|
| Lần 1 → 2 | −379 | +49 | **1 : 7,7** |
| Lần 2 → 3 | −2.121 | +772 | **1 : 2,7** |

**[NÓI]**

Slide dễ hiểu và thuyết phục nhất — dành thời gian cho nó.

> "Nếu chỉ nhìn Accuracy, ta tưởng model tiến bộ đều. Nhưng tách ra thì gần 90% lỗi
> của lần 1 và 2 là báo động giả. Và vì Normal chiếm đa số tập test, chỉ cần giảm
> báo động giả là Accuracy tự tăng — không cần model giỏi hơn."

Ý nghĩa nghiệp vụ: **FN = một cuộc xâm nhập không bị phát hiện. FP = thời gian của
người phân tích.** Hai loại lỗi chi phí rất khác nhau, Accuracy cộng gộp cả hai.

---

## SLIDE 6 — Lần 1 → Lần 2: cải thiện THẬT nhưng nhỏ

**[SLIDE]**

### Thay đổi
`max_depth`: None → **20** · `max_features`: `'sqrt'` → **0,5** · 100 → **300 cây**

### Bằng chứng cải thiện thật — chỉ số KHÔNG phụ thuộc ngưỡng

| | Lần 1 | Lần 2 |
|---|---|---|
| ROC-AUC | 0,9548 | 0,9600 |
| **PR-AUC** | 0,9264 | **0,9420** (+1,56 điểm) |

### Overfit đã giảm

| | Accuracy trên dữ liệu fit | Validation | Khoảng chênh |
|---|---|---|---|
| Cấu hình lần 1 | **1,0000** | 0,9268 | 7,3 điểm |
| Cấu hình lần 2 | 0,9775 | 0,9322 | **4,5 điểm** |

### Nhưng vì sao chỉ +1,3 điểm Accuracy?
- 10 cấu hình tốt nhất có CV PR-AUC **0,9822–0,9829**, std ~0,0015 → **nằm trong nhiễu**
- Khoảng chênh validation → test vẫn ~**10 điểm**

**[NÓI]**

Giải thích con số **1,0000**: với `max_depth=None` và `min_samples_leaf=1`, cây mọc
đến khi mỗi lá thuần một lớp, kể cả lá chỉ chứa 1 mẫu. Model thuộc lòng toàn bộ tập
train — FP = 0, FN = 0. Đặt `max_depth=20` chặn được việc này.

Câu kết: *"Tinh chỉnh tham số xử lý được **overfit**, nhưng không xử lý được
**lệch phân bố**. Đó là trần của bước này."*

---

## SLIDE 7 — Lần 2 → Lần 3: cú lật

**[SLIDE]**

### Thay đổi
Giữ **nguyên** tham số rừng · thêm isotonic calibration · ngưỡng 0,515 → **0,711**

### ⚠️ Chỉ số không phụ thuộc ngưỡng KHÔNG đổi

| | Lần 2 | Lần 3 |
|---|---|---|
| ROC-AUC | 0,9600 | **0,9595** |
| PR-AUC | 0,9420 | **0,9416** |

### Bằng chứng tách bạch — cùng tập `test-final`

| | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| Lần 2 @0,515 | 0,8287 | 0,6965 | 0,9438 | **0,8015** |
| Lần 3 calibrate **@0,5** | 0,8289 | 0,6976 | 0,9413 | **0,8013** |
| Lần 3 calibrate **@0,711** | 0,8820 | 0,8251 | 0,8605 | 0,8424 |

> ✅ Ở **cùng điểm vận hành**, calibration không đổi gì (0,8013 vs 0,8015)
> ✅ Toàn bộ chênh lệch đến từ **dời ngưỡng**, không phải model tốt hơn

**[NÓI]** — Slide quan trọng nhất của bài.

Lý do toán học:

> "ROC-AUC chỉ phụ thuộc vào **thứ tự xếp hạng**, không phụ thuộc giá trị xác suất.
> Isotonic calibration là hàm **đơn điệu không giảm**, mà phép biến đổi đơn điệu
> **bảo toàn thứ tự**. Vậy về nguyên lý, calibration **không thể** làm thay đổi
> ROC-AUC. Số liệu đo được khớp đúng với lý thuyết."

Vì sao dời ngưỡng lại hiệu quả: FP nằm sát biên (trung vị `P(Attack)` = 0,648) còn
TP nằm xa (trung vị 0,992). 63% số FP nằm trong [0,50; 0,70). Nên cắt ở 0,711 bỏ
được 55,7% FP mà chỉ mất 8,8% TP.

Bổ sung: Brier score trên test 0,10673 → 0,10688 — calibration còn **xấu đi** chút ít.

---

## SLIDE 8 — Nguyên nhân gốc: vấn đề nằm ở DỮ LIỆU

**[SLIDE]**

### Vùng "bắt tay TCP chậm" (`tcprtt > 0,01 s`)

| | % Normal là chậm | Tỷ lệ Attack:Normal |
|---|---|---|
| **Train** | 19,0% | **4,01 : 1** |
| **Test** | 41,5% | **1,04 : 1** |

- Train: `P(Attack \| chậm)` = **0,80** → model học rất chắc quy tắc này
- Test: `P(Attack \| chậm)` = **0,51** → quy tắc **mất sạch tác dụng**

### Phân rã Precision — `Precision = TPR·π / (TPR·π + FPR·(1−π))`

| | TPR | FPR | π | Precision |
|---|---|---|---|---|
| Validation | 0,9577 | 0,0929 | 0,4964 | **0,9104** |
| Test | 0,9504 | **0,2627** | 0,3665 | **0,6767** |

Precision rơi **0,2337**, trong đó:
- Do **tỷ lệ lớp** đổi: **0,0540** (~23%)
- Do **FPR tăng** gần 3 lần: **0,1294** (~55%)

> Recall gần như không đổi (0,9577 → 0,9504) — **toàn bộ vấn đề nằm ở FPR**

### Bằng chứng độc lập
**Adversarial validation AUC = 0,8040** — chỉ nhìn feature đã đoán được dòng thuộc
train hay test (0,5 = không phân biệt được)

**[NÓI]** — Phát hiện có giá trị nhất của bài.

> "Model không sai. Nó học đúng một quy tắc **có thật** trong tập train: bắt tay
> chậm thì khả năng là tấn công cao gấp 4 lần. Nhưng trong tập test, tỷ lệ đó chỉ
> còn 1,04 — gần như vô dụng. Đây không phải lỗi thuật toán mà là tính chất dữ liệu.
> Không tham số nào của Random Forest sửa được."

Thay vì nói chung chung "do dữ liệu lệch", nhóm em **tách được**: 23% do tỷ lệ lớp,
55% do model thật sự báo nhầm nhiều hơn.

*Thuật ngữ nếu được hỏi:* đây là **concept shift** (quan hệ nhãn–feature đổi), không
phải **covariate shift** (chỉ phân bố feature đổi).

---

## SLIDE 9 — Điểm yếu nhóm tự phát hiện & những gì đã thất bại

**[SLIDE]**

### ⚠️ Ngưỡng của lần 3 chọn bằng `test-dev` — **dữ liệu test CÓ NHÃN**
Lần 1 và lần 2 **không** được tiếp cận thông tin này

Phép đối chứng đã định trước — cùng model, ngưỡng chọn trên validation của train:

| Cách chọn ngưỡng | Ngưỡng | F1 trên `test-final` |
|---|---|---|
| Trên validation (phân bố train) | 0,4636 | **0,7884** |
| Trên `test-dev` (phân bố test) | 0,7106 | 0,8424 |
| *Lần 2 để so sánh* | 0,5152 | *0,8015* |

> **0,7884 còn thấp hơn lần 2** → phần lớn "cải tiến" của lần 3 là **lợi thế thông
> tin**, không phải lợi thế mô hình

### 3 hướng xử lý lệch phân bố — đều KÉM HƠN

| | F1 |
|---|---|
| Cấu hình chính lần 2 | **0,8005** |
| Ngưỡng chọn trên "validation giống test" | 0,7734 |
| + Importance weighting | 0,7723 |
| Thêm 4 feature tỷ lệ | 0,7968 |

**Lý do thất bại:** các kỹ thuật này giả định **covariate shift**, nhưng dữ liệu là
**concept shift** → đánh trọng số lại mẫu train không sửa được

**[NÓI]**

Chủ động nói ra điểm yếu. Giáo viên tinh sẽ tự tìm ra; nêu trước thì thành điểm cộng.

Vì sao hai ngưỡng cách xa nhau (0,46 vs 0,71) cho **cùng** ràng buộc FPR ≤ 0,10:
cùng một mức xác suất mang ý nghĩa khác nhau ở hai phân bố — traffic Normal của test
nằm sâu hơn trong vùng model coi là đáng ngờ.

Slide "thất bại" thường bị bỏ qua nhưng giáo viên đánh giá rất cao.

---

## SLIDE 10 — Kết luận và hướng phát triển

**[SLIDE]**

### 1. Lần 1 → Lần 2: model tốt lên THẬT, nhưng ít
PR-AUC **+1,56 điểm** · overfit giảm 7,3 → 4,5 điểm · nhờ `max_depth=20`

### 2. Lần 2 → Lần 3: model KHÔNG tốt lên
ROC-AUC 0,9600 vs 0,9595 — bằng nhau trong sai số.
Thứ thay đổi là **điểm vận hành**, không phải chất lượng mô hình

### 3. Nút thắt nằm ở DỮ LIỆU
Quy tắc "bắt tay chậm ⇒ Attack": **4,01:1** (train) → **1,04:1** (test)

### 4. Không xếp hạng "tốt nhất"

| | Recall | Cảnh báo đúng : giả |
|---|---|---|
| Lần 1–2 | 0,94 | ~2 : 1 |
| Lần 3 | 0,86 | ~5 : 1 |

> **FN** = xâm nhập không bị phát hiện · **FP** = thời gian người phân tích
> → Chọn điểm nào là quyết định **vận hành**, không phải kết luận kỹ thuật

### Hướng tiếp theo
Thí nghiệm đối chứng feature ô nhiễm · So sánh thuật toán khác · Xử lý concept
shift · Phân tích nhóm **Fuzzers** (Recall 0,816 — chiếm ~81% tổng FN)

**[NÓI]**

Kết lại bằng đúng câu mở đầu, tạo vòng tròn khép kín:

> "Quay lại câu hỏi ban đầu: Accuracy tăng từ 0,82 lên 0,88 có nghĩa model tốt hơn
> không? Câu trả lời: một phần nhỏ thì có, phần lớn thì không. Và nhóm em **đo được
> chính xác** phần nào là phần nào."

Tài liệu kèm: `notebooks/model_comparison_results.csv` ·
`reports/confusion_matrices.png` · `reports/Bao_cao_so_sanh_3_lan_chay.txt`

---
---

# SLIDE DỰ PHÒNG (chỉ mở khi được hỏi)

## DP-1 — Recall theo từng loại tấn công

| Loại | n | Recall lần 1 | Recall lần 2 |
|---|---|---|---|
| Exploits | 7.559 | 0,9836 | 0,9821 |
| **Fuzzers** | 4.436 | **0,8158** | **0,8102** |
| Reconnaissance | 2.262 | 0,9929 | 0,9929 |
| DoS | 1.677 | 0,9893 | 0,9863 |
| Generic | 1.430 | 0,9930 | 0,9937 |
| Analysis / Backdoor / Worms | 427 / 328 / 44 | 1,0000 | ~1,0000 |
| Shellcode | 370 | 0,9514 | 0,9459 |

> Fuzzers là điểm yếu duy nhất — chiếm ~81% tổng FN. Lý do: gửi dữ liệu ngẫu
> nhiên/dị dạng để dò lỗi nên luồng mạng giống traffic bình thường nhất.

## DP-2 — Bảng quét ngưỡng (model lần 3, trên `test-dev`)

| Ngưỡng | Precision | Recall | F1 | FPR |
|---|---|---|---|---|
| 0,50 | 0,6954 | 0,9417 | 0,8000 | 0,2387 |
| 0,60 | 0,7677 | 0,9005 | 0,8288 | 0,1576 |
| **0,7106** | **0,8328** | **0,8594** | **0,8459** | **0,0998** ← chọn |
| 0,80 | 0,8790 | 0,8256 | 0,8515 | 0,0657 |
| 0,90 | 0,9442 | 0,7485 | 0,8351 | 0,0256 |

> F1 cao nhất thực ra ở ngưỡng 0,80 (0,8515), **không** phải 0,7106. Lần 3 tối ưu
> **Recall dưới ràng buộc FPR ≤ 0,10**, không tối ưu F1.

## DP-3 — Vì sao không dùng SMOTE / cân bằng dữ liệu

- Train đã gần cân bằng: **49,64%** Attack
- `class_weight='balanced'` **đã có** trong không gian tìm kiếm — CV chọn `None`
- Vấn đề không phải mất cân bằng lớp, mà là **lệch phân bố giữa train và test**

## DP-4 — Chống rò rỉ dữ liệu & tái lập

- Encoder nằm **trong** `Pipeline` → chỉ `fit` trên train, test chỉ `transform`
- Mỗi notebook có `assert` kiểm tra `attack_cat` và 13 cột đã loại không có mặt
- One-Hot thay Label Encoding, tránh thứ tự giả (`tcp=113 > udp=112` là vô nghĩa)
- `handle_unknown='ignore'` xử lý `state` = `ACC`, `CLO` chỉ có trong test
- `random_state=42` ở cả 3 model · chạy lại notebook 01 cho file parquet **giống hệt**
- 5 notebook chạy hết, không cell lỗi: 9/9 · 8/8 · 15/15 · 18/18 · 10/10
