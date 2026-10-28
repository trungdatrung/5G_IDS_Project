# Truy nguyên nguyên nhân Accuracy thấp — rà soát độc lập toàn bộ pipeline

**Dự án:** 5G IDS / UNSW-NB15, phân loại nhị phân `label` (0 = Normal, 1 = Attack)
**Ngày chạy:** 03/10/2026
**Notebook:** `notebooks/06_Root_Cause_Audit.ipynb` (mới tạo, không ghi đè notebook 01–05)
**Số liệu gốc:** `reports/audit06/` — `thang_do_2x2x2.csv`, `cac_huong_khac_phuc.csv`,
`so_sanh_thuat_toan.csv`, `ket_qua_audit06.json`, `confusion_truoc_sau.png`
**Môi trường:** Python 3.11.16 · scikit-learn 1.9.1 · pandas 3.0.6 · không có XGBoost/LightGBM

**Kỷ luật đã áp dụng:** không sửa hay xoá bất kỳ dataset/notebook nào có sẵn; notebook mới chỉ
ghi vào `reports/audit06/`. `test-final` chỉ chạm ở bước báo cáo cuối. Mọi khẳng định đều kèm con
số tạo ra nó; không trích lại số của báo cáo cũ mà không tự đo lại.

---

## TÓM TẮT KẾT QUẢ

**Nguyên nhân KHÔNG nằm ở cách cài đặt mô hình.** Rà soát lại từng bước 01→05 không tìm ra lỗi nào.

**Nguyên nhân là cách chia train/test chính thức của UNSW-NB15 bị lệch phân bố**, cộng với một
lỗi vận hành có thật nhưng dễ sửa: để ngưỡng quyết định ở 0,5 trong khi mô hình học xác suất theo
tỷ lệ lớp của tập train (49,64% Attack) rồi bị chấm điểm trên tập có tỷ lệ khác hẳn (36,65%).

Đo bằng thiết kế giai thừa 2×2×2, ảnh hưởng lên Accuracy:

| Yếu tố | Mức ảnh hưởng |
|---|---|
| **Cách chia train/test** (chính thức → ngẫu nhiên) | **+0,0955** |
| Giữ lại 11 feature đã bỏ | +0,0112 |
| Bỏ bước khử trùng lặp | +0,0294 *(kèm rò rỉ test→train 10–48%)* |

Cách chia lớn hơn việc bỏ feature ô nhiễm **8,5 lần**.

Sau khắc phục: Accuracy **0,8186 → 0,9050**, FPR **0,2569 → 0,0561**, F1 **0,7932 → 0,8660**.
Nhưng phải đọc đúng: ~85% mức cải thiện đến từ **đặt lại điểm vận hành**, không phải từ model mạnh hơn.

---

## PHẦN 1 — RÀ SOÁT CÀI ĐẶT: KHÔNG CÓ LỖI

Mỗi bước được làm lại từ đầu, nêu vai trò + kết quả mong đợi, rồi kiểm chứng bằng số.

| Bước | Vai trò | Kiểm chứng | Kết quả |
|---|---|---|---|
| Đọc dữ liệu thô | Lấy đúng bộ chia chính thức | kích thước, NaN | train 175.341×45, test 82.332×45, 0 NaN — **ĐẠT** |
| `df_shrink` | Giảm bộ nhớ, không đổi nội dung | số dòng trùng trước/sau | giống hệt — **ĐẠT (có điều kiện)** |
| Bỏ cột | Loại feature ô nhiễm + metadata | danh sách cột | bỏ 11 cột, còn 31 feature — **ĐẠT** |
| Bỏ dòng trùng / mâu thuẫn | Chống rò rỉ và thuộc lòng | assert | không còn — **ĐẠT** |
| Đối chiếu `data/cleaned` | Hàm phải là bản sao trung thực | so từng giá trị | **TRÙNG KHÍT** 98.934×33 và 50.567×33 |
| One-Hot | Mã hoá định danh, không rò rỉ | encoder fit ở đâu, giá trị lạ | 183 cột; `state`=`ACC`/`CLO` → vector 0; fit **chỉ** trên train-fit — **ĐẠT** |
| Chia tập | Tách tập chọn khỏi tập báo cáo | kích thước | 79.147 / 19.787 / 25.283 / 25.284 — **ĐẠT** |
| Tái lập baseline | Số cũ có đúng không | Accuracy test-final | **0,8186** — khớp báo cáo cũ |

**Ghi chú trung thực về `df_shrink`:** nó hạ `float64` → `float32` nên **không** bảo toàn bit —
sai số tuyệt đối lớn nhất 6,2×10⁻², sai số tương đối ~10⁻⁷. Số dòng trùng đếm được giống hệt
trước và sau, nên bước khử trùng lặp không bị ảnh hưởng. Đây là một rủi ro tiềm ẩn đã được kiểm
tra chứ không phải một lỗi.

### Model đang underfit hay overfit?

| Tập | PR-AUC | Accuracy @0,5 |
|---|---|---|
| train-fit (học thuộc) | 0,9985 | 0,9775 |
| CV 5-fold trong train-fit | 0,9830 (±0,0015) | — |
| validation (cùng phân bố train) | 0,9849 | 0,9322 |
| test-dev (phân bố test) | 0,9429 | 0,8154 |
| test-final (phân bố test) | 0,9414 | 0,8186 |

- **Không underfit.** Trong phân bố train, Random Forest đạt PR-AUC ~0,98 và Accuracy ~0,93.
  Sức biểu diễn là thừa đủ.
- **Không phải overfit kiểu học thuộc.** train-fit 0,9775 so với validation 0,9322 — khoảng cách
  bình thường của một rừng cây.
- **Toàn bộ mức tụt xảy ra đúng ranh giới train → test:** Accuracy −11,4 điểm, PR-AUC −0,0416,
  tức **28 lần** độ lệch chuẩn giữa các fold CV.

---

## PHẦN 2 — NGUYÊN NHÂN, ĐO BẰNG THIẾT KẾ 2×2×2

Ba yếu tố bị nghi ngờ, tách bạch bằng thiết kế giai thừa đầy đủ. Cùng thuật toán, cùng tham số,
cùng seed ở cả 8 ô. Để so sánh công bằng, cả hai cách chia dùng **cùng một tập dòng**: gộp
train+test rồi khử trùng lặp toàn cục, sau đó mới gán train/test theo nguồn gốc hoặc ngẫu nhiên.

### Accuracy @0,5

| | chia chính thức | chia ngẫu nhiên |
|---|---|---|
| có khử trùng lặp, 31 feature | **0,8145** | 0,9102 |
| có khử trùng lặp, 42 feature | 0,8259 | 0,9211 |
| không khử trùng lặp, 31 feature | 0,8633 | 0,9400 |
| không khử trùng lặp, 42 feature | 0,8711 | **0,9505** |

### PR-AUC

| | chia chính thức | chia ngẫu nhiên |
|---|---|---|
| có khử trùng lặp, 31 feature | 0,9259 | 0,9693 |
| có khử trùng lặp, 42 feature | 0,9466 | 0,9778 |
| không khử trùng lặp, 31 feature | 0,9840 | 0,9941 |
| không khử trùng lặp, 42 feature | 0,9859 | **0,9958** |

### FPR

| | chia chính thức | chia ngẫu nhiên |
|---|---|---|
| có khử trùng lặp, 31 feature | 0,2476 | 0,0717 |
| có khử trùng lặp, 42 feature | 0,2562 | 0,0663 |

Chú ý cột FPR: với bộ chia chính thức, FPR nằm ở mức 0,25 bất kể feature hay khử trùng lặp.
Với chia ngẫu nhiên, nó tụt xuống 0,06–0,07. Đây là dấu vân tay của lệch phân bố, không phải của
một mô hình yếu.

### Phân rã mức chênh do cách chia

Trong +0,0955 của yếu tố "cách chia", **khoảng một nửa là dịch chuyển tỷ lệ lớp**:

| | Accuracy | FPR | Precision | Recall |
|---|---|---|---|---|
| Baseline @0,5 | 0,8186 | 0,2569 | 0,6813 | 0,9491 |
| **Chỉ sửa tỷ lệ lớp**, vẫn @0,5 | **0,8673** | **0,1470** | 0,7784 | 0,8921 |

Không đổi model, không đổi ngưỡng — chỉ hiệu chỉnh xác suất theo tỷ lệ lớp của miền test:
**+4,87 điểm Accuracy**, FPR giảm gần một nửa.

Nửa còn lại là lệch phân bố thật của feature:

- KS trung bình trên 39 feature số: toàn bộ 0,0530 · **riêng lớp Normal 0,1097** · riêng Attack 0,0385.
  Lệch tập trung ở lớp Normal, gấp **2,8 lần** lớp Attack.
- 6 feature lệch nhất (KS riêng Normal): `sttl` 0,2763 · `ct_state_ttl` 0,2559 · `ackdat` 0,2383 ·
  `dload` 0,2348 · `dttl` 0,2055 · `tcprtt` 0,2023.
- Cơ cấu `attack_cat`: tỷ trọng Normal đổi từ 0,3194 (train) lên 0,4494 (test), **+0,13** —
  đúng bằng khoảng lệch tỷ lệ lớp. Các loại tấn công giữ gần như nguyên tỷ lệ tương đối với nhau.

Nghĩa là: bộ chia chính thức lấy mẫu Normal và Attack theo tỷ lệ khác nhau, **và** các dòng Normal
ở tập test có phân bố feature khác hẳn (trung vị `ackdat` 0,0000 → 0,0001; `dload` 1.447 → 2.113;
`sjit` 0,00 → 17,62).

### Cơ chế của bước khử trùng lặp (phát hiện mới)

| Tập | % dòng Normal bị xoá | % dòng Attack bị xoá | Chênh |
|---|---|---|---|
| training | 10,5% (5.862/56.000) | **58,6%** (69.913/119.341) | 5,6 lần |
| testing | 13,1% (4.846/37.000) | **58,8%** (26.677/45.332) | 4,5 lần |

Luồng tấn công (nhất là Generic) lặp lại gần như y hệt nhau nên bị gộp rất nhiều. Đây là lý do
tỷ lệ Attack tụt từ 0,6806 → 0,4964 (train) và 0,5506 → 0,3665 (test).

**Xác nhận lại một điểm phải sửa trong báo cáo cũ và slide:** bước làm sạch **không** tạo ra lệch
tỷ lệ lớp. Lệch 0,1300 có sẵn trong dữ liệu thô; sau làm sạch là 0,1299. Mức giảm của train
(0,1842) và của test (0,1841) chênh nhau 0,0001.

---

## PHẦN 3 — THUẬT TOÁN CÓ PHẢI ĐÒN BẨY KHÔNG? KHÔNG

Năm họ thuật toán, cùng 31 feature, cùng cách chia, cùng seed, mỗi họ một cấu hình hợp lý.

| Thuật toán | PR-AUC validation | PR-AUC test-final | Acc @0,5 | Acc @ngưỡng chọn | F1 |
|---|---|---|---|---|---|
| Random Forest | 0,9849 | 0,9414 | 0,8186 | 0,8925 | 0,8448 |
| HistGradientBoosting | 0,9833 | **0,9423** | 0,8215 | 0,8930 | 0,8433 |
| Soft Voting (RF+ET+HGB) | 0,9847 | 0,9419 | 0,8038 | **0,8950** | **0,8462** |
| Extra Trees | 0,9812 | 0,9285 | 0,7694 | 0,8798 | 0,8250 |
| Logistic Regression | 0,9238 | 0,7281 | 0,7270 | 0,7298 | 0,6091 |

- Bốn họ thuật toán cây nằm trong khoảng **0,0138** PR-AUC trên test-final, trong khi khoảng tụt từ
  validation sang test-final là **0,0752** — lớn gấp **5 lần**. Đổi thuật toán không phải đòn bẩy.
- HistGradientBoosting (tương đương LightGBM) hơn Random Forest đúng **+0,0009** PR-AUC. Không đáng kể.
- Tổ hợp Soft Voting cho Accuracy cao nhất ở điểm vận hành (0,8950) nhưng PR-AUC vẫn nằm trong
  cùng khoảng — nó không vượt được trần, chỉ xếp hạng mượt hơn một chút.
- **Hồi quy Logistic sụp hẳn** (0,9238 → 0,7281). Giả thuyết "mô hình đơn giản chịu lệch phân bố
  tốt hơn" **không đúng** ở bài toán này.

XGBoost/LightGBM/CatBoost không có trong môi trường. HistGradientBoosting của scikit-learn là cùng
họ thuật toán (boosting trên histogram) và đã cho kết quả ngang Random Forest, nên khả năng một thư
viện boosting khác tạo đột phá là thấp — nhưng đây là suy luận, không phải phép đo.

---

## PHẦN 4 — CÁC HƯỚNG KHẮC PHỤC

Mọi cấu hình: fit trên `train-fit`, chọn ngưỡng trên `validation` hoặc `test-dev`,
chỉ báo cáo trên `test-final`.

| # | Cấu hình | Ngưỡng | Accuracy | F1 | FPR | PR-AUC | Cần nhãn test? |
|---|---|---|---|---|---|---|---|
| 0 | RF 31f @0,5 (baseline) | 0,500 | 0,8186 | 0,7932 | 0,2569 | 0,9414 | — |
| 1 | + ngưỡng chọn trên validation | 0,535 | 0,8335 | 0,8046 | 0,2254 | 0,9414 | **Không** |
| 2 | + sửa prior bằng EM | 0,500 | 0,8310 | 0,8026 | 0,2309 | 0,9414 | **Không** |
| 3 | + sửa prior + ngưỡng trên test-dev | 0,794 | 0,8925 | 0,8447 | 0,0528 | 0,9414 | Có |
| 4 | + căn chỉnh phân bố (phân vị) | 0,500 | 0,7314 | 0,6984 | 0,3363 | **0,7736** | Không |
| 5 | + căn chỉnh + sửa prior | 0,775 | 0,7617 | 0,6600 | 0,1628 | 0,7736 | Có |
| 6 | RF 24f (bỏ nhóm feature lệch nhất) | 0,500 | 0,8200 | 0,7948 | 0,2557 | 0,9393 | Không |
| 7 | RF 24f + sửa prior | 0,780 | 0,8903 | 0,8432 | 0,0600 | 0,9393 | Có |
| 8 | HGB 31f @0,5 | 0,500 | 0,8215 | 0,7959 | 0,2527 | 0,9423 | Không |
| 9 | HGB 31f + sửa prior | 0,841 | 0,8930 | 0,8433 | 0,0451 | 0,9423 | Có |
| 10 | RF 42f (giữ feature ô nhiễm) @0,5 | 0,500 | 0,8353 | 0,8124 | 0,2442 | 0,9530 | Không |
| 11 | RF 42f + sửa prior | 0,817 | 0,9048 | 0,8667 | 0,0603 | 0,9530 | Có |
| **12** | **HGB 42f + sửa prior** | 0,859 | **0,9050** | 0,8660 | 0,0561 | **0,9544** | Có |

### Hai hướng KHÔNG hiệu quả — báo cáo đầy đủ

- **Căn chỉnh phân bố bằng phân vị (#4, #5): THẤT BẠI NẶNG.** PR-AUC tụt 0,9414 → 0,7736.
  Lý do: phân vị của một dòng phụ thuộc vào thành phần của chính tập chứa nó; khi hai tập có tỷ lệ
  lớp khác nhau, phép căn chỉnh này phá luôn thông tin phân biệt. Đây là một ý tưởng hợp lý trên
  giấy nhưng sai trong trường hợp này.
- **Bỏ nhóm feature lệch nhất (#6, #7): KHÔNG ĐỔI.** 0,8186 → 0,8200. Những feature đó vừa lệch nhất
  vừa hữu ích nhất; bỏ đi không được lợi gì.

### Giới hạn trung thực của hướng "sửa prior"

Thuật toán EM (Saerens–Latinne–Decaestecker 2002) ước lượng tỷ lệ Attack của miền test từ dữ liệu
**không nhãn**. Kết quả:

| Cấu hình | π train | π test ước lượng EM | π test thật |
|---|---|---|---|
| RF 31f | 0,4964 | **0,4684** | **0,3665** |
| HGB 31f | 0,4964 | 0,4709 | 0,3665 |
| RF 42f | 0,4964 | 0,4778 | 0,3665 |

**EM sửa thiếu rất nhiều.** Nó giả định *chỉ* có dịch chuyển tỷ lệ lớp (P(x|y) không đổi); ở đây
còn có lệch phân bố feature nên giả định bị vi phạm. Hệ quả:

- Phương án **hoàn toàn không dùng nhãn test**: chỉ lấy lại được **+1,2 đến +1,5 điểm** Accuracy.
- Muốn lấy đủ **+7 điểm** thì phải có một mẫu **có nhãn** từ phân bố triển khai (ở đây là `test-dev`)
  để đặt ngưỡng — đúng điều notebook 04 đã làm ở lần chạy 3.

Đây là phát hiện quan trọng và đi ngược kỳ vọng ban đầu: độ lệch **không** phải prior shift thuần tuý.

### Kiểm định thống kê — cấu hình 12 so với baseline

Bootstrap theo cặp 1.000 lần trên test-final:

| | Trung bình | CI 95% | p |
|---|---|---|---|
| Δ Accuracy | **+0,0863** | [+0,0812 ; +0,0914] | ≈ 0 |
| Δ PR-AUC | **+0,0130** | [+0,0109 ; +0,0150] | ≈ 0 |

**Phải đọc đúng:** ΔAccuracy +0,086 nhưng ΔPR-AUC chỉ +0,013. Nghĩa là khoảng **85% mức cải thiện
đến từ đặt lại điểm vận hành**, chỉ ~15% đến từ model thật sự xếp hạng tốt hơn — và phần 15% đó đến
từ 11 feature được giữ lại, không phải từ việc đổi thuật toán.

### Ma trận nhầm lẫn (test-final, 25.284 dòng)

| | TN | FP | FN | TP |
|---|---|---|---|---|
| Baseline RF 31f @0,5 | 11.903 | 4.114 | 472 | 8.795 |
| Cấu hình 12 (HGB 42f + sửa prior) | 15.119 | 898 | 1.505 | 7.762 |

Báo động giả giảm từ 4.114 xuống 898 (−78%), đổi lại bỏ sót tăng từ 472 lên 1.505.
Hình: `reports/audit06/confusion_truoc_sau.png`.

### Recall theo loại tấn công tại cấu hình 12

Worms 1,000 · Reconnaissance 0,986 · Generic 0,976 · Backdoor 0,970 · DoS 0,969 ·
Exploits 0,962 · Shellcode 0,924 · Analysis 0,911 · **Fuzzers 0,430**

Fuzzers vẫn là điểm yếu duy nhất và không có cấu hình nào trong đợt này xử lý được.

---

## PHẦN 5 — VÌ SAO CÁC BÀI BÁO ĐẠT 97–98%?

Đọc thẳng từ bảng PR-AUC ở Phần 2: chỉ cần **không khử trùng lặp** là PR-AUC lên 0,984–0,996 và
Accuracy lên 0,863–0,951 — trong khi 10–48% dòng test khi đó là **bản sao chính xác** của dòng train.
Thêm chia ngẫu nhiên thay vì dùng bộ chia chính thức thì lên 0,9505 Accuracy / 0,9958 PR-AUC.

Khoảng cách giữa nhóm và các con số công bố chủ yếu là khoảng cách **giao thức đánh giá**, không
phải khoảng cách năng lực mô hình. Nhóm đang chạy giao thức khắt khe hơn và trả giá bằng con số thấp hơn.

---

## PHẦN 6 — KHUYẾN NGHỊ

1. **Giữ bộ chia chính thức và giữ bước khử trùng lặp.** Cả hai đều đúng về mặt phương pháp.
   Nhưng khi báo cáo con số, phải nói rõ đây là benchmark có lệch phân bố, kèm bảng 2×2×2 ở Phần 2
   làm bằng chứng — nó biến "số thấp" từ một điểm yếu thành một kết quả có giải thích.
2. **Sửa lỗi vận hành ngưỡng 0,5.** Đây là thứ rẻ nhất và có thật. Tối thiểu: chọn ngưỡng trên
   validation (+1,5 điểm, không cần nhãn test). Nếu chấp nhận dùng `test-dev` có nhãn như một mẫu
   từ phân bố triển khai: +7,4 điểm và FPR 0,2569 → 0,0528.
3. **Không đổi thuật toán để tìm đột phá.** Bằng chứng ở Phần 3: biên độ giữa các họ thuật toán cây
   nhỏ hơn khoảng tụt do lệch phân bố 5 lần.
4. **Về 11 feature đã bỏ:** chúng đáng +0,0112 Accuracy theo thang đo 2×2×2 (trung bình hai cách
   chia), và +0,0167 Accuracy / +0,0116 PR-AUC khi so trực tiếp cấu hình #0 với #10. Nếu nhóm muốn giữ lập
   luận theo D'hooge et al. thì tiếp tục bỏ và chấp nhận mức giá đó — mức giá này nhỏ, và nay đã
   đo được chứ không còn là ước đoán. Lưu ý thêm: `sttl` và `ct_state_ttl` cũng chính là hai feature
   **lệch phân bố nhất** (KS riêng Normal 0,2763 và 0,2559), nên giữ chúng lại cũng đi kèm rủi ro.
5. **Báo cáo Balanced Accuracy và PR-AUC song song với Accuracy.** Trên tập mất cân bằng và lệch
   phân bố, Accuracy một mình gây hiểu nhầm — chính nó là lý do câu hỏi "vì sao accuracy thấp"
   xuất hiện.
6. **Sửa 2 chỗ trong tài liệu cũ** (đã xác nhận lại bằng số ở Phần 2): câu "bước làm sạch tự nó tạo
   ra lệch tỷ lệ lớp 13 điểm" trong `reports/Bao_cao_so_sanh_3_lan_chay.txt` mục 3.2 và
   `reports/Noi_dung_slide_thuyet_trinh.md` slide 2.

---

## PHẦN 7 — ĐIỀU KHÔNG ĐƯỢC KẾT LUẬN TỪ ĐỢT NÀY

- **Không** kết luận được rằng bộ chia chính thức là "sai". Nó là một benchmark khó có lệch phân bố;
  dùng nó là lựa chọn khắt khe và nên giữ.
- **Không** kết luận được rằng không thuật toán nào vượt được trần. Chỉ thử 5 họ, mỗi họ một cấu
  hình hợp lý, không dò siêu tham số diện rộng, và không có XGBoost/LightGBM/CatBoost trong môi trường.
- **Không** kết luận được rằng mọi phương pháp thích ứng miền đều vô dụng. Chỉ thử hai cách
  (căn chỉnh phân vị, sửa prior bằng EM). Các hướng chưa thử: CORAL, học đối kháng theo miền,
  self-training trên dữ liệu test không nhãn.
- **Không** kết luận được rằng cấu hình 12 là cấu hình nên triển khai. Nó dùng 11 feature mà nhóm đã
  cố ý loại theo lập luận phương pháp, và ngưỡng của nó chọn trên `test-dev` có nhãn.
- Con số của notebook này dùng 300 cây và seed 42; chưa kiểm tra độ bền theo nhiều seed như
  `reports/Bao_cao_cai_thien_model.txt` đã làm cho thực nghiệm đa lớp.

---

## NGUỒN SỐ LIỆU

| File | Nội dung |
|---|---|
| `notebooks/06_Root_Cause_Audit.ipynb` | Toàn bộ code, chạy tuần tự, kèm output |
| `reports/audit06/thang_do_2x2x2.csv` | 8 ô của thiết kế giai thừa |
| `reports/audit06/cac_huong_khac_phuc.csv` | 13 cấu hình khắc phục |
| `reports/audit06/so_sanh_thuat_toan.csv` | 5 thuật toán |
| `reports/audit06/ket_qua_audit06.json` | Mọi số đo của notebook |
| `reports/audit06/confusion_truoc_sau.png` | Ma trận nhầm lẫn trước/sau |

`data/`, `models/` và `notebooks/01..05` **không bị thay đổi**.
