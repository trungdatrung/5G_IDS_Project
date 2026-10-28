# Ma trận nhầm lẫn & chỉ số đánh giá — dataset BỎ TRÙNG vs KHÔNG BỎ TRÙNG

**Dự án:** 5G IDS / UNSW-NB15, nhãn nhị phân `label` (0 = Normal, 1 = Attack)  
**Nguồn số:** `experiment_nodedup/reports/nodedup_results.csv` (chạy 02/10/2026) — không huấn luyện lại, chỉ tổng hợp kết quả đã lưu  
**Thuật toán:** giữ nguyên tuyệt đối ở cả hai nhánh (cùng RF, cùng tiền xử lý, cùng cách chia, seed 42). Biến duy nhất thay đổi là **bộ dữ liệu huấn luyện**.

## 1. Hai bộ dữ liệu

| | Bỏ trùng (chính thức) | Không bỏ trùng (V1) |
|---|---|---|
| Dòng train | 98.934 | 170.515 |
| Dòng test | 50.567 | 80.816 |
| Tỷ lệ Attack train | 0,4964 | 0,6807 |
| Tỷ lệ Attack test | 0,3665 | 0,5560 |
| Dòng trùng bị xoá (train) | 75.775 | 0 |
| Dòng mâu thuẫn bị xoá (train) | 632 | 4.826 |
| **Dòng test trùng khít với train** | **1.993 (3,94%)** | **20.960 (25,94%)** |

> Hàng cuối là điều quyết định cách đọc mọi con số phía dưới: bỏ bước khử trùng lặp làm tỷ lệ rò rỉ test→train tăng **6,6 lần**.

## 2. So sánh đối chứng — cùng tập đánh giá (test-final chính thức, 25.284 dòng)

Đây là phép so sánh **duy nhất trả lời được câu hỏi**: tập đánh giá giữ nguyên, nên khác biệt chỉ đến từ dữ liệu huấn luyện.

### 2.1  M1 - RF run1 (100 cây, không giới hạn độ sâu)

**M1 - RF run1 (100 cây, không giới hạn độ sâu) — train: Bỏ trùng (chính thức)**  
ngưỡng = 0,5000

| Thực \ Dự đoán | Normal | Attack | Tổng |
|---|---|---|---|
| **Normal** | TN = 11.737 | FP = 4.280 | 16.017 |
| **Attack** | FN = 465 | TP = 8.802 | 9.267 |

**M1 - RF run1 (100 cây, không giới hạn độ sâu) — train: Không bỏ trùng (V1)**  
ngưỡng = 0,5000

| Thực \ Dự đoán | Normal | Attack | Tổng |
|---|---|---|---|
| **Normal** | TN = 11.827 | FP = 4.190 | 16.017 |
| **Attack** | FN = 482 | TP = 8.785 | 9.267 |

| Chỉ số | Bỏ trùng (chính thức) | Không bỏ trùng (V1) | Hiệu |
|---|---|---|---|
| Accuracy | 0,8123 | 0,8152 | +0,0029 |
| Precision | 0,6728 | 0,6771 | +0,0042 |
| Recall (TPR) | 0,9498 | 0,9480 | −0,0018 |
| Specificity (TNR) | 0,7328 | 0,7384 | +0,0056 |
| F1 | 0,7877 | 0,7899 | +0,0023 |
| Balanced Accuracy | 0,8413 | 0,8432 | +0,0019 |
| FPR | 0,2672 | 0,2616 | −0,0056 |
| FNR | 0,0502 | 0,0520 | +0,0018 |
| NPV | 0,9619 | 0,9608 | −0,0010 |
| MCC | 0,6582 | 0,6617 | +0,0035 |
| PR-AUC | 0,9265 | 0,9240 | −0,0025 |
| ROC-AUC | 0,9547 | 0,9537 | −0,0010 |


### 2.2  M2 - RF run2 (300 cây, đã tinh chỉnh)

**M2 - RF run2 (300 cây, đã tinh chỉnh) — train: Bỏ trùng (chính thức)**  
ngưỡng = 0,5000

| Thực \ Dự đoán | Normal | Attack | Tổng |
|---|---|---|---|
| **Normal** | TN = 11.903 | FP = 4.114 | 16.017 |
| **Attack** | FN = 472 | TP = 8.795 | 9.267 |

**M2 - RF run2 (300 cây, đã tinh chỉnh) — train: Không bỏ trùng (V1)**  
ngưỡng = 0,5000

| Thực \ Dự đoán | Normal | Attack | Tổng |
|---|---|---|---|
| **Normal** | TN = 11.873 | FP = 4.144 | 16.017 |
| **Attack** | FN = 461 | TP = 8.806 | 9.267 |

| Chỉ số | Bỏ trùng (chính thức) | Không bỏ trùng (V1) | Hiệu |
|---|---|---|---|
| Accuracy | 0,8186 | 0,8179 | −0,0008 |
| Precision | 0,6813 | 0,6800 | −0,0013 |
| Recall (TPR) | 0,9491 | 0,9503 | +0,0012 |
| Specificity (TNR) | 0,7431 | 0,7413 | −0,0019 |
| F1 | 0,7932 | 0,7927 | −0,0005 |
| Balanced Accuracy | 0,8461 | 0,8458 | −0,0003 |
| FPR | 0,2569 | 0,2587 | +0,0019 |
| FNR | 0,0509 | 0,0497 | −0,0012 |
| NPV | 0,9619 | 0,9626 | +0,0008 |
| MCC | 0,6672 | 0,6666 | −0,0006 |
| PR-AUC | 0,9414 | 0,9387 | −0,0027 |
| ROC-AUC | 0,9594 | 0,9584 | −0,0010 |


### 2.3  M3 - RF run3 (calibrated + ngưỡng theo FPR<=0,10)

**M3 - RF run3 (calibrated + ngưỡng theo FPR<=0,10) — train: Bỏ trùng (chính thức)**  
ngưỡng = 0,7105

| Thực \ Dự đoán | Normal | Attack | Tổng |
|---|---|---|---|
| **Normal** | TN = 14.344 | FP = 1.673 | 16.017 |
| **Attack** | FN = 1.300 | TP = 7.967 | 9.267 |

**M3 - RF run3 (calibrated + ngưỡng theo FPR<=0,10) — train: Không bỏ trùng (V1)**  
ngưỡng = 0,7636

| Thực \ Dự đoán | Normal | Attack | Tổng |
|---|---|---|---|
| **Normal** | TN = 14.459 | FP = 1.558 | 16.017 |
| **Attack** | FN = 1.408 | TP = 7.859 | 9.267 |

| Chỉ số | Bỏ trùng (chính thức) | Không bỏ trùng (V1) | Hiệu |
|---|---|---|---|
| Accuracy | 0,8824 | 0,8827 | +0,0003 |
| Precision | 0,8265 | 0,8346 | +0,0081 |
| Recall (TPR) | 0,8597 | 0,8481 | −0,0117 |
| Specificity (TNR) | 0,8955 | 0,9027 | +0,0072 |
| F1 | 0,8428 | 0,8413 | −0,0015 |
| Balanced Accuracy | 0,8776 | 0,8754 | −0,0022 |
| FPR | 0,1045 | 0,0973 | −0,0072 |
| FNR | 0,1403 | 0,1519 | +0,0117 |
| NPV | 0,9169 | 0,9113 | −0,0056 |
| MCC | 0,7493 | 0,7483 | −0,0010 |
| PR-AUC | 0,9418 | 0,9395 | −0,0024 |
| ROC-AUC | 0,9596 | 0,9586 | −0,0010 |


**Kiểm định ý nghĩa thống kê** (paired bootstrap 1.000 lần, hiệu = không bỏ trùng − bỏ trùng; nguồn: `experiment_nodedup/reports/Bao_cao_nodedup.txt` §5.1):

| Giai đoạn | Δ PR-AUC | CI 95% | p | Kết luận |
|---|---|---|---|---|
| M1 | −0,00243 | [−0,00454; −0,00033] | 0,026 | Có ý nghĩa — kém hơn |
| M2 | −0,00271 | [−0,00374; −0,00167] | 0,000 | Có ý nghĩa — kém hơn |

## 3. Đánh giá "native" trên tập test KHÔNG bỏ trùng (40.408 dòng)

Con số một nhóm sẽ **nhận được** nếu họ bỏ qua bước khử trùng lặp ở cả train và test. 25,94% dòng của tập test này là bản sao chính xác của dòng train.

**M1 - RF run1 (100 cây, không giới hạn độ sâu) — train: Không bỏ trùng (V1)**  
ngưỡng = 0,5000

| Thực \ Dự đoán | Normal | Attack | Tổng |
|---|---|---|---|
| **Normal** | TN = 13.175 | FP = 4.765 | 17.940 |
| **Attack** | FN = 526 | TP = 21.942 | 22.468 |

**M2 - RF run2 (300 cây, đã tinh chỉnh) — train: Không bỏ trùng (V1)**  
ngưỡng = 0,5000

| Thực \ Dự đoán | Normal | Attack | Tổng |
|---|---|---|---|
| **Normal** | TN = 13.217 | FP = 4.723 | 17.940 |
| **Attack** | FN = 520 | TP = 21.948 | 22.468 |

**M3 - RF run3 (calibrated + ngưỡng theo FPR<=0,10) — train: Không bỏ trùng (V1)**  
ngưỡng = 0,7636

| Thực \ Dự đoán | Normal | Attack | Tổng |
|---|---|---|---|
| **Normal** | TN = 16.094 | FP = 1.846 | 17.940 |
| **Attack** | FN = 1.540 | TP = 20.928 | 22.468 |

| Chỉ số | M1 | M2 | M3 |
|---|---|---|---|
| Accuracy | 0,8691 | 0,8702 | 0,9162 |
| Precision | 0,8216 | 0,8229 | 0,9189 |
| Recall | 0,9766 | 0,9769 | 0,9315 |
| Specificity | 0,7344 | 0,7367 | 0,8971 |
| F1 | 0,8924 | 0,8933 | 0,9252 |
| FPR | 0,2656 | 0,2633 | 0,1029 |
| MCC | 0,7462 | 0,7485 | 0,8301 |
| PR-AUC | 0,9789 | 0,9846 | 0,9851 |
| ROC-AUC | 0,9757 | 0,9794 | 0,9796 |

So với mục 2, PR-AUC cao hơn **0,045–0,046**. Nhìn như một bước nhảy lớn, nhưng đây là **số ảo**: model không cần tổng quát hoá, nó chỉ cần nhớ lại dòng đã thấy trong train (data snooping qua đường trùng lặp — Arp et al., pitfall P1/P3).

## 4. Kết luận

1. Trên cùng tập đánh giá trung thực, huấn luyện bằng dữ liệu **không bỏ trùng cho kết quả kém hơn** ~0,0025 PR-AUC ở cả ba giai đoạn — nhỏ nhưng có ý nghĩa thống kê.
2. Nhân đôi dữ liệu train (79.147 → 136.412 dòng fit) **không giúp gì**, vì phần thêm vào chỉ là bản lặp, không mang thông tin mới. Số lần lặp chỉ đóng vai trò trọng số mẫu ngầm.
3. Chỉ số cao trên tập test không bỏ trùng (PR-AUC ~0,985, Accuracy ~0,87–0,92) **không được báo cáo** như hiệu năng thật.
4. **Bước khử trùng lặp là đúng và nên giữ.**

## 5. File đi kèm

| File | Nội dung |
|---|---|
| `chi_so_va_ma_tran_nham_lan.csv` | Toàn bộ 16 dòng kết quả: TN/FP/FN/TP + 14 chỉ số |
| `confusion_doi_chung.png` | Ma trận nhầm lẫn M1/M2/M3 × 2 bộ train, cùng tập đánh giá |
| `confusion_native_nodedup.png` | Ma trận nhầm lẫn khi đánh giá native trên test không bỏ trùng |

*Mọi chỉ số trong CSV được tính lại từ TN/FP/FN/TP và đã đối chiếu trùng khít (lệch < 1e-6) với chỉ số lưu trong file gốc.*