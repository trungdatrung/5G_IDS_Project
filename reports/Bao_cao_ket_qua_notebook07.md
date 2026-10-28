# Notebook 07 — Kết quả chạy lại hợp nhất

**Dự án:** 5G IDS / UNSW-NB15 · phân loại nhị phân `label` (0 = Normal, 1 = Attack)
**Notebook:** `notebooks/07_Consolidated_Rerun.ipynb` — 39 cell, chạy hết, **0 cell lỗi**
**Ngày chạy:** 08/10/2026 · Random Forest 300 cây · seed 42
**Môi trường:** Python 3.11.16 · scikit-learn 1.9.1 · pandas 3.0.6 · numpy 2.4.6
**Số liệu gốc:** `reports/rerun07/` — `ket_qua_rerun07.json`, `bang_cau_hinh.csv`,
`so_sanh_thuat_toan.csv`, `thang_do_2x2.csv`, `dedup_cung_tap_danh_gia.csv`,
`recall_theo_loai.csv`, `confusion_truoc_sau.png`, `tom_tat.csv`

**Cấu trúc notebook:** 57 ô — 23 ô code, 34 ô Text. Ô code **chỉ tính và hiện bảng**; mọi diễn
giải nằm ở ô Text riêng ngay sau đó. Toàn notebook còn 25 lệnh `print`, tất cả thuộc ba loại:
tiến trình fit, `assert` đã qua, và một dòng số. Không hàm nào in gì.

**Mục đích:** chạy lại các phép đo của notebook 03–06 theo giao thức chặt hơn, sau khi bản rà
soát `Bao_cao_ra_soat_notebook06.md` tìm ra 9 lỗi phương pháp trong notebook 06. Đây **không**
phải một thử nghiệm mới — mục tiêu là xác định con số nào của notebook 06 đứng vững và con số nào
phải thay.

**Không file nào trong `data/`, `models/`, `notebooks/01..06` bị thay đổi.** Notebook 07 chỉ ghi
vào `reports/rerun07/`.

---

## 0. TÓM TẮT

**Tái lập hoàn hảo.** Baseline RF 31 feature @0,5 trên `test-final` cho accuracy
**0,818620** — khớp `models/random_forest_v3_metrics.json` tới **6 chữ số thập phân**.
Mọi so sánh sau đó đứng trên một mốc đã được xác nhận.

**Năm kết luận của notebook 06 đứng vững**, và một trong số đó nay có bằng chứng mạnh hơn.
**Bốn con số của notebook 06 phải thay.**

**Kết quả quan trọng nhất:** đo câu hỏi khử trùng lặp bằng cách giữ nguyên tập đánh giá cho
**ΔPR-AUC = −0,0027** — **trùng khít tới 4 chữ số** với thực nghiệm `experiment_nodedup` đã làm
độc lập từ 02/10/2026. Notebook 06 báo cáo **+0,0294** cho cùng câu hỏi vì nó đổi cả tập đánh giá.
Đây là xác nhận chéo rõ ràng rằng phép đo của notebook 06 sai, không phải phép đo cũ sai.

**Cấu hình được chọn** (quy tắc khai báo trước, chốt trên `test-dev`): RF 39 feature,
ngưỡng 0,7311 → trên `test-final`: **Accuracy 0,8952 · Balanced acc 0,8955 · MCC 0,7794 ·
Recall 0,8967 · FPR 0,1058 · PR-AUC 0,9527**. So baseline: FP giảm 4.114 → 1.694,
FN tăng 472 → 957.

Và điều đáng chú ý nhất: cấu hình này **gần như trùng khít với cấu hình notebook 05 đã chọn**
(ngưỡng 0,7309 → Accuracy 0,8951 · Fuzzers 0,6249). Notebook 07 dò lại từ **7 thuật toán** thay
vì 4, theo một quy tắc độc lập, và **đến lại đúng chỗ cũ**. Nghĩa là điểm vận hành của notebook 05
là đúng, và notebook 06 là một đường vòng.

---

## 1. TÁI LẬP — ĐẠT

| Hạng mục | Notebook 07 đo được | Số đã lưu từ trước | Khớp |
|---|---|---|---|
| 4 tập | 79.147 / 19.787 / 25.283 / 25.284 | giống | ✅ |
| Tỷ lệ Attack 4 tập | 0,4964 / 0,4964 / 0,3665 / 0,3665 | giống | ✅ |
| Baseline accuracy `test-final` | **0,818620** | 0,818620 | ✅ 6 chữ số |
| TN / FP / FN / TP | 11.903 / 4.114 / 472 / 8.795 | giống | ✅ |
| PR-AUC `test-final` | 0,941405 | 0,941405 | ✅ |
| Validation accuracy | 0,932228 | 0,932228 | ✅ |

Cách chia `test-dev` / `test-final` lấy từ `data/cleaned/test_split_v3.csv` thay vì gọi lại
`train_test_split`, nên tập báo cáo được cố định bằng **dữ liệu** chứ không phụ thuộc seed.

---

## 2. CHẨN ĐOÁN — kết luận của NB06 đứng vững, và nay rõ hơn

| Tập | PR-AUC | ROC-AUC | Accuracy @0,5 | Balanced acc @0,5 | MCC @0,5 |
|---|---|---|---|---|---|
| train-fit (học thuộc) | 0,9985 | 0,9988 | 0,9775 | 0,9776 | 0,9552 |
| CV 5-fold trong train-fit | 0,9830 ± 0,0015 | — | — | — | — |
| validation (phân bố train) | 0,9849 | 0,9860 | 0,9322 | 0,9324 | 0,8657 |
| test-dev (phân bố test) | 0,9429 | 0,9600 | 0,8154 | 0,8438 | 0,6620 |
| test-final (phân bố test) | 0,9414 | 0,9594 | 0,8186 | 0,8461 | 0,6672 |

Tụt từ validation sang test-final:

| Chỉ số | Mức tụt | Ý nghĩa |
|---|---|---|
| ROC-AUC | **−0,0266** | năng lực **xếp hạng** gần như giữ nguyên |
| PR-AUC | −0,0435 | tụt một phần do π_test thấp hơn |
| MCC @0,5 | **−0,1984** | **điểm vận hành sụp hẳn** |

**Đây là phát hiện được làm rõ hơn so với notebook 06.** NB06 chỉ nói "lệch phân bố". Bộ ba chỉ số
trên nói chính xác hơn: model vẫn **xếp hạng** gần như tốt như cũ (ROC-AUC chỉ mất 2,7%), nhưng
**ngưỡng 0,5 đặt sai chỗ** nên chất lượng quyết định ở ngưỡng đó sụp (MCC mất 20 điểm). Mức tụt
MCC gấp **7,5 lần** mức tụt ROC-AUC. Đó là dấu vân tay của *sai điểm vận hành*, không phải của
*model yếu*.

### Lệch phân bố nằm ở đâu — tính trên dữ liệu đã làm sạch, chỉ feature trong model

| Phạm vi | KS TB riêng Normal | KS TB riêng Attack | Tỷ lệ |
|---|---|---|---|
| **28 feature số trong model, dữ liệu đã làm sạch** *(đúng cách)* | **0,1300** | **0,0492** | **2,64×** |
| 39 feature số, dữ liệu thô *(NB06 làm)* | 0,1097 | 0,0385 | 2,85× |

Kết luận "lệch tập trung ở lớp Normal" **đứng vững** ở mọi cách tính. Nhưng **danh sách feature
phải đổi**: NB06 nêu `sttl` (0,2763) và `ct_state_ttl` (0,2559) làm hai feature lệch nhất, mà cả
hai **nằm trong 11 cột đã bị bỏ** — chúng không thể giải thích mức tụt của model 31 feature.

Năm feature lệch nhất **thật sự trong model**:

| Feature | KS riêng Normal | Trung vị train | Trung vị test |
|---|---|---|---|
| `ackdat` | 0,2698 | 0,0002 | 0,0288 |
| `dload` | 0,2391 | 9.923 | 6.971 |
| `tcprtt` | 0,2258 | 0,0009 | 0,0530 |
| `synack` | 0,2250 | 0,0007 | 0,0100 |
| `dmean` | 0,2061 | 80 | 66 |

Bốn trong năm là **thời gian bắt tay TCP** (`ackdat`, `tcprtt`, `synack`) và lưu lượng chiều về
(`dload`, `dmean`). Trung vị `ackdat` của lớp Normal tăng **144 lần** từ train sang test.

*(Ghi chú sửa số của chính tôi: trong `Bao_cao_ra_soat_notebook06.md` §L6 tôi đưa con số 3,39× —
đó là KS tính trên dữ liệu **thô** rồi lọc lấy feature trong model. Con số đúng để dùng là
**2,64×**, tính trên dữ liệu **đã làm sạch** — tức phân bố mà model thật sự nhìn thấy.)*

### Chặn trên của phép sửa tỷ lệ lớp

| | Accuracy | Balanced acc | MCC | Recall | FPR | PR-AUC |
|---|---|---|---|---|---|---|
| Baseline @0,5 | 0,8186 | 0,8461 | 0,6672 | 0,9491 | 0,2569 | 0,9414 |
| Sửa prior bằng π **thật**, vẫn @0,5 | **0,8673** | **0,8726** | **0,7274** | 0,8921 | **0,1470** | 0,9414 |

Không đổi model, không đổi ngưỡng: **+4,87 điểm** accuracy, FPR giảm gần một nửa, và **PR-AUC
không nhích một ly** — vì phép sửa prior là đơn điệu tăng. Đây là bằng chứng gọn nhất cho luận
điểm "vấn đề nằm ở điểm vận hành".

---

## 3. THANG ĐO 2×2 — sửa lỗi 1 của NB06

Bốn ô, cùng thuật toán / tham số / seed. **Tập đánh giá của bốn ô khác nhau**, nên bảng in rõ
`n` và `π_test` từng ô:

| Khử trùng | Cách chia | n_test | π_test | Rò rỉ | Accuracy | Balanced acc | MCC | ROC-AUC |
|---|---|---|---|---|---|---|---|---|
| có | official | 47.361 | 0,3332 | 0,000 | 0,8160 | 0,8462 | 0,6535 | 0,9543 |
| có | random | 47.361 | 0,4221 | 0,000 | 0,9074 | 0,9037 | 0,8098 | 0,9760 |
| không | official | 80.816 | 0,5560 | **0,2594** | 0,8710 | 0,8578 | 0,7495 | 0,9797 |
| không | random | 80.816 | 0,6406 | **0,4624** | 0,9475 | 0,9457 | 0,8868 | 0,9916 |

π_test chạy từ 0,3332 đến 0,6406 — chênh **0,3074**. Accuracy và PR-AUC đều phụ thuộc π_test nên
**không so được giữa các ô**. Độ lớn hai yếu tố, đo bằng bốn chỉ số:

| Yếu tố | Accuracy | PR-AUC | **Balanced acc** | **ROC-AUC** |
|---|---|---|---|---|
| Đổi cách chia official → random | +0,0840 | +0,0268 | **+0,0727** | **+0,0168** |
| Bỏ khử trùng lặp (TB 2 ô) | +0,0476 | +0,0435 | **+0,0268** | **+0,0205** |
| Bỏ khử trùng lặp (chỉ chia official) | +0,0550 | +0,0599 | **+0,0116** | +0,0253 |
| **Tỷ lệ chia / khử trùng lặp** | 1,76× | 0,62× | **2,71×** | **0,82×** |

**Đây là lý do con số "8,5 lần" của NB06 không dùng được.** Thứ tự và độ lớn của các yếu tố
**thay đổi hoàn toàn** tuỳ chỉ số:

- Theo **balanced accuracy**: cách chia lớn hơn khử trùng lặp **2,7 lần**.
- Theo **ROC-AUC**: khử trùng lặp **lớn hơn** cách chia một chút (0,82×).

Không có một con số duy nhất nào mô tả được "độ lớn của yếu tố". Cách trình bày đúng là nêu cả
bảng và nói rõ chỉ số nào bền với tỷ lệ lớp.

Cột **rò rỉ** là chỗ phải đọc trước mọi cột khác: ở nhánh không khử trùng lặp, **25,9%**
(official) và **46,2%** (random) dòng test là **bản sao chính xác** của một dòng train. Con số
25,94% này trùng khít với `experiment_nodedup` đã đo độc lập.

---

## 4. KHỬ TRÙNG LẶP, ĐO ĐÚNG CÁCH — sửa lỗi 2, kết quả quan trọng nhất

Hai model, cùng thuật toán / tham số / seed. Khác **duy nhất một thứ**: dữ liệu huấn luyện.
Cả hai đo trên **đúng cùng 25.284 dòng** `test-final`.

| | n_train | Rò rỉ vào test-final | Accuracy | Balanced acc | MCC | Recall | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|---|---|---|
| train = `data/cleaned` (**có** khử trùng lặp) | 79.147 | 3,22% | **0,8186** | **0,8461** | **0,6672** | 0,9491 | 0,2569 | **0,9594** | **0,9414** |
| train = `V1_nodedup` (**không** khử trùng lặp) | 136.412 | 3,67% | 0,8179 | 0,8458 | 0,6666 | 0,9503 | 0,2587 | 0,9584 | 0,9387 |

Hiệu (không khử − có khử): **ΔPR-AUC = −0,0027** · Δbalanced acc = −0,0003 · ΔMCC = −0,0006 ·
ΔROC-AUC = −0,0008 · Δaccuracy = −0,0007.

### Ba phép đo cùng một câu hỏi, đặt cạnh nhau

| Nguồn | Cách đo | Kết quả |
|---|---|---|
| `experiment_nodedup` (02/10/2026) | giữ nguyên tập đánh giá | **−0,0027 PR-AUC**, CI95 [−0,0037; −0,0017], p ≈ 0 |
| **Notebook 07** (08/10/2026) | giữ nguyên tập đánh giá | **−0,0027 PR-AUC** |
| Notebook 06 (03/10/2026) | đổi **cả** tập đánh giá | +0,0294 accuracy |

Hai phép đo độc lập dùng cách đúng ra **cùng một con số tới 4 chữ số**. Phép đo của notebook 06
lệch dấu vì nó đổi cả tập đánh giá.

### Vì sao ở Phần 3 bỏ khử trùng lặp lại "đẹp hơn"

Rò rỉ vào `test-final` **gần như bằng nhau** ở hai nhánh (3,22% và 3,67%), vì `V1_nodedup` chứa
đúng cùng tập **dòng phân biệt** như `data/cleaned`, chỉ thêm bản lặp. Tập dòng phân biệt không
đổi ⇒ rò rỉ không đổi ⇒ không có lợi thế nào.

Con số đẹp chỉ xuất hiện khi **tập đánh giá cũng còn dòng trùng** (80.816 dòng ở Phần 3, rò rỉ
25,9–46,2%). Lúc đó model không cần tổng quát hoá, chỉ cần nhớ lại dòng đã thấy trong train —
đúng pitfall P1/P3 của Arp et al.

**Kết luận: nhân đôi dữ liệu train bằng bản lặp không giúp gì, thậm chí kém hơn một chút.
Số lần lặp chỉ là trọng số mẫu ngầm. Bước khử trùng lặp là ĐÚNG và nên giữ.**

### Phát hiện phụ

Ngay cả bộ dữ liệu chính thức **đã** khử trùng lặp vẫn còn **3,22%** dòng `test-final` trùng khít
với một dòng train. Nguyên nhân: notebook 01 khử trùng lặp **riêng trong từng tập** (train riêng,
test riêng), không khử chéo giữa hai tập. Mức này nhỏ và không đổi kết luận, nhưng nên nêu khi
báo cáo để không ai phát hiện ra sau rồi nghi ngờ phần còn lại.

---

## 5. BẢY THUẬT TOÁN — sửa lỗi 7

Cùng 31 feature (trừ dòng 39f), cùng cách chia, cùng seed. Ngưỡng của mọi dòng đều chọn
**trên `test-dev`** theo ràng buộc `FPR ≤ 0,10`.

| Thuật toán | PR-AUC val | PR-AUC dev | PR-AUC final | ROC-AUC final | Acc @0,5 | Ngưỡng (từ dev) | Acc @ngưỡng | Bal acc @ngưỡng | Recall @ngưỡng | FPR @ngưỡng |
|---|---|---|---|---|---|---|---|---|---|---|
| **RF 39f (NB05)** | **0,9881** | **0,9525** | **0,9527** | **0,9690** | 0,8345 | 0,7311 | **0,8952** | **0,8955** | **0,8967** | 0,1058 |
| RF đa lớp `1−P(Normal)` | 0,9842 | 0,9453 | 0,9427 | 0,9607 | 0,8270 | 0,6859 | 0,8846 | 0,8812 | 0,8682 | 0,1059 |
| HGB | 0,9833 | 0,9435 | 0,9423 | 0,9594 | 0,8215 | 0,7153 | 0,8786 | 0,8739 | 0,8563 | 0,1085 |
| Soft Voting (RF+ET+HGB) | 0,9847 | 0,9430 | 0,9419 | 0,9591 | 0,8038 | 0,7013 | 0,8790 | 0,8742 | 0,8560 | 0,1077 |
| Random Forest (baseline) | 0,9849 | 0,9429 | 0,9414 | 0,9594 | 0,8186 | 0,6949 | 0,8825 | 0,8779 | 0,8607 | 0,1050 |
| Extra Trees | 0,9812 | 0,9292 | 0,9285 | 0,9496 | 0,7694 | 0,7220 | 0,8702 | 0,8619 | 0,8309 | 0,1071 |
| Logistic Regression | 0,9238 | 0,7326 | **0,7330** | 0,8349 | 0,7285 | 0,8635 | 0,7296 | 0,6673 | **0,4341** | 0,0995 |

Biên độ PR-AUC trên `test-final`, **báo cáo cả hai cách** như lỗi 7 yêu cầu:

| Cách tính | Biên độ | Khoảng tụt val → final | Đọc ra sao |
|---|---|---|---|
| Gồm cả Logistic Regression | **0,2197** | 0,0428 | biên độ **lớn hơn** khoảng tụt ⇒ "chọn thuật toán CÓ quan trọng" |
| Chỉ 6 họ mạnh | **0,0242** | 0,0428 | khoảng tụt lớn gấp **1,8 lần** ⇒ "trong các họ phù hợp, đổi thuật toán không phải đòn bẩy" |

**Cả hai đều đúng, và phải nói cả hai.** Notebook 06 in ra 0,2142 rồi kết luận bằng 0,0138 mà
không nói đã loại Logistic Regression. Cách phát biểu đúng:

- **Chọn sai họ thuật toán thì mất rất nhiều.** Logistic Regression: PR-AUC 0,9238 (val) →
  0,7330 (final). Giả thuyết "model đơn giản chịu lệch phân bố tốt hơn" bị **phủ định bằng số** —
  giữ nguyên kết luận của NB06.
- **Trong các họ đã phù hợp, chênh nhau không đáng kể.** Giữa 31 feature: RF đa lớp 0,9427 so với
  RF 0,9414 = **+0,0013**. Đúng bằng con số notebook 05 đã đo (p = 0,046).

### Thu hồi được nhánh "giữ feature ô nhiễm"

Hai file CSV thô không có nên không fit lại được model trên bộ feature đầy đủ. **Nhưng** notebook
05 đã lưu xác suất dự đoán của nhánh 39 feature vào `reports/exp05/ablation_proba.npz`. Notebook 07
nạp các mảng đó và **tự kiểm tra căn chỉnh**: chấm lại mảng 31 feature bằng nhãn của chính nó cho
`accuracy = 0,818620` và `PR-AUC = 0,941405` — khớp 6 chữ số, nên thứ tự dòng là một.

Hiệu quả sạch của 8 feature ô nhiễm, **cùng 25.284 dòng, cùng ngưỡng 0,5**:

| Chỉ số | Δ |
|---|---|
| Accuracy | **+0,0159** |
| Balanced accuracy | **+0,0171** |
| MCC | **+0,0330** |
| ROC-AUC | +0,0115 |
| PR-AUC | **+0,0113** |

Khớp với con số +0,0167 / +0,0116 mà bản rà soát tính từ 13 cấu hình của notebook 06. Nay nó được
đo trên tập đánh giá cố định và theo đúng quy tắc chọn — **tốt hơn cả cách notebook 06 đo nó**.

**Quyết định vẫn thuộc về nhóm:** 8 feature này đáng khoảng +1,6 điểm accuracy, nhưng `sttl` và
`ct_state_ttl` cũng chính là hai feature lệch phân bố nhất trong dữ liệu thô, và lập luận
D'hooge et al. 2022 về việc chúng mã hoá sẵn nhãn vẫn còn đó. Nay cái giá đã **đo được** chứ
không còn là ước đoán.

---

## 6. CẤU HÌNH ĐƯỢC CHỌN — sửa lỗi 3

### Quy tắc, khai báo trong cell 0 trước khi chạy

> Tối đa **Recall** với ràng buộc **FPR ≤ 0,10**, đo **trên `test-dev`**.
> `test-final` chỉ chạm một lần ở bước báo cáo.

14 ứng viên (7 thuật toán × 2 cách sửa prior) được chấm điểm **chỉ trên `test-dev`**:

| Thuật toán | Ngưỡng | dev: Recall | dev: FPR | dev: Bal acc |
|---|---|---|---|---|
| **RF 39f (NB05)** | **0,7311** | **0,8920** | 0,0999 | **0,8960** |
| RF đa lớp | 0,6859 | 0,8657 | 0,1000 | 0,8829 |
| RF | 0,6949 | 0,8556 | 0,1000 | 0,8778 |
| Soft Voting | 0,7013 | 0,8510 | 0,0997 | 0,8756 |
| HGB | 0,7153 | 0,8503 | 0,0999 | 0,8752 |
| Extra Trees | 0,7220 | 0,8278 | 0,0999 | 0,8639 |
| Logistic Regression | 0,8635 | 0,4371 | 0,1000 | 0,6686 |

Logistic Regression **thoả** ràng buộc FPR nhưng Recall chỉ 0,44 nên bị quy tắc loại tự nhiên —
bằng chứng quy tắc hoạt động đúng: nó không thưởng cho model giữ FPR thấp bằng cách bỏ sót gần
hết tấn công.

### Đo một lần trên `test-final`

| | n | π_test | Accuracy | Bal acc | MCC | Precision | Recall | F1 | FPR | PR-AUC | TN | FP | FN | TP |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Baseline RF 31f @0,5 | 25.284 | 0,3665 | 0,8186 | 0,8461 | 0,6672 | 0,6813 | 0,9491 | 0,7932 | 0,2569 | 0,9414 | 11.903 | 4.114 | 472 | 8.795 |
| **Được chọn: RF 39f @0,7311** | 25.284 | 0,3665 | **0,8952** | **0,8955** | **0,7794** | **0,8253** | 0,8967 | **0,8624** | **0,1058** | **0,9527** | **14.323** | **1.694** | 957 | 8.310 |

| Thay đổi | Δ |
|---|---|
| Accuracy | **+0,0765** |
| Balanced accuracy | **+0,0494** |
| MCC | **+0,1122** |
| Precision | +0,1440 |
| Recall | **−0,0523** |
| F1 | +0,0692 |
| FPR | **−0,1511** |
| PR-AUC | +0,0113 |
| Báo động giả (FP) | 4.114 → **1.694** (−2.420, −59%) |
| Tấn công bỏ sót (FN) | 472 → **957** (+485, +103%) |

### Notebook 07 độc lập đến lại đúng cấu hình của notebook 05

| | Ngưỡng | Accuracy | F1 | FPR | Recall Fuzzers |
|---|---|---|---|---|---|
| Notebook 05 chọn (RF 39f, FPR ≤ 0,10) | 0,7309 | 0,8951 | 0,8624 | 0,1059 | 0,6249 |
| **Notebook 07 chọn** (dò lại từ 7 thuật toán) | **0,7311** | **0,8952** | **0,8624** | 0,1058 | 0,6244 |

Hai lần dò độc lập, hai bộ ứng viên khác nhau, cùng một đích. **Điểm vận hành của notebook 05 là
đúng.** Notebook 06 đi chệch khỏi nó vì bỏ ràng buộc FPR và chọn trên tập báo cáo.

---

## 7. NHÁNH KHÔNG DÙNG NHÃN TEST

Mọi cấu hình ở Phần 6 cần `test-dev` **có nhãn** để đặt ngưỡng. Trong triển khai thật, mẫu có nhãn
từ miền triển khai có thể không có. Nhánh hoàn toàn không dùng nhãn test:

| Cấu hình (RF 31 feature) | Ngưỡng | Accuracy | Bal acc | MCC | Recall | FPR |
|---|---|---|---|---|---|---|
| 0. Baseline @0,5 | 0,5000 | 0,8186 | 0,8461 | 0,6672 | 0,9491 | 0,2569 |
| 1. Ngưỡng tối ưu Acc trên validation | 0,5349 | 0,8335 | 0,8550 | 0,6844 | 0,9354 | 0,2254 |
| 2. Sửa prior bằng EM, vẫn @0,5 | 0,5000 | 0,8310 | 0,8535 | 0,6814 | 0,9378 | 0,2309 |
| 3. EM + ngưỡng trên validation | 0,5066 | 0,8333 | 0,8548 | 0,6841 | 0,9354 | 0,2258 |
| *chặn trên: sửa prior bằng π **thật*** | 0,5000 | *0,8673* | *0,8726* | *0,7274* | *0,8921* | *0,1470* |

**Tốt nhất trong toàn bộ nhóm không cần nhãn test** (gồm cả 39 feature):

| Cấu hình | Ngưỡng | Accuracy | Bal acc | MCC | Recall | FPR |
|---|---|---|---|---|---|---|
| **RF 39f + EM + ngưỡng từ validation** | 0,5148 | **0,8460** | **0,8704** | **0,7140** | **0,9618** | 0,2210 |
| RF 39f + ngưỡng từ validation | 0,5329 | 0,8460 | 0,8703 | 0,7139 | 0,9617 | 0,2210 |
| HGB + ngưỡng từ validation | 0,5881 | 0,8507 | 0,8639 | 0,7046 | 0,9131 | 0,1854 |

**Đây là một cấu hình đáng chú ý mà notebook 06 không tìm ra.** Nó **không dùng một nhãn nào của
tập test**, mà vẫn đạt balanced accuracy **0,8704** (so với 0,8461 của baseline) **trong khi giữ
Recall ở 0,9618** — cao hơn cả baseline. Nếu nhóm muốn một cấu hình triển khai được mà không cần
mẫu có nhãn từ miền đích, đây là cấu hình nên dùng, không phải cấu hình ở Phần 6.

### EM sửa thiếu — xác nhận phát hiện của notebook 06

| | Giá trị |
|---|---|
| π(train-fit) | 0,4964 |
| π(test) ước lượng bằng EM | **0,4684** |
| π(test) thật | **0,3665** |

Khoảng cần sửa là 0,1299. EM chỉ sửa được 0,0280, tức **21,6%** — còn thiếu **78,4%**.

Lý do, nay có bằng chứng từ Phần 2: EM giả định **chỉ** có dịch chuyển tỷ lệ lớp, tức P(x|y) không
đổi. KS riêng lớp Normal gấp 2,64 lần lớp Attack ⇒ P(x | y=0) **có đổi thật** ⇒ giả định bị vi phạm.
**Phát hiện này của notebook 06 đứng vững hoàn toàn.**

### Phát hiện mới: khi đã có nhãn, sửa prior bằng EM là DƯ THỪA

Trong bảng 14 ứng viên ở Phần 6, hai dòng "sửa prior = không" và "sửa prior = EM" của **mỗi**
thuật toán cho điểm `test-dev` **giống hệt nhau**, và trên `test-final` cũng vậy (0,8952 cả hai).

Không phải lỗi: phép sửa prior là **đơn điệu tăng**, nên khi ngưỡng đã được dò lại để đạt cùng một
FPR, ma trận nhầm lẫn thu được là một. Hai thao tác chỉ đơn giản là hai cách đi tới cùng một điểm
trên đường ROC.

**Hệ quả thực tiễn:** sửa prior bằng EM **chỉ** có giá trị khi **không** có nhãn để đặt ngưỡng.
Notebook 06 gộp "sửa prior + đặt lại ngưỡng" vào một cấu hình (`#3`, `#11`, `#12`) nên không thể
tách được hai thứ, và đã quy công cho EM phần công lao vốn thuộc về việc đặt lại ngưỡng.

---

## 8. CÁI GIÁ PHẢI TRẢ — sửa lỗi 8

Recall theo từng loại tấn công, **cùng `test-final`**, cho mọi cấu hình đáng chú ý:

| Loại | n | Baseline @0,5 | RF 31f @0,695 | EM prior @0,5 (không nhãn) | **Được chọn: RF 39f @0,731** |
|---|---|---|---|---|---|
| Exploits | 3.780 | 0,9870 | 0,9556 | 0,9849 | 0,9804 |
| **Fuzzers** | 2.218 | **0,8237** | **0,5496** | 0,7845 | **0,6244** |
| Reconnaissance | 1.131 | 0,9956 | 0,9788 | 0,9929 | 0,9920 |
| DoS | 839 | 0,9881 | 0,9511 | 0,9869 | 0,9845 |
| Generic | 715 | 0,9902 | 0,9776 | 0,9902 | 0,9902 |
| Analysis | 213 | 1,0000 | 0,9812 | 1,0000 | 0,9437 |
| Shellcode | 185 | 0,9514 | 0,8000 | 0,9243 | **0,9622** |
| Backdoor | 164 | 0,9939 | 0,9939 | 0,9939 | 0,9878 |
| Worms | 22 | 1,0000 | 0,9545 | 1,0000 | 1,0000 |
| **TỔNG Recall** | 9.267 | **0,9491** | 0,8607 | 0,9378 | **0,8967** |
| **TỔNG FPR** | 16.017 | 0,2569 | 0,1050 | 0,2309 | **0,1058** |

**Notebook 06 đã che mất bảng này.** Nó chỉ báo cáo Fuzzers 0,430 cho cấu hình thắng và gọi đó là
"điểm yếu duy nhất còn lại", không nói rằng ở ngưỡng 0,5 cùng loại model bắt được **0,824**. Người
đọc không thể thấy rằng Fuzzers tụt **là cái giá của việc đẩy ngưỡng lên**.

### So sánh trực tiếp với cấu hình "tốt nhất" của notebook 06

| | Ngưỡng | Accuracy | FPR | Recall tổng | **Recall Fuzzers** | FN |
|---|---|---|---|---|---|---|
| NB06 #12 (HGB 42f, ngưỡng max-Acc) | 0,8586 | **0,9050** | **0,0561** | 0,8376 | **0,4301** | 1.505 |
| **NB07 được chọn** (RF 39f, FPR ≤ 0,10) | 0,7311 | 0,8952 | 0,1058 | **0,8967** | **0,6244** | **957** |

Notebook 06 hơn **0,0098 accuracy**. Đổi lại, nó **bỏ sót thêm 548 cuộc tấn công** và
Recall Fuzzers **thấp hơn 0,1943**. Dưới bất kỳ yêu cầu vận hành nào của một hệ phát hiện xâm
nhập, **cấu hình của notebook 07 là lựa chọn đúng** — và nó là lựa chọn mà quy tắc khai báo trước
tự dẫn tới, không phải lựa chọn được chọn sau khi xem điểm.

**Đây vẫn là một quyết định đánh đổi, không phải một "cải thiện" đơn thuần.** Người quyết định
phải là người vận hành hệ thống, dựa trên chi phí một báo động giả so với chi phí một cuộc tấn công
bị bỏ sót. Notebook chỉ có nhiệm vụ đặt hai con số đó lên bàn.

---

## 9. PHÂN RÃ MỨC CẢI THIỆN — sửa lỗi 4

Toàn bộ là **accuracy trên `test-final`**, nên cộng lại đúng bằng tổng:

| Bước | Accuracy | Δ so với bước trước | % của tổng |
|---|---|---|---|
| 0. Baseline RF 31f @0,5 | 0,8186 | — | — |
| 1. Đổi sang RF 39 feature, vẫn @0,5 | 0,8345 | **+0,0159** | **20,8%** |
| 2. + sửa prior bằng EM, vẫn @0,5 | 0,8345 | **+0,0000** | **0,0%** |
| 3. + đặt lại ngưỡng = 0,7311 | **0,8952** | **+0,0606** | **79,2%** |
| **Tổng** | | **+0,0765** | 100% |

| Nguồn | Con số | Trạng thái |
|---|---|---|
| NB06 nói | 85% điểm vận hành / 15% model | ❌ chia ΔAccuracy cho ΔPR-AUC — hai đơn vị khác nhau |
| Bản rà soát tính lại trên 13 cấu hình của NB06 | 77,3% / 19,3% feature / 3,3% thuật toán | ✅ cùng đơn vị |
| **Notebook 07 đo trực tiếp** | **79,2% điểm vận hành / 20,8% feature / 0,0% prior** | ✅ cùng đơn vị, cộng đúng tổng |

Ba cách tính cho cùng một câu trả lời định tính: **khoảng 80% mức cải thiện là đặt lại điểm vận
hành, khoảng 20% là feature, và 0% là thuật toán hay phép sửa prior.**

Bằng chứng độc lập: **ΔPR-AUC chỉ +0,0113**, và toàn bộ +0,0113 đó đến từ 39 feature (xem Phần 5),
không từ thuật toán. Năng lực xếp hạng của model gần như không đổi.

---

## 10. KIỂM ĐỊNH — sửa lỗi 9

### Paired bootstrap 1.000 lần trên `test-final`

Nay **hợp lệ**, vì cấu hình được chọn trên `test-dev` chứ không phải trên tập đang kiểm định.

| Chỉ số | Trung bình | CI 95% | Khác 0? |
|---|---|---|---|
| Δ Accuracy | **+0,0765** | [+0,0718 ; +0,0808] | ✅ |
| Δ Balanced accuracy | **+0,0493** | [+0,0448 ; +0,0534] | ✅ |
| Δ PR-AUC | **+0,0113** | [+0,0093 ; +0,0134] | ✅ |
| Δ Recall | **−0,0523** | [−0,0582 ; −0,0462] | ✅ |
| Δ FPR | **−0,1510** | [−0,1572 ; −0,1448] | ✅ |

Đọc bảng: ΔAccuracy và ΔFPR rất mạnh, ΔPR-AUC nhỏ, ΔRecall **âm có ý nghĩa**. Đây là chữ ký
của một thay đổi **điểm vận hành**, không phải của một model mạnh hơn. Việc CI của ΔRecall nằm
hoàn toàn dưới 0 là thứ notebook 06 không bao giờ báo cáo.

### Độ bền theo seed

Cố định cách chia, chỉ đổi `random_state` của Random Forest (42, 7, 2024):

| | Biên độ |
|---|---|
| Accuracy @ngưỡng | **0,0006** |

Mức cải thiện (+0,0765) lớn hơn nhiễu seed khoảng **128 lần**. Kết luận bền.

---

## 11. BẢNG TỔNG — 42 cấu hình

`reports/rerun07/bang_cau_hinh.csv` chứa đủ 42 cấu hình = 7 thuật toán × 2 cách sửa prior ×
3 quy tắc ngưỡng, mỗi dòng 17 chỉ số, có cột `cần nhãn test?` để tách rõ hai nhóm.

Mỗi model được **fit một lần**; 42 cấu hình dùng lại xác suất đã lưu. Notebook 06 fit lại
21 lần cho 21 cấu hình.

**Hai dòng cần nhớ:**

| Mục đích | Cấu hình | Accuracy | Bal acc | Recall | FPR |
|---|---|---|---|---|---|
| Có mẫu có nhãn từ miền triển khai | RF 39f, ngưỡng từ test-dev (FPR ≤ 0,10) | 0,8952 | 0,8955 | 0,8967 | 0,1058 |
| **Không** có nhãn test | RF 39f + EM, ngưỡng từ validation | 0,8460 | 0,8704 | 0,9618 | 0,2210 |

---

## 12. TỔNG KẾT: NOTEBOOK 06 — CÁI GÌ ĐỨNG, CÁI GÌ ĐỔ

### Năm kết luận đứng vững

| Kết luận NB06 | Notebook 07 xác nhận |
|---|---|
| Không có lỗi cài đặt; baseline 0,8186 | ✅ tái lập 6 chữ số |
| Mức tụt sinh ra ở ranh giới train → test, không ở độ phức tạp model | ✅ và rõ hơn: ROC-AUC −0,0266 vs MCC −0,1984 |
| Lệch phân bố tập trung ở lớp Normal | ✅ 2,64× khi tính đúng (NB06 nói 2,85×) |
| EM sửa thiếu → lệch không phải prior shift thuần tuý | ✅ EM chỉ sửa 22% khoảng cần sửa |
| Đổi thuật toán không phải đòn bẩy trong các họ phù hợp | ✅ biên độ 0,0242 vs khoảng tụt 0,0428 |

### Bốn con số phải thay

| NB06 nói | Số đúng | Vì sao |
|---|---|---|
| "Cách chia lớn hơn bỏ feature **8,5 lần**" | **2,6–4,9 lần** tuỳ chỉ số | so Accuracy giữa các ô có π_test khác nhau tới 0,31 |
| "Bỏ khử trùng lặp **+0,0294**" | **−0,0027 PR-AUC** | đổi cả tập đánh giá; đo đúng cách thì ngược dấu |
| "**85% / 15%**" | **79,2% / 20,8% / 0,0%** | chia ΔAccuracy cho ΔPR-AUC |
| "Cấu hình tốt nhất **0,9050**, CI95 [+0,0812; +0,0914]" | **0,8952**, CI95 [+0,0718; +0,0808] | NB06 chọn cấu hình trên chính `test-final` |

### Ba phát hiện mới của notebook 07

1. **Sửa prior bằng EM là dư thừa khi đã có nhãn để đặt ngưỡng** — hai thao tác là hai đường tới
   cùng một điểm trên ROC. NB06 gộp chúng nên quy công sai.
2. **Cấu hình triển khai được mà không cần nhãn test**: RF 39f + EM + ngưỡng từ validation →
   balanced accuracy 0,8704 **và** Recall 0,9618, tốt hơn baseline ở cả hai. NB06 chỉ tìm được
   +1,5 điểm cho nhánh này.
3. **Dữ liệu chính thức vẫn còn 3,22% rò rỉ test → train** vì notebook 01 khử trùng lặp riêng
   trong từng tập, không khử chéo. Nhỏ, không đổi kết luận, nhưng nên nêu trước khi người khác
   phát hiện.

---

## 13. KHUYẾN NGHỊ

1. **Dùng cấu hình RF 39f @ngưỡng 0,7311 làm số báo cáo chính** (Accuracy 0,8952 · Balanced acc
   0,8955 · Recall 0,8967 · FPR 0,1058), và nêu rõ ngưỡng được chọn trên `test-dev` theo ràng buộc
   `FPR ≤ 0,10` khai báo trước. Đây đồng thời là cấu hình notebook 05 đã chọn — hai lần dò độc
   lập cùng đích.
2. **Bỏ con số 0,9050 của notebook 06 khỏi mọi tài liệu.** Nó được chọn trên tập báo cáo, và nó
   đánh đổi 548 cuộc tấn công bị bỏ sót để lấy 0,98 điểm accuracy.
3. **Giữ bộ chia chính thức, giữ bước khử trùng lặp.** Phần 4 xác nhận bằng phép đo sạch, trùng
   khít với `experiment_nodedup`.
4. **Báo cáo Balanced Accuracy, MCC và PR-AUC song song với Accuracy.** Trên tập mất cân bằng và
   lệch phân bố, Accuracy một mình gây hiểu nhầm — chính nó là lý do câu hỏi "vì sao accuracy thấp"
   xuất hiện.
5. **Mọi lần đổi điểm vận hành phải kèm bảng Recall theo loại tấn công.** Fuzzers là loại nhạy
   nhất với ngưỡng: từ 0,824 (@0,5) xuống 0,624 (@0,731) xuống 0,430 (@0,859).
6. **Sửa 4 con số trong `Bao_cao_truy_nguyen_accuracy.md`** và các chỗ tương ứng trong
   `Noi_dung_slide_thuyet_trinh.md`, theo bảng ở Phần 12.
7. **Khôi phục `data/raw/CSV Files/Training and Testing Sets/`** để đo lại thang đo đầy đủ 2×2×2.
   Đây là việc duy nhất còn thiếu.

---

## 14. ĐIỀU KHÔNG ĐƯỢC KẾT LUẬN TỪ NOTEBOOK NÀY

- **Không** kết luận được rằng RF 39 feature là cấu hình nên triển khai. Nó dùng 8 feature mà nhóm
  đã cố ý loại theo lập luận D'hooge et al. 2022, và xác suất của nó là xác suất **đã lưu** của
  notebook 05, không fit lại trong lần chạy này.
- **Không** kết luận được rằng `FPR ≤ 0,10` là ràng buộc đúng. Nó được kế thừa từ notebook 04/05
  để mọi lần chạy so được với nhau. Con số 0,10 cần người vận hành xác nhận.
- **Không** kết luận được rằng không thuật toán nào vượt được trần. Đã thử 7 cấu hình thuộc 6 họ,
  mỗi họ một cấu hình hợp lý, **không dò siêu tham số diện rộng**, và không có
  XGBoost/LightGBM/CatBoost trong môi trường.
- **Không** kết luận được rằng mọi phương pháp thích ứng miền đều vô dụng. Notebook 07 chỉ thử
  sửa prior bằng EM. Căn chỉnh phân vị đã bị notebook 06 loại (PR-AUC 0,9414 → 0,7736) nên không
  thử lại. Chưa thử: CORAL, học đối kháng theo miền, self-training trên test không nhãn.
- **Không** giải quyết được Fuzzers. Ở cấu hình được chọn, Recall Fuzzers là 0,6244 — tốt hơn
  notebook 06 (0,4301) nhưng vẫn là loại tấn công yếu nhất, và cải thiện đó chỉ đến từ việc chọn
  ngưỡng thấp hơn, không từ một cách xử lý Fuzzers nào.
- Thang đo ở Phần 3 chỉ là **2×2**. Yếu tố feature cần fit lại trên bể dữ liệu gộp, việc đó cần
  hai file CSV thô hiện không có.
