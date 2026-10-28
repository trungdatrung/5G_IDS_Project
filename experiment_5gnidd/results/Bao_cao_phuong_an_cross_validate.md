# Chọn phương án cross-validate UNSW-NB15 ↔ 5G-NIDD

**Ngày:** 27/10/2026 · **Thư mục:** `experiment_5gnidd/` (không file nào ngoài thư mục này bị ghi)
**Mô hình:** RF của NB07 (300 cây, max_depth 20, max_features 0,5, max_samples 0,7, seed 42), OneHot cho `proto`/`service`/`state`.
**Ngưỡng vận hành:** luôn chọn trên validation của **miền nguồn** (FPR ≤ 0,10), không nhìn nhãn miền đích.

| Bước | Lệnh | Ra |
|---|---|---|
| 1. Ánh xạ + làm sạch | `python -I -X utf8 experiment_5gnidd/src/01_lam_sach_5gnidd.py <dự án>` | `data/cleaned/5gnidd_unsw31*.parquet`, `results/01_thong_ke_lam_sach.json` |
| 2. E1–E4 | `python -I -X utf8 experiment_5gnidd/src/02_train_danh_gia.py <dự án>` | `results/02_ket_qua.json`, `tong_hop_*.csv`, `figures/` |
| 3. So sánh phương án | `python -I -X utf8 experiment_5gnidd/src/03_phuong_an_cross_validate.py <dự án>` | `results/03_tat_ca_phuong_an.csv`, `03_few_shot_tong_hop.csv`, `03_ket_qua.json` |

---

## 0. TÓM TẮT

| | |
|---|---|
| **Dữ liệu** | 5G-NIDD bản Fairdata (CC BY 4.0). Hash SHA-256 khớp bản đã kiểm ngày 26/10 (`625F4D178C8A`, `01E6C4669E64`, `6C420140E7DC`). 1.215.890 flow thô → **379.556** flow sau khi bỏ 281.529 bản sao bắt nhầm (nhãn sai), 554.789 dòng trùng lặp và 16 dòng mâu thuẫn nhãn. |
| **Ánh xạ** | Đủ 31 feature của model, đúng tên và đơn vị UNSW (bảng ánh xạ chi tiết: `reports/5gnidd/Bao_cao_doi_chieu_5G-NIDD.md` §3). Model gốc tái lập đúng NB07: accuracy UNSW test-final = 0,81862. |
| **Zero-shot (model hiện tại → 5G)** | **Không khả thi.** ROC-AUC 0,21–0,40 với mọi bộ feature và mọi cách căn nhãn. Chiều ngược (5G → UNSW) cho 0,45–0,55. |
| **Phương án khả thi nhất** | **P3 — train gộp UNSW + 5G trạm BS1, kiểm tra trên trạm BS2 (giữ riêng hoàn toàn) và trên UNSW test-final**, dùng bộ **LOI18** (18 feature ổn định, không có shortcut). Kết quả: BS2 ROC-AUC **0,998**, UNSW test-final **0,955** (gốc 0,957). Một model phục vụ cả hai miền mà không làm hỏng UNSW. |
| **Cần nói rõ khi báo cáo** | (1) BS2 dễ: cùng công cụ tấn công, cùng server nạn nhân với BS1, nên 0,998 là mức lạc quan. (2) Dữ liệu UNSW **không giúp** thêm gì cho 5G: P3 ≈ P5 (chỉ dùng 5G). Few-shot với rất ít nhãn còn bị chuyển giao âm. (3) Không có chuyển giao tri thức thật giữa hai bộ. |

---

## 1. BA TRỤC SO SÁNH

**Bộ feature**

| Tên | Feature | Lý do |
|---|---|---|
| F31 | 31 feature của model hiện tại | Mốc |
| **LOI12** | `dur, proto, state, spkts, dpkts, sbytes, dbytes, rate, sload, dload, smean, dmean` | Lấy chính xác hoặc theo công thức Argus đã kiểm khớp 99,6–100% ở cả hai bộ |
| **LOI18** | LOI12 + `sinpkt, dinpkt, sjit, djit, sloss, dloss` | Thêm 6 feature xấp xỉ (Spearman 0,84–0,98 trong round-trip) |

Loại khỏi LOI vì là "dấu vân tay" môi trường hoặc shortcut:
- `ackdat`/`synack`/`tcprtt`: đo độ trễ mạng chứ không đo tấn công.
- `stcpb`/`dtcpb`: số thứ tự TCP ngẫu nhiên.
- `swin`/`dwin`: gần như hằng số.
- 4 feature Bro (`service`, `trans_depth`, `ct_flw_http_mthd`, `response_body_len`): chỉ suy được từ cổng.
- `ct_src_ltm`/`ct_src_dport_ltm`: đếm theo thứ tự dòng. Trong E1, hai feature này chiếm **58% importance** của RF train trên 5G. Đây là shortcut "nguồn đang flood thì 99/100 bản ghi gần nhất đều từ nó".

**Căn nhãn:**
- ALL: giữ mọi họ tấn công UNSW.
- **DR**: UNSW chỉ giữ Normal + DoS + Reconnaissance, cùng họ với tấn công trong 5G-NIDD (DoS và scan).

**Giao thức:**

| Mã | Train | Test |
|---|---|---|
| P1 | UNSW | 5G (toàn bộ và BS2), zero-shot |
| P2 | 5G-BS1 | UNSW test-final (chiều ngược) |
| P3 | UNSW + 5G-BS1 | BS2 **và** UNSW test-final |
| P4 | k% nhãn BS1 (có / không kèm UNSW-DR), 3 seed | BS2 |
| P5 | 5G-BS1 | BS2 (mức trần trong miền) |

---

## 2. KẾT QUẢ (ROC-AUC; Bal acc / FPR ở ngưỡng chọn trên miền nguồn)

| Giao thức | Feature | Nhãn | → 5G BS2 | → UNSW test-final* |
|---|---|---|---|---|
| P1 zero-shot | F31 | ALL | **0,354** (0,33 / 0,46) | 0,959 (mốc) |
| P1 zero-shot | LOI12 | ALL | 0,277 | 0,957 |
| P1 zero-shot | LOI18 | DR | 0,282 (0,37 / **0,96**) | 0,993 |
| P2 ngược | F31 / LOI12 / LOI18 | ALL | — | 0,454 / 0,483 / 0,477 |
| P2 ngược | LOI18 | DR | — | 0,549 |
| P5 trong miền | F31 / LOI12 / LOI18 | — | 0,999 / 0,998 / 0,998 | — |
| **P3 gộp** | **LOI18** | **ALL** | **0,998** (0,974 / 0,049) | **0,955** (0,872 / 0,122) |
| P3 gộp | LOI18 | DR | 0,997 (0,945 / 0,111) | 0,993 (0,941 / 0,107) |
| P3 gộp | F31 | ALL | 0,999 (0,984 / 0,028) | 0,958 (0,869 / 0,155) |

\* Với DR thì đây là UNSW test-final đã lọc DR (17.987 dòng, π = 0,11).

**Few-shot P4** (LOI18, BS2, trung bình 3 seed):

| Số nhãn 5G (k% BS1) | Chỉ 5G: ROC-AUC | UNSW-DR + 5G: ROC-AUC | UNSW-DR + 5G: FPR @ngưỡng nguồn |
|---|---|---|---|
| 168 (0,1%) | **0,965** ± 0,017 | 0,943 ± 0,012 | **0,80** |
| 1.664 (1%) | 0,991 | 0,989 | 0,38 |
| 8.322 (5%) | 0,994 | 0,995 | 0,24 |
| 33.283 (20%) | 0,997 | 0,997 | 0,15 |

Khi gộp, UNSW test-final DR giữ nguyên 0,993 ở mọi mức k.

**Recall theo loại tấn công trên BS2, ngưỡng nguồn:**
- P3 (LOI18, DR): mọi loại tấn công đạt 0,9997–1,0; FPR Benign 0,11.
- P1 zero-shot (LOI18, DR): UDPFlood 0,003, SYNScan 0,013, SYNFlood 0,20; FPR Benign 0,96.

---

## 3. ĐỌC KẾT QUẢ

1. **Zero-shot hỏng ở mọi biến thể, và bỏ shortcut còn làm tệ hơn** (F31 0,35 → LOI12 0,28). Sau khi bỏ `ackdat` và các feature liên quan, model chỉ còn dựa vào kích thước và tốc độ gói. Trên trục này, khái niệm "tấn công" của hai bộ **ngược nhau**: tấn công UNSW có payload, còn flood/scan 5G là gói trần. Căn nhãn về DoS + Recon cũng không cứu được.
2. **Chiều ngược cũng thất bại** (≈ 0,5). Đúng với nhận xét của Layeghy & Portmann về tính bất đối xứng, nhưng ở đây cả hai chiều đều hỏng.
3. **Train gộp là cách duy nhất cho kết quả tốt ở cả hai miền.** Thêm 166 nghìn flow 5G không làm giảm UNSW (0,957 → 0,955). Model đủ sức học hai "khái niệm tấn công" song song.
4. **Nhưng UNSW không đóng góp gì cho 5G.** P3 ≈ P5. Với 168 nhãn 5G, có UNSW còn **kém hơn** (0,943 so với 0,965). Ngưỡng chọn trên validation gộp cũng lệch theo UNSW nên FPR trên 5G lên 0,80. → Khi ít nhãn 5G, ngưỡng **phải** chọn trên phần nhãn 5G, không dùng validation gộp.
5. **Các con số ≈ 0,998 trên BS2 không có nghĩa là bài toán 5G đã được giải.** BS1 và BS2 dùng cùng hping3/nmap/slowloris và cùng nhắm vào một server. Chia theo trạm chỉ là chia theo vị trí bắt gói, không phải theo loại tấn công mới.

---

## 4. KHUYẾN NGHỊ

**Phương án chuẩn để báo cáo cross-validate** (theo thứ tự trình bày):

1. **P1 — zero-shot, dùng làm kết quả âm.** Áp model F31 hiện tại lên 5G: ROC-AUC 0,40. Đây là con số trả lời câu hỏi "model UNSW có dùng được trên 5G không".
2. **P3 — train gộp UNSW + BS1 với LOI18; test BS2 và UNSW test-final.** Đây là phương án chính. Báo cáo **cả hai miền** cạnh nhau, chia theo trạm chứ không chia ngẫu nhiên, ngưỡng chọn trên validation nguồn.
3. **P4 — đường cong few-shot**, cho câu hỏi "cần bao nhiêu nhãn 5G": 1.664 nhãn (1%) là đủ đạt ROC-AUC 0,99.
4. **P5 làm mức trần**, để thấy rõ phần UNSW không đóng góp gì.

Chọn **LOI18** thay vì F31: chỉ thua 0,001–0,002 ROC-AUC, nhưng loại được shortcut `ct_*`, độ trễ mạng và các feature Bro không đo được trên 5G. Kết quả nhờ vậy giải thích được và dùng lại được với dữ liệu khác.

**Bước tiếp theo nên làm** để kiểm tra tổng quát hoá thật trong 5G: chạy **leave-one-attack-out** (giữ lại hẳn một loại tấn công, ví dụ SYNScan hoặc SlowrateDoS, khi train). Chia theo trạm không trả lời được câu hỏi này.
