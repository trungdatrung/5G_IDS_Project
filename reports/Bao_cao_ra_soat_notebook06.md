# Rà soát notebook 06 — đầu việc, phát hiện, kỹ thuật, kết quả, và so sánh với các phiên bản trước

**Dự án:** 5G IDS / UNSW-NB15 · phân loại nhị phân `label` (0 = Normal, 1 = Attack)
**Đối tượng rà soát:** `notebooks/06_Root_Cause_Audit.ipynb` (34 cell, chạy 03/10/2026) và
`reports/Bao_cao_truy_nguyen_accuracy.md`
**Ngày rà soát:** 08/10/2026
**Cách rà soát:** đọc lại toàn bộ code + output đã lưu của notebook 06; tính lại mọi con số
từ `reports/audit06/ket_qua_audit06.json`; đối chiếu với `models/*_metrics.json`,
`notebooks/model_comparison_results.csv`, `reports/exp05/*.json` và
`reports/dedup_vs_nodedup/Bao_cao_dedup_vs_nodedup.md`.
**Không chạy lại model.** Mọi số dưới đây là số đã lưu, hoặc là phép tính lại từ số đã lưu
(có ghi rõ công thức ở từng chỗ).

---

## 0. TÓM TẮT CHO NGƯỜI ĐỌC NHANH

**Phần kiểm chứng của notebook 06 là chắc.** Bước làm sạch tái lập trùng khít `data/cleaned`;
baseline 0,8186 khớp chính xác tới 7 chữ số với `models/random_forest_v3_metrics.json`;
one-hot không rò rỉ; chia tập đúng kích thước. Kết luận "accuracy thấp không phải do lỗi cài đặt"
**đứng vững**.

**Phần "đo nguyên nhân" thì có lỗi phương pháp thật, và lỗi đó đổi kết luận.** Thang đo 2×2×2
so sánh accuracy giữa 8 ô có **tập đánh giá khác nhau** (47.214 / 52.640 / 82.332 dòng) và
**tỷ lệ lớp khác nhau** (π_test từ 0,3338 đến 0,6391). Accuracy phụ thuộc tỷ lệ lớp, nên ba
con số trong bảng kết luận không so được với nhau. Tính lại bằng chỉ số không phụ thuộc tỷ lệ lớp:

| Yếu tố | NB06 báo cáo (accuracy) | Tính lại (balanced acc) | Tính lại (ROC-AUC) |
|---|---|---|---|
| Cách chia official → random | **+0,0955** | +0,0616 | +0,0194 |
| Giữ lại 11 feature đã bỏ | +0,0112 | +0,0125 | +0,0075 |
| Bỏ bước khử trùng lặp | +0,0294 | +0,0161 | +0,0156 |
| **Tỷ lệ "chia / feature"** | **8,53 lần** | 4,94 lần | **2,58 lần** |

Kết luận "cách chia lớn hơn việc bỏ feature 8,5 lần" là con số **lớn nhất trong ba cách đo**.
Đo trung thực hơn thì là **2,6–4,9 lần**. Hướng của kết luận vẫn đúng, độ lớn thì bị phóng đại.

**Phần "khắc phục" có một lỗi nặng hơn:** cấu hình tốt nhất được chọn bằng
`FIX.accuracy.idxmax()` — tức **chọn model trên chính `test-final`**, đúng điều mà cell đầu
notebook tự cấm. Sau đó bootstrap CI lại tính cho cấu hình vừa được chọn trên tập đó, nên
CI95 [+0,0812; +0,0914] là **lạc quan có hệ thống** (winner's curse). Khoảng cách giữa #12 và #11
chỉ là **0,0002** accuracy — và nếu xếp theo balanced accuracy thì #11 thắng, không phải #12.

**So với các phiên bản trước:** con số 0,9050 của notebook 06 **không phải năng lực mới**.
Notebook 05 đã đo cấu hình tương đương (ablation 39 feature ô nhiễm, ngưỡng theo FPR ≤ 10%)
và được **0,8951** accuracy / **0,9527** PR-AUC. Notebook 06 hơn 0,0098 accuracy, nhưng trả giá
bằng **Recall Fuzzers 0,625 → 0,430** và bỏ mất ràng buộc FPR mà notebook 04/05 đã cố ý đặt ra.

---

## 1. NOTEBOOK 06 ĐÃ LÀM NHỮNG ĐẦU VIỆC GÌ

34 cell, chia 5 phần. Bảng dưới liệt kê từng đầu việc, kỹ thuật dùng, và output để lại.

### Phần 1 — Rà soát bước làm sạch (cell 2–9)

| # | Đầu việc | Kỹ thuật | Output |
|---|---|---|---|
| 1.1 | Đọc 2 file chia chính thức | `read_csv` + `assert` kích thước/NaN | train 175.341×45, test 82.332×45, 0 NaN |
| 1.2 | Kiểm tra `df_shrink` có làm mất thông tin | So sai số tuyệt đối/tương đối từng cột; đếm dòng trùng trước–sau | sai số lớn nhất ở `sjit` = 0,062 (tương đối 4,2×10⁻⁸); dòng trùng 75.775 **không đổi** |
| 1.3 | Bỏ 11 cột (8 ô nhiễm + 3 vô dụng) | Danh sách `CONTAM` + `USELESS` theo D'hooge 2022 | còn 31 feature + 2 cột nhãn; `ct_srv_ltm` **không tồn tại** trong dữ liệu |
| 1.4 | Bỏ dòng trùng, tách theo lớp | `drop_duplicates()` + `groupby('label').size()` trước/sau | **phát hiện mới**: xoá 58,6% dòng Attack nhưng chỉ 10,5% dòng Normal (train) |
| 1.5 | Bỏ dòng mâu thuẫn | `groupby(feats).label.nunique() > 1` | 632 (train) / 242 (test) |
| 1.6 | Đối chiếu với `data/cleaned` | So **từng giá trị** sau `astype(str)` | **trùng khít** 98.934×33 và 50.567×33 |

### Phần 2 — Rà soát tiền xử lý & mô hình (cell 10–15)

| # | Đầu việc | Kỹ thuật | Output |
|---|---|---|---|
| 2.1 | Tái lập cách chia của NB03/04 | `train_test_split` stratify + `assert` | 79.147 / 19.787 / 25.283 / 25.284 |
| 2.2 | Kiểm tra One-Hot có rò rỉ không | Đếm cột; tìm giá trị chỉ có ở test; đếm dòng test bị mã hoá toàn 0 | 183 cột; `state` = `ACC`,`CLO` chỉ có ở test → vector 0; encoder fit **chỉ** trên train-fit |
| 2.3 | Tái lập baseline | RF 300 cây, tham số NB03 | test-final accuracy **0,8186** |
| 2.4 | Underfit hay overfit? | Thang 5 bậc: train-fit → CV 5-fold → validation → test-dev → test-final | train-fit 0,9985 · CV 0,9830±0,0015 · val 0,9849 · test 0,9414 (PR-AUC) |

### Phần 3 — Đo nguyên nhân (cell 16–21)

| # | Đầu việc | Kỹ thuật | Output |
|---|---|---|---|
| 3.1 | Thiết kế giai thừa 2×2×2 | Gộp train+test → khử trùng lặp **toàn cục** → gán nhãn train/test theo nguồn gốc hoặc ngẫu nhiên; 8 ô cùng thuật toán/tham số/seed | `thang_do_2x2x2.csv` |
| — | Đo rò rỉ test→train | Hash từng dòng (`pd.util.hash_pandas_object`) rồi `np.isin` | 0% khi có khử trùng lặp; 10,0–47,5% khi không |
| 3.2 | Tách độ lớn ba yếu tố | Hiệu accuracy giữa các ô | +0,0955 / +0,0112 / +0,0294 |
| 3.3 | Pháp y lệch phân bố | Kolmogorov–Smirnov 2 mẫu, tính riêng cho từng lớp; cơ cấu `attack_cat` | KS trung bình: tất cả 0,0530 · riêng Normal 0,1097 · riêng Attack 0,0385 |
| 3.4 | Lệch tỷ lệ lớp chiếm bao nhiêu | Hiệu chỉnh prior bằng tỷ lệ lớp **thật** của test (chặn trên) | accuracy 0,8186 → **0,8673**; FPR 0,2569 → 0,1470 |

### Phần 4 — Thử các hướng khắc phục (cell 22–32)

| # | Đầu việc | Kỹ thuật | Output |
|---|---|---|---|
| 4.1 | Dựng công cụ | EM prior (Saerens–Latinne–Decaestecker 2002); `shift_prior`; `QuantileTransformer`; nhánh 42 feature **giữ đúng tập dòng** của nhánh 31 feature | — |
| 4.2 | Chạy 13 cấu hình | 4 chiều: thuật toán × bộ feature × sửa prior × quy tắc ngưỡng | `cac_huong_khac_phuc.csv` |
| 4.3 | EM có ước lượng đúng không | So π ước lượng với π thật | EM cho **0,4684**, thật là **0,3665** → sửa thiếu |
| 4B | So 5 họ thuật toán | RF, Extra Trees, HistGradientBoosting, Logistic Regression, Soft Voting | `so_sanh_thuat_toan.csv` |
| 4.4 | Kiểm định thống kê | Paired bootstrap 1.000 lần | ΔAcc +0,0863 CI95 [+0,0812; +0,0914]; ΔPR-AUC +0,0130 |
| 4.5–4.7 | Ma trận nhầm lẫn, recall theo loại tấn công, ghi file | — | `confusion_truoc_sau.png`, `ket_qua_audit06.json` |

### Phần 5 — Kết luận (cell 33)

Tám tiểu mục, trong đó có hai mục đáng khen về mặt liêm chính học thuật: **5.4 báo cáo hai hướng
thất bại** và **5.8 liệt kê những điều KHÔNG được kết luận**.

---

## 2. KIỂM CHỨNG LẠI: NHỮNG GÌ NOTEBOOK 06 LÀM ĐÚNG

Tôi đối chiếu từng con số then chốt với file đã lưu từ các lần chạy trước. Tất cả khớp:

| Con số của NB06 | Giá trị | Nguồn độc lập đối chiếu | Giá trị | Khớp? |
|---|---|---|---|---|
| Baseline accuracy test-final | 0,818620 | `random_forest_v3_metrics.json` → `A: RF @0.5` | 0,8186204714 | ✅ trùng 7 chữ số |
| Baseline validation accuracy | 0,932228 | `random_forest_v2_metrics.json` → `Tuned - validation` | 0,932228 | ✅ |
| PR-AUC train-fit | 0,998464 | `random_forest_v2_metrics.json` → `Tuned - train-fit` | 0,998464 | ✅ |
| TN/FP/FN/TP baseline | 11.903 / 4.114 / 472 / 8.795 | `exp05/step7_final.json` → `RF-A binary @0.50` | 11.903 / 4.114 / 472 / 8.795 | ✅ |
| CV PR-AUC | 0,982977 | `exp05/step5_shift.json` → `cv_pr_auc_trainfit.mean` | 0,982977 | ✅ |
| Độ lệch chuẩn CV | 0,0014806 | `exp05/step5_shift.json` → `std` | 0,0014806 | ✅ |
| Kích thước 4 tập | 79.147/19.787/25.283/25.284 | `exp05/step0_baseline.json` → `sizes` | giống | ✅ |
| Tỷ lệ Attack 4 tập | 0,4964/0,4964/0,3665/0,3665 | `exp05/step5_shift.json` → `prevalence` | giống | ✅ |

**Đánh giá:** khâu tái lập của notebook 06 là nghiêm túc và không có lỗi. Mọi `assert` trong
notebook đều là assert thật (có giá trị cụ thể, fail được), không phải assert trang trí.
Đây là điểm mạnh nhất của notebook.

---

## 3. CÁC PHÁT HIỆN CỦA NOTEBOOK 06 — PHÁT HIỆN NÀO ĐỨNG VỮNG

| Phát hiện | Đứng vững? | Ghi chú sau rà soát |
|---|---|---|
| **P1.** Bước làm sạch tái lập trùng khít, không có lỗi cài đặt | ✅ **Vững** | So từng giá trị, có assert chặn |
| **P2.** `df_shrink` hạ float64→float32, sai số 0,062 nhưng không đổi kết quả bỏ trùng | ✅ **Vững** | Kiểm chứng đúng cách: đếm dòng trùng trước/sau |
| **P3.** Bỏ trùng xoá ~59% dòng Attack nhưng chỉ 10–13% dòng Normal | ✅ **Vững, và là phát hiện mới có giá trị** | Giải thích được cơ chế tỷ lệ Attack tụt 0,68→0,50 |
| **P4.** Lệch tỷ lệ lớp 0,13 điểm **có sẵn trong dữ liệu thô**, không do làm sạch tạo ra | ✅ **Vững** | train giảm 0,1842, test giảm 0,1841 — chênh 0,0001. Đây là chỗ **sửa được một câu sai** trong `Bao_cao_so_sanh_3_lan_chay.txt` §3.2 và `Noi_dung_slide_thuyet_trinh.md` slide 2 |
| **P5.** Không underfit, không học thuộc quá mức; toàn bộ mức tụt xảy ra ở ranh giới train→test | ✅ **Vững** | Thang 5 bậc là cách trình bày tốt |
| **P6.** One-Hot không rò rỉ, xử lý được giá trị lạ | ✅ **Vững** | Đếm dòng bị mã hoá toàn 0 = 0 |
| **P7.** Lệch phân bố tập trung ở lớp Normal (KS 0,1097 vs 0,0385) | ✅ **Vững — và mạnh hơn NB06 nói** | Tính lại chỉ trên 28 feature model thật dùng: Normal 0,1156 vs Attack 0,0341 = **3,39 lần** (NB06 nói 2,85 lần) |
| **P8.** EM ước lượng thiếu (0,4684 vs 0,3665 thật) → lệch không phải prior shift thuần | ✅ **Vững, phát hiện quan trọng** | Đây là kết quả âm được báo cáo trung thực, đáng giá |
| **P9.** Căn chỉnh phân vị thất bại nặng (PR-AUC 0,9414 → 0,7736) | ✅ **Vững** | Lời giải thích (phân vị phụ thuộc thành phần của chính tập) là đúng |
| **P10.** Đổi thuật toán không phải đòn bẩy | ⚠️ **Đúng kết luận, sai cách chứng minh** | Xem lỗi L5 bên dưới |
| **P11.** "Cách chia lớn hơn bỏ feature 8,5 lần" | ⚠️ **Phóng đại** | Thực tế 2,6–4,9 lần. Xem lỗi L1 |
| **P12.** "Bỏ khử trùng lặp làm số đẹp lên +0,0294" | ❌ **Mâu thuẫn với thực nghiệm đã có** | Xem lỗi L2 |
| **P13.** "~85% cải thiện từ điểm vận hành, ~15% từ model" | ❌ **Không phải phép tính hợp lệ** | Xem lỗi L4 |

---

## 4. CÁC LỖI PHƯƠNG PHÁP TÌM ĐƯỢC — VÀ SỐ ĐÚNG

Đây là phần trả lời trực tiếp cho nhận xét "không khoa học".

### L1 — Thang đo 2×2×2 so sánh accuracy trên **các tập đánh giá khác nhau** (lỗi nặng)

Cột `n_test` và `pi_test` của 8 ô, đọc trực tiếp từ `ket_qua_audit06.json`:

| bỏ trùng | feature | chia | n_train | n_test | π_train | π_test | rò rỉ | accuracy | balanced acc | ROC-AUC |
|---|---|---|---|---|---|---|---|---|---|---|
| có | 31 | official | 93.462 | **47.214** | 0,4671 | **0,3338** | 0,000 | 0,8145 | 0,8454 | 0,9547 |
| có | 31 | random | 93.462 | **47.214** | 0,4224 | **0,4224** | 0,000 | 0,9102 | 0,9068 | 0,9771 |
| có | 42 | official | 100.630 | **52.640** | 0,4868 | **0,3605** | 0,000 | 0,8259 | 0,8577 | 0,9652 |
| có | 42 | random | 100.630 | **52.640** | 0,4434 | **0,4434** | 0,000 | 0,9211 | 0,9195 | 0,9816 |
| không | 31 | official | 175.341 | **82.332** | 0,6806 | **0,5506** | 0,286 | 0,8633 | 0,8507 | 0,9782 |
| không | 31 | random | 175.341 | **82.332** | 0,6391 | **0,6391** | 0,475 | 0,9400 | 0,9371 | 0,9892 |
| không | 42 | official | 175.341 | **82.332** | 0,6806 | **0,5506** | 0,100 | 0,8711 | 0,8580 | 0,9814 |
| không | 42 | random | 175.341 | **82.332** | 0,6391 | **0,6391** | 0,443 | 0,9505 | 0,9481 | 0,9923 |

Notebook tự khẳng định (cell 16): *"Cùng thuật toán, cùng tham số, cùng seed ở cả 8 ô — chỉ ba
yếu tố dưới đây thay đổi."* Thực tế **cả ba yếu tố đều làm đổi tập đánh giá**:

- Đổi `feature` 31→42 thì phép khử trùng lặp chạy trên 42 cột thay vì 31 cột, nên **tập dòng
  cũng đổi** (47.214 → 52.640 dòng test, π_test 0,3338 → 0,3605).
- Đổi `bỏ trùng` có→không thì tập test nhảy lên 82.332 dòng với π_test 0,5506–0,6391.
- Đổi `cách chia` official→random thì tập test là tập dòng khác, và π_test bị **ép bằng** π_train
  do stratify.

Accuracy là chỉ số **phụ thuộc tỷ lệ lớp**. PR-AUC cũng vậy (đường cơ sở của PR-AUC chính là π).
Với một model recall cao như ở đây (0,94–0,99), tập test nhiều Attack hơn sẽ tự động cho accuracy
cao hơn, **không cần model tốt hơn chút nào**. Vậy nên không thể so ô này với ô kia bằng accuracy.

**Số đúng.** Tính lại ba yếu tố bằng balanced accuracy (không phụ thuộc tỷ lệ lớp) và ROC-AUC
(cũng không phụ thuộc tỷ lệ lớp), dùng đúng cùng công thức hiệu ô mà cell 18 dùng:

| Yếu tố | accuracy (NB06) | balanced acc | ROC-AUC |
|---|---|---|---|
| Cách chia official → random | +0,0955 | **+0,0616** | **+0,0194** |
| Giữ lại 11 feature | +0,0112 | +0,0125 | +0,0075 |
| Bỏ khử trùng lặp (TB 4 cặp ô) | +0,0383 | +0,0161 | +0,0156 |
| Tỷ lệ chia / feature | 8,53× | **4,94×** | **2,58×** |

→ Câu kết luận nên viết lại thành: *"Cách chia train/test là yếu tố lớn nhất trong ba yếu tố,
lớn hơn việc bỏ 11 feature khoảng 2,6–4,9 lần tuỳ chỉ số."* Hướng không đổi; con số "8,5 lần"
thì phải bỏ.

### L2 — Yếu tố "bỏ khử trùng lặp" bị báo cáo bằng **một ô duy nhất**, và mâu thuẫn với thực nghiệm đã có

Cell 18 tính `eff_split` và `eff_feat` bằng cách lấy trung bình 2 ô, nhưng `eff_dedup` thì lấy
**đúng 1 ô** (42 feature, chia ngẫu nhiên). Bốn cặp ô cho bốn giá trị rất khác nhau:

| Cặp ô | Δ accuracy | Δ balanced acc |
|---|---|---|
| 31 feature, chia official | +0,0489 | **+0,0054** |
| 42 feature, chia official | +0,0451 | **+0,0003** |
| 31 feature, chia random | +0,0298 | +0,0303 |
| 42 feature, chia random | **+0,0294** ← ô NB06 chọn | +0,0286 |
| Trung bình 4 ô | +0,0383 | +0,0161 |

NB06 báo cáo đúng giá trị **nhỏ nhất** trong bốn giá trị accuracy, nhưng lại trình bày nó
ngang hàng với hai yếu tố kia (vốn là trung bình). Cơ sở tính không thống nhất.

**Quan trọng hơn:** dòng 1–2 của bảng trên cho thấy với **bộ chia chính thức** — tức đúng giao
thức dự án đang dùng — việc bỏ khử trùng lặp gần như **không đem lại gì** về balanced accuracy
(+0,0054 và +0,0003). Điều này **khớp hoàn toàn** với thực nghiệm `experiment_nodedup` đã làm từ
02/10/2026, vốn đo cẩn thận hơn (giữ nguyên tập đánh giá test-final 25.284 dòng, chỉ đổi dữ liệu
huấn luyện) và kết luận: **ΔPR-AUC = −0,0027, CI95 [−0,0037; −0,0017], p ≈ 0 — bỏ khử trùng lặp
cho kết quả KÉM HƠN**, và con số đẹp chỉ xuất hiện khi đánh giá "native" trên tập test còn trùng.

Notebook 06 đo lại cùng câu hỏi bằng một thiết kế **kém hơn** (đổi cả tập đánh giá), ra con số
ngược dấu (+0,0294 thay vì −0,0027), **và không đối chiếu với thực nghiệm cũ**. Notebook 06 có
giải thích "+0,0294 là điểm số ảo vì rò rỉ tăng", nên không phải gian dối — nhưng nó đã thay một
phép đo sạch bằng một phép đo bẩn mà không nói, và không ai đọc bảng đó biết rằng câu hỏi này
**đã có câu trả lời chính xác hơn** nằm ở `reports/dedup_vs_nodedup/`.

### L3 — Cấu hình tốt nhất được chọn **trên chính `test-final`** (lỗi nặng nhất)

Cell 0 của notebook tự đặt kỷ luật:

> *"`test-final` chỉ được chạm ở bước báo cáo cuối. Mọi lựa chọn ngưỡng/feature/model đều quyết
> định trên `validation` hoặc `test-dev`."*

Cell 29 làm ngược lại:

```python
best_name = FIX.loc[FIX.accuracy.idxmax(), 'name']   # accuracy nay la accuracy tren test-final
```

13 cấu hình được chấm điểm trên `test-final` rồi lấy cấu hình điểm cao nhất. Sau đó cell 29
tính bootstrap CI cho **đúng cấu hình vừa được chọn bằng tập đó**. Đây là winner's curse kinh điển:
CI95 [+0,0812; +0,0914] và p ≈ 0 là **lạc quan có hệ thống**, không phải một kiểm định hợp lệ.

Mức độ nghiêm trọng: cao, vì khoảng cách giữa các cấu hình đầu bảng nằm trong mức nhiễu.

| Thứ hạng | Cấu hình | accuracy | balanced acc |
|---|---|---|---|
| 1 theo accuracy | **12. HGB 42f + sửa prior** | 0,90496 | 0,8908 |
| 2 theo accuracy | 11. RF 42f + sửa prior | 0,90476 | **0,8920** |
| 3 | 9. HGB 31f + sửa prior | 0,8930 | 0,8704 |
| 4 | 3. RF 31f + prior + ngưỡng test-dev | 0,8925 | 0,8725 |

Chênh #12 − #11 = **+0,00020** accuracy, tức 5 dòng trên 25.284. Và **nếu xếp theo balanced
accuracy thì #11 thắng**, không phải #12. Việc gọi #12 là "cấu hình tốt nhất" là chọn theo nhiễu.

**Cách đúng:** chọn trên `test-dev` (notebook 04 và 05 đã làm đúng điều này), rồi báo cáo một lần
trên `test-final`. Notebook 05 còn làm thêm một bước đúng nữa: khai báo trước ràng buộc
`FPR ≤ 0,10` làm tiêu chí chọn, nên không có chỗ cho việc dò tìm.

### L4 — "85% cải thiện từ điểm vận hành, 15% từ model" không phải phép tính hợp lệ

Câu này được suy ra từ: ΔAccuracy = +0,0863 và ΔPR-AUC = +0,0130. Hai đại lượng **khác đơn vị,
khác thang, khác ý nghĩa** — không chia được cho nhau để ra tỷ lệ phần trăm.

**Phép phân rã đúng** phải dùng cùng một đơn vị. Cả ba số dưới đây đều là accuracy trên
`test-final`, lấy từ chính bảng 13 cấu hình:

| Thành phần | Cấu hình đối chứng | Δ accuracy | Tỷ lệ |
|---|---|---|---|
| Do giữ lại 11 feature | #0 (0,8186) → #10 RF 42f @0,5 (0,8353) | **+0,0167** | 19,3% |
| Do đổi RF → HGB | #0 (0,8186) → #8 HGB 31f @0,5 (0,8215) | **+0,0029** | 3,3% |
| Do sửa prior + đặt lại ngưỡng | phần còn lại | **+0,0668** | **77,3%** |
| **Tổng** | #0 → #12 | **+0,0863** | 100% |

Kết luận định tính của NB06 (*cải thiện chủ yếu đến từ điểm vận hành, không từ model mạnh hơn*)
**vẫn đúng**, và nay có con số hợp lệ đỡ lưng: **77% điểm vận hành, 19% feature, 3% thuật toán**.

### L5 — Kết luận "đổi thuật toán không phải đòn bẩy" dùng số khác với số notebook in ra

Cell 28 in ra:

```
Bien do giua cac thuat toan: trong phan bo train 0.0611 | tren test-final 0.2142
Khoang tut trung binh tu validation sang test-final: 0.0752
CACH DOC: neu khoang tut (do lech phan bo) LON HON NHIEU so voi bien do giua cac thuat toan,
thi doi thuat toan khong phai don bay.
```

Theo đúng quy tắc đọc mà chính cell đó đặt ra: 0,0752 **không** lớn hơn 0,2142, nên kết luận
phải là *"đổi thuật toán CÓ là đòn bẩy"*. Nhưng markdown cell 33 lại viết:

> *"Bốn họ thuật toán cây ... nằm trong khoảng **0,0138** PR-AUC ... trong khi khoảng tụt ...
> là 0,0752 — lớn gấp 5 lần."*

Tức là markdown đã **âm thầm bỏ Logistic Regression** ra khỏi biên độ để đảo chiều kết luận.
0,2142 là biên độ gồm cả Logistic (0,9423 − 0,7281); 0,0138 là biên độ chỉ 4 họ cây
(0,9423 − 0,9285). Tôi xác nhận cả hai con số đều tính đúng — vấn đề là **con số in ra trong
notebook và con số dùng để kết luận là hai con số khác nhau**, không có một dòng nào nói rõ
việc loại Logistic.

Kết luận cuối (*trong các họ cây, đổi thuật toán không đem lại gì đáng kể*) là **đúng** —
chênh HGB so với RF chỉ +0,0009 PR-AUC. Chỉ cần sửa lại cách trình bày cho khớp.

### L6 — KS tính trên dữ liệu **thô** và trên cả những feature model không dùng

Cell 19 tính KS trên `raw['training']` / `raw['testing']` — tức dữ liệu **trước** khi bỏ trùng và
**trước** khi bỏ cột. Model thì học trên dữ liệu đã bỏ trùng (mất 59% dòng Attack) và chỉ dùng
31 feature. Nên bảng KS đang mô tả một phân bố khác với phân bố model thực sự nhìn thấy.

Hệ quả cụ thể: 3 trong 6 feature "lệch nhất" mà kết luận §5.2 nêu tên — `sttl` (0,2763),
`ct_state_ttl` (0,2559), `dttl` (0,2055) — **nằm trong danh sách 11 cột đã bị bỏ**, nên chúng
không thể giải thích mức tụt của model 31 feature.

**Tin tốt:** kết luận "lệch tập trung ở lớp Normal" đứng vững ở mọi cách tính:

| Phạm vi tính | KS TB riêng Normal | KS TB riêng Attack | Tỷ lệ |
|---|---|---|---|
| 39 feature số, dữ liệu **thô** (NB06 dùng) | 0,1097 | 0,0385 | 2,85× |
| 28 feature trong model, dữ liệu **thô** | 0,1156 | 0,0341 | 3,39× |
| 11 feature đã bỏ, dữ liệu **thô** | 0,0946 | 0,0495 | 1,91× |
| **28 feature trong model, dữ liệu ĐÃ LÀM SẠCH** *(đúng cách)* | **0,1300** | **0,0492** | **2,64×** |

Dòng cuối là con số nên dùng, vì đó là phân bố **model thật sự nhìn thấy** — đã bỏ cột và đã bỏ
dòng trùng. Nó được đo trong notebook 07 (xem `reports/Bao_cao_ket_qua_notebook07.md` §2).

Danh sách feature lệch nhất **trong model, trên dữ liệu đã làm sạch** cần nêu thay thế:
`ackdat` 0,2698 · `dload` 0,2391 · `tcprtt` 0,2258 · `synack` 0,2250 · `dmean` 0,2061.
Bốn trong năm là nhóm thời gian bắt tay TCP và lưu lượng chiều về.

(Ghi chú: `reports/exp05/step5_shift.json` của notebook 05 đã tính KS **trên dữ liệu đã làm sạch
và chỉ trên feature trong model** — đúng cách. NB06 làm lại kém hơn ở điểm này.)

### L7 — So sánh "28 lần độ lệch chuẩn CV" là so hai thứ không cùng loại

(0,982977 − 0,941405) / 0,0014806 = 28,08 — phép tính đúng. Nhưng độ lệch chuẩn giữa các fold CV
đo **nhiễu lấy mẫu của ước lượng CV trong cùng một phân bố**, nó không phải thước đo cho một
dịch chuyển phân bố. Chia hai thứ cho nhau ra một số lớn thì nghe mạnh, nhưng không có ý nghĩa
thống kê. Câu "PR-AUC tụt 0,0416 từ CV sang test-final" tự nó đã đủ.

### L8 — Notebook 06 **không chạy lại được** trên bản sao hiện tại

Cell 1 đặt `RAW = BASE/'data'/'raw'/'CSV Files'/'Training and Testing Sets'`, cell 3 đọc
`UNSW_NB15_training-set.csv` và `UNSW_NB15_testing-set.csv` từ đó. Thư mục đó **không tồn tại**
trong bản đồng bộ hiện tại (`data/raw/CSV Files/` chỉ có `UNSW-NB15_1..4.csv`, `NUSW-NB15_GT.csv`,
`NUSW-NB15_features.csv`, `UNSW-NB15_LIST_EVENTS.csv`). Phần 1 và Phần 3 của notebook phụ thuộc
hoàn toàn vào hai file này nên hiện **không tái lập được**; chỉ Phần 2 và 4 chạy được vì chúng
dùng `data/cleaned/*.parquet` (có sẵn).

Có thể hai file đó vẫn nằm trên Google Drive mà chưa đồng bộ xuống máy, hoặc đã bị di chuyển.
Cần xác nhận và khôi phục — nếu không, kết quả Phần 1 "trùng khít `data/cleaned`" là một khẳng
định không ai kiểm lại được.

### L9 — Vấn đề trình bày: vì sao notebook đọc rất khó

Đây là phần trả lời nhận xét "quá khó hiểu":

1. **13 cấu hình trong một danh sách phẳng, trộn 4 chiều.** Tên như `"12. HGB 42f + sua prior"`
   bắt người đọc tự nhớ rằng #12 khác #0 ở **ba** thứ (thuật toán, bộ feature, ngưỡng+prior).
   Không có bảng nào nói rõ cấu hình nào là phép so sánh đơn biến của cấu hình nào.
2. **Phần 3 và Phần 4 huấn luyện lại 21 model mà không chia sẻ gì với nhau** (8 ô thang đo +
   13 cấu hình), tổng ~22 phút. Hai phần dùng hai cách dựng dữ liệu khác nhau (`pool()` khử trùng
   lặp **toàn cục** trên train+test; `cleaned_with_contaminants()` khử trùng lặp **từng tập**),
   nên số của Phần 3 và Phần 4 không so trực tiếp được với nhau — và notebook không nói điều đó.
3. **Code in tiếng Việt không dấu, markdown tiếng Việt có dấu.** Người đọc phải nhảy qua lại
   giữa hai hệ chữ.
4. **Cell 33 dài 90 dòng markdown với 8 tiểu mục và 6 bảng** — nó là một báo cáo nhúng trong
   notebook, trùng lặp gần như hoàn toàn với `reports/Bao_cao_truy_nguyen_accuracy.md`.
   Hai bản sẽ lệch nhau ngay khi một bên được sửa.
5. **Không có bảng tóm tắt một dòng một yếu tố ở đầu notebook.** Người đọc phải chạy hết 22 phút
   mới thấy kết luận.

---

## 5. TỪNG KỸ THUẬT ĐÃ DÙNG VÀ KẾT QUẢ THỰC TẾ

### 5.1 Mười ba cấu hình khắc phục (test-final, 25.284 dòng)

| # | Kỹ thuật | Ngưỡng | Accuracy | Bal. acc | Recall | FPR | F1 | PR-AUC | Dùng nhãn test? | Đánh giá |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | RF 31f @0,5 — **baseline** | 0,500 | 0,8186 | 0,8461 | 0,9491 | 0,2569 | 0,7932 | 0,9414 | — | mốc |
| 1 | + ngưỡng tối ưu Acc trên validation | 0,535 | 0,8335 | 0,8550 | 0,9354 | 0,2254 | 0,8046 | 0,9414 | **Không** | ✅ rẻ, dùng được ngay |
| 2 | + sửa prior bằng EM | 0,500 | 0,8310 | 0,8535 | 0,9378 | 0,2309 | 0,8026 | 0,9414 | **Không** | ✅ dùng được, nhưng sửa thiếu |
| 3 | + sửa prior + ngưỡng trên test-dev | 0,794 | 0,8925 | 0,8725 | 0,7978 | 0,0528 | 0,8447 | 0,9414 | Có (test-dev) | ✅ hiệu quả nhất trên 31f |
| 4 | Căn chỉnh phân bố bằng phân vị | 0,500 | 0,7314 | 0,7561 | 0,8485 | 0,3363 | 0,6984 | **0,7736** | Không | ❌ **thất bại nặng** |
| 5 | #4 + sửa prior | 0,775 | 0,7617 | 0,7342 | 0,6312 | 0,1628 | 0,6600 | **0,7736** | Có | ❌ thất bại |
| 6 | RF 24f (bỏ 7 feature lệch nhất) | 0,500 | 0,8200 | 0,8476 | 0,9510 | 0,2557 | 0,7948 | 0,9393 | Không | ➖ vô tác dụng (+0,0014) |
| 7 | #6 + sửa prior | 0,780 | 0,8903 | 0,8722 | 0,8045 | 0,0600 | 0,8432 | 0,9393 | Có | ➖ kém #3 |
| 8 | HGB 31f @0,5 | 0,500 | 0,8215 | 0,8485 | 0,9498 | 0,2527 | 0,7959 | 0,9423 | Không | ➖ +0,0029, không đáng kể |
| 9 | HGB 31f + sửa prior | 0,841 | 0,8930 | 0,8704 | 0,7860 | 0,0451 | 0,8433 | 0,9423 | Có | ✅ ngang #3 |
| 10 | RF 42f (giữ feature ô nhiễm) @0,5 | 0,500 | 0,8353 | 0,8643 | 0,9727 | 0,2442 | 0,8124 | 0,9530 | Không | ✅ +0,0167 — **phép đo sạch nhất** của giá trị 11 feature |
| 11 | RF 42f + sửa prior | 0,817 | 0,9048 | **0,8920** | 0,8444 | 0,0603 | **0,8667** | 0,9530 | Có | ✅ **tốt nhất theo balanced acc & F1** |
| 12 | HGB 42f + sửa prior | 0,859 | **0,9050** | 0,8908 | 0,8376 | 0,0561 | 0,8660 | **0,9544** | Có | ⚠️ NB06 gọi là tốt nhất, nhưng hơn #11 đúng 0,0002 |

**Đọc bảng này cho đúng:**

- Các cấu hình 1, 2, 6, 8, 10 (và #4, đã thất bại) là nhóm **không cần nhãn test** → dùng được
  trong triển khai thật. Mức lợi tối đa của nhóm này là **+1,67 điểm** (#10), và nếu phải giữ
  31 feature thì chỉ **+1,49 điểm** (#1).
- Các cấu hình 3, 7, 9, 11, 12 lợi +7 đến +8,6 điểm nhưng **đều cần một mẫu có nhãn từ phân bố
  triển khai** để đặt ngưỡng. Đây không phải cải thiện của model, mà là đổi điểm vận hành.
- #4 và #5 là **kết quả âm được báo cáo trung thực** — điểm đáng khen của notebook.

### 5.2 Cái giá bị bỏ qua: đẩy ngưỡng lên làm sụp khả năng bắt tấn công

Notebook 06 báo cáo accuracy / F1 / FPR cải thiện, nhưng không đặt cạnh chi phí:

| Chỉ số | #0 baseline @0,5 | #12 @0,859 | Thay đổi |
|---|---|---|---|
| Recall tổng | 0,9491 | 0,8376 | **−0,1115** |
| FN (tấn công bị bỏ sót) | 472 | 1.505 | **+1.033 (+219%)** |
| FP (báo động giả) | 4.114 | 898 | −3.216 (−78%) |
| **Recall Fuzzers** | **0,8237** (†) | **0,4301** | **−0,3936** |

(†) lấy từ `reports/exp05/step6_fuzzers.json` — cùng model RF-A, cùng `test-final`, ngưỡng 0,5.

Notebook 06 có nêu "Fuzzers 0,430 vẫn là điểm yếu duy nhất" (§5.7) nhưng **không nói rằng
chính việc đẩy ngưỡng lên 0,859 đã làm nó tụt từ 0,824**. Người đọc §5.5 sẽ tưởng đây là một
điểm yếu sẵn có, không phải cái giá vừa phải trả. Với một IDS, bỏ sót thêm 1.033 cuộc tấn công
để giảm 3.216 báo động giả là một **quyết định đánh đổi cần nêu rõ và cần người quyết**, không
phải một "cải thiện" đơn thuần.

### 5.3 Năm thuật toán

| Thuật toán | PR-AUC val | PR-AUC test-final | ROC-AUC test-final | Acc @0,5 | Acc @ngưỡng | F1 @ngưỡng | Giây |
|---|---|---|---|---|---|---|---|
| Random Forest | 0,9849 | 0,9414 | 0,9594 | 0,8186 | 0,8925 | 0,8448 | 126 |
| HistGradientBoosting | 0,9833 | **0,9423** | 0,9594 | 0,8215 | 0,8930 | 0,8433 | 110 |
| Soft Voting (RF+ET+HGB) | 0,9847 | 0,9419 | 0,9591 | 0,8038 | **0,8950** | **0,8462** | 113 |
| Extra Trees | 0,9812 | 0,9285 | 0,9496 | 0,7694 | 0,8798 | 0,8250 | 115 |
| Logistic Regression | 0,9238 | **0,7281** | 0,8337 | 0,7270 | 0,7298 | 0,6091 | 26 |

- Biên độ 4 họ cây: **0,0138** PR-AUC. HGB hơn RF **+0,0009** — nằm trong nhiễu.
- Logistic Regression sụp từ 0,9238 → 0,7281. Giả thuyết *"model đơn giản chịu lệch phân bố tốt
  hơn"* bị **phủ định bằng số** — đây là một kết quả có giá trị.
- Soft Voting cho F1 cao nhất ở điểm vận hành nhưng PR-AUC vẫn trong cùng khoảng → không vượt trần.

---

## 6. SO SÁNH VỚI CÁC PHIÊN BẢN NOTEBOOK TRƯỚC

### 6.1 Cùng một tập đánh giá: `test-final` 25.284 dòng

Mọi dòng dưới đây đánh giá trên **đúng cùng 25.284 dòng** (`data/cleaned/test_split_v3.csv`,
seed 42), nên so trực tiếp được.

| Phiên bản | Cấu hình | Ngưỡng | Accuracy | Precision | Recall | F1 | FPR | PR-AUC | Ngưỡng chọn ở đâu |
|---|---|---|---|---|---|---|---|---|---|
| **NB02** | RF 100 cây, mặc định | 0,500 | 0,8156 | 0,6773 | 0,9491 | 0,7905 | 0,2616 | 0,9264 | không chọn |
| **NB03** | RF 300 cây đã tinh chỉnh | 0,515 | 0,8287 | 0,6965 | 0,9438 | 0,8015 | 0,2379 | 0,9420 | CV trên train-fit |
| **NB04** | + isotonic calibration, ngưỡng FPR ≤ 0,10 | 0,711 | 0,8820 | 0,8251 | 0,8605 | 0,8424 | 0,1055 | 0,9416 | test-dev, ràng buộc khai báo trước |
| **NB05** | RF đa lớp `1−P(Normal)`, FPR ≤ 0,10 | 0,686 | 0,8846 | 0,8259 | 0,8682 | 0,8465 | 0,1059 | 0,9427 | test-dev, ràng buộc khai báo trước |
| **NB05** | *(ablation)* RF 39 feature ô nhiễm, FPR ≤ 0,10 | 0,731 | 0,8951 | 0,8305 | 0,8968 | **0,8624** | 0,1059 | 0,9527 | test-dev, ràng buộc khai báo trước |
| **NB06** | #3 RF 31f + EM prior + ngưỡng max-Acc | 0,794 | 0,8925 | 0,8974 | 0,7978 | 0,8447 | 0,0528 | 0,9414 | test-dev, **không** ràng buộc |
| **NB06** | #12 HGB 42f + EM prior + ngưỡng max-Acc | 0,859 | **0,9050** | 0,8963 | 0,8376 | 0,8660 | 0,0561 | **0,9544** | test-dev, **không** ràng buộc; **cấu hình được chọn trên test-final** |

Lưu ý mốc baseline khác nhau giữa các notebook: NB02 dùng RF 100 cây không giới hạn độ sâu
(0,8156), từ NB03 trở đi dùng tham số đã tinh chỉnh (0,8186). Chênh 0,0030 này là do tham số,
không phải do dữ liệu.

### 6.2 Từng bước tiến thực chất là bao nhiêu

| Bước chuyển | Δ Accuracy | Δ PR-AUC | Bản chất của bước tiến |
|---|---|---|---|
| NB02 → NB03 | +0,0131 | **+0,0156** | **Thật** — tinh chỉnh tham số làm model xếp hạng tốt hơn |
| NB03 → NB04 | +0,0533 | −0,0003 | **Chỉ là điểm vận hành** — calibration + ngưỡng. PR-AUC không nhích |
| NB04 → NB05 | +0,0026 | +0,0011 | **Thật nhưng rất nhỏ** — đa lớp, p = 0,046 (`step7_final.json`) |
| NB05 → NB06 #12 | +0,0204 | +0,0117 | **Chủ yếu là 11 feature ô nhiễm được giữ lại** |
| NB05 *(ablation 39f)* → NB06 #12 | **+0,0098** | **+0,0017** | ⚠️ gần như **không có gì mới** |

Dòng cuối là dòng quan trọng nhất. Notebook 05 **đã** chạy ablation giữ lại feature ô nhiễm và
được 0,8951 accuracy / 0,9527 PR-AUC. Cấu hình "tốt nhất" của notebook 06 (0,9050 / 0,9544) chỉ
hơn **+0,0098 accuracy và +0,0017 PR-AUC** — và phần lớn khoảng đó đến từ việc notebook 06
**bỏ ràng buộc FPR ≤ 0,10** để tự do đẩy ngưỡng lên 0,859.

Hệ quả ở mặt bắt tấn công, cùng `test-final`:

| Phiên bản / cấu hình | Ngưỡng | FPR | Recall tổng | **Recall Fuzzers** |
|---|---|---|---|---|
| NB05 RF-A @0,5 | 0,500 | 0,2569 | 0,9491 | **0,8237** |
| NB05 RF-A @FPR≤10% | 0,695 | 0,1050 | 0,8607 | 0,5496 |
| NB05 RF đa lớp @FPR≤10% | 0,686 | 0,1059 | 0,8682 | 0,5676 |
| NB05 RF 39f @FPR≤10% | 0,731 | 0,1059 | 0,8968 | **0,6249** |
| **NB06 #12** | 0,859 | 0,0561 | 0,8376 | **0,4301** |

Notebook 06 mua thêm 0,0098 accuracy bằng **0,1948 Recall Fuzzers** so với cấu hình gần nhất
của notebook 05. Theo bất kỳ cách đọc nào của một hệ phát hiện xâm nhập, đây **không phải một
cải thiện**, mà là một điểm vận hành khác — bảo thủ hơn về báo động giả, dễ bị lọt hơn về tấn công.

### 6.3 Notebook 06 đóng góp mới được gì

| Đóng góp | Trước đó đã có chưa? |
|---|---|
| Rà soát tái lập **toàn bộ** NB01 so với `data/cleaned`, so từng giá trị | ❌ **Mới** — chưa notebook nào làm |
| Cơ chế bỏ trùng xoá 59% Attack vs 10–13% Normal | ❌ **Mới, có giá trị** |
| Chứng minh lệch tỷ lệ lớp 0,13 **có sẵn trong dữ liệu thô** | ❌ **Mới** — sửa được một câu sai trong báo cáo cũ + slide |
| Kiểm tra `df_shrink` có làm mất thông tin | ❌ **Mới** |
| Kiểm tra One-Hot: giá trị lạ, rò rỉ encoder | ❌ **Mới** |
| Thiết kế giai thừa 2×2×2 tách ba yếu tố | ❌ **Mới về thiết kế** — nhưng cách đo có lỗi L1, L2 |
| EM prior (Saerens 2002) ước lượng π từ test không nhãn | ❌ **Mới** — kết quả âm, báo cáo trung thực, đáng giá |
| Căn chỉnh phân bố bằng phân vị | ❌ **Mới** — thất bại, báo cáo trung thực |
| Extra Trees, Logistic Regression, Soft Voting | ❌ **Mới** (HGB thì NB05 đã có) |
| Mục "những điều KHÔNG được kết luận" | ✅ NB05 cũng có, nhưng NB06 viết kỹ hơn |

### 6.4 Notebook 06 thụt lùi so với notebook 05 ở đâu

| Hạng mục | Notebook 05 | Notebook 06 | Nhận xét |
|---|---|---|---|
| Chọn model / ngưỡng | trên **test-dev**, với ràng buộc `FPR ≤ 0,10` **khai báo trước** | `idxmax` accuracy trên **test-final** | ❌ **thụt lùi nặng** (lỗi L3) |
| Kiểm định thống kê | CI bootstrap cho **mọi** ứng viên khai báo trước (`step7_final.json`) | CI chỉ cho cấu hình vừa thắng trên test-final | ❌ winner's curse |
| Độ bền theo seed | có (`step8_seeds.json`: biên độ 0,00024) | không có | ❌ thiếu |
| KS lệch phân bố | trên dữ liệu **đã làm sạch**, chỉ 28 feature **trong model** | trên dữ liệu **thô**, 39 feature kể cả cột đã bỏ | ❌ kém hơn (lỗi L6) |
| Phân tích Fuzzers | riêng một thực nghiệm: phân vị xác suất, KS tách lớp, cơ cấu `service` | một bảng recall ở cuối | ❌ kém hơn |
| Hướng đa lớp `attack_cat` | có, và là ứng viên **thắng có ý nghĩa thống kê** (p = 0,046) | không thử | ❌ bỏ mất |
| Ràng buộc vận hành (FPR) | khai báo trước, giữ nguyên xuyên suốt | không có | ❌ thiếu |
| Câu hỏi khử trùng lặp | `experiment_nodedup`: giữ nguyên tập đánh giá, ΔPR-AUC = −0,0027 (p≈0) | đổi cả tập đánh giá, +0,0294 accuracy | ❌ phép đo bẩn hơn, không đối chiếu (lỗi L2) |
| Tái lập được không | có (dùng `data/cleaned`) | **không** — thiếu file raw (lỗi L8) | ❌ |

---

## 7. ĐÁNH GIÁ TỔNG: NOTEBOOK 06 CẢI THIỆN ĐƯỢC GÌ, KHÔNG CẢI THIỆN ĐƯỢC GÌ

**Cải thiện thật (giữ lại):**

1. Đây là notebook **đầu tiên** kiểm chứng toàn bộ chuỗi 01→04 bằng assert thật thay vì tin
   báo cáo cũ. Kết luận "không có lỗi cài đặt" là một kết luận có bằng chứng.
2. Ba phát hiện về **cơ chế dữ liệu** (bỏ trùng tác động lệch theo lớp; lệch tỷ lệ lớp có sẵn
   trong dữ liệu thô; lệch phân bố tập trung ở lớp Normal) là đóng góp mới và sửa được lỗi
   trong tài liệu cũ.
3. Hai **kết quả âm** (EM sửa thiếu; căn chỉnh phân vị phá PR-AUC) được báo cáo đầy đủ.
   Đây là điểm mạnh nhất về mặt liêm chính học thuật của cả dự án.
4. Khung giải thích "khoảng cách với các bài báo 97–98% là khoảng cách **giao thức đánh giá**"
   là đúng và biến một điểm yếu thành một kết quả có giải thích được.

**Không phải cải thiện (không dùng để báo cáo):**

5. Con số **0,9050** accuracy không phải năng lực mới. Nó là ablation feature ô nhiễm của
   notebook 05 (0,8951) cộng với một ngưỡng mạnh tay hơn, chọn trên tập dùng để báo cáo.
6. Các con số độ lớn yếu tố **+0,0955 / +0,0112 / +0,0294** không dùng được như đang viết,
   vì ba ô so sánh có tập đánh giá và tỷ lệ lớp khác nhau.
7. Khẳng định "**8,5 lần**" phải sửa thành "**2,6–4,9 lần**".
8. Tỷ lệ "**85% / 15%**" phải sửa thành "**77% điểm vận hành / 19% feature / 3% thuật toán**".
9. CI95 [+0,0812; +0,0914] không dùng được vì cấu hình được chọn trên chính tập kiểm định.

---

## 8. CẦN LÀM GÌ ĐỂ NOTEBOOK 06 THÀNH MỘT NOTEBOOK KHOA HỌC

Sửa theo thứ tự ưu tiên. Mỗi việc đều nhỏ, không cần chạy lại từ đầu.

| Ưu tiên | Việc | Cell cần sửa | Chi phí |
|---|---|---|---|
| 1 | Đổi `best_name` sang chọn theo accuracy **trên `test-dev`**, giữ bootstrap trên `test-final` | cell 29, 1 dòng | 0 phút (dùng lại xác suất đã có) |
| 2 | Khai báo trước ràng buộc vận hành (ví dụ `FPR ≤ 0,10`) và dùng nó làm quy tắc chọn ngưỡng, giống NB04/NB05 | cell 24 (`thr_rule`) | ~5 phút |
| 3 | Thêm cột `balanced_acc` và `roc_auc` vào **bảng độ lớn ba yếu tố**; ghi chú rõ `n_test` và `π_test` của từng ô khác nhau | cell 18, in thêm 2 bảng | 0 phút (số đã có trong `LAD`) |
| 4 | Tính `eff_dedup` bằng trung bình **cả 4** cặp ô, in cả khoảng min–max | cell 18 | 0 phút |
| 5 | Dẫn chiếu `reports/dedup_vs_nodedup/` ở chỗ nói về yếu tố khử trùng lặp, và nói rõ phép đo nào sạch hơn | markdown cell 21 | 0 phút |
| 6 | Thay tỷ lệ "85/15" bằng bảng phân rã accuracy ba thành phần (#0→#10, #0→#8, phần còn lại) | markdown cell 33 | 0 phút |
| 7 | Tính lại KS trên dữ liệu **đã làm sạch**, chỉ trên feature trong model; cập nhật danh sách feature lệch nhất | cell 19 | ~2 phút |
| 8 | Thêm bảng Recall-theo-loại-tấn-công **cho cả baseline**, đặt cạnh cấu hình tốt nhất | cell 31 | 0 phút (chỉ cần thêm `p_base`) |
| 9 | Sửa cell 28 để in biên độ 4 họ cây **và** biên độ gồm Logistic, kèm một dòng nói rõ vì sao tách ra | cell 28 | 0 phút |
| 10 | Khôi phục `data/raw/CSV Files/Training and Testing Sets/` hoặc đổi Phần 1 sang đọc `data/cleaned` kèm ghi chú | cell 1, 3 | cần xác nhận file |
| 11 | Thêm bảng tóm tắt một-dòng-một-yếu-tố ngay sau cell 0; rút cell 33 xuống còn 10 dòng + link tới báo cáo | cell 0, 33 | ~15 phút viết |
| 12 | Hợp nhất `pool()` và `cleaned_with_contaminants()` về một cách dựng dữ liệu, hoặc ghi chú rõ số Phần 3 và Phần 4 không so trực tiếp được | cell 17, 23 | ~10 phút |

---

## 9. NGUỒN SỐ LIỆU DÙNG CHO BÁO CÁO NÀY

| File | Dùng để |
|---|---|
| `notebooks/06_Root_Cause_Audit.ipynb` | Đọc lại toàn bộ code + output đã lưu của 34 cell |
| `reports/audit06/ket_qua_audit06.json` | Nguồn của mọi phép tính lại (thang đo, KS, 13 cấu hình, 5 thuật toán, bootstrap) |
| `models/random_forest_v2_metrics.json`, `..._v3_metrics.json` | Đối chiếu baseline NB03 / NB04 |
| `notebooks/model_comparison_results.csv` | Số NB02 / NB03 / NB04 trên cùng `test-final` |
| `reports/exp05/step5_shift.json` | KS trên dữ liệu đã làm sạch; CV; adversarial AUC |
| `reports/exp05/step6_fuzzers.json` | Recall Fuzzers của baseline ở ngưỡng 0,5 và 0,711 |
| `reports/exp05/step7_final.json` | Cấu hình NB05, CI bootstrap, recall theo loại tại điểm vận hành |
| `reports/exp05/step8_seeds.json` | Độ bền theo seed của NB05 |
| `reports/dedup_vs_nodedup/Bao_cao_dedup_vs_nodedup.md` | Phép đo sạch về khử trùng lặp để đối chiếu lỗi L2 |
| `reports/Bao_cao_truy_nguyen_accuracy.md` | Bản báo cáo của NB06 được rà soát |

**Không có file nào trong `data/`, `models/`, `notebooks/` hay `reports/audit06/` bị sửa đổi
khi làm báo cáo này.** Mọi phép tính lại chạy trên bản sao trong thư mục tạm.

### Công thức của các con số tính lại

- Độ lớn yếu tố, đúng công thức cell 18 nhưng đổi chỉ số:
  `cách chia = TB[ ô(có, f, random) − ô(có, f, official) ]` với f ∈ {31, 42};
  `feature = TB[ ô(có, 42, c) − ô(có, 31, c) ]` với c ∈ {official, random};
  `bỏ dedup = TB[ ô(không, f, c) − ô(có, f, c) ]` trên cả 4 cặp.
- Phân rã accuracy: `(#10 − #0)` = phần feature; `(#8 − #0)` = phần thuật toán;
  `(#12 − #0) − (#10 − #0) − (#8 − #0)` = phần điểm vận hành.
- KS trung bình theo phạm vi: lọc `3.3_ks` theo việc feature có nằm trong
  `CONTAM ∪ USELESS` hay không (11 feature bị bỏ / 28 feature trong model).
