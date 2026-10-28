# Kế hoạch validate chéo trên 5G-NIDD — khả thi và khả năng phát hiện

> **Cập nhật 26/10/2026:** đã tải dữ liệu thật và chạy cross-validate. Xem `Bao_cao_doi_chieu_5G-NIDD.md`.
> Một số điểm trong bản kế hoạch này đã được dữ liệu thật **sửa lại**:
> - `SIntPkt`/jitter rỗng 100%, nên chúng không nằm ở nhóm "có trong CSV".
> - `swin` của UNSW chỉ nhận 0/255.
> - Dự báo "flood và scan bị bắt tốt", cũng như ROC-AUC zero-shot 0,70–0,90, là **sai**. Kết quả thật là ROC-AUC 0,40, và flood/scan bị bỏ sót.

**Dự án:** 5G IDS · model RF 31 feature huấn luyện trên UNSW-NB15 (pipeline `reports/exp05/rf_A_trainfit.joblib`)
**Ngày:** 26/10/2026
**Bộ dữ liệu đích:** 5G-NIDD (Samarakoon et al., Đại học Oulu, 5GTN) — IEEE DataPort `10203`
**Số liệu gốc:** `reports/5gnidd/stress_test_5g.py` → `stress_test_5g_ket_qua.json`
(chạy lại được: `python stress_test_5g.py <thư mục dự án>`; model được kiểm tra khớp NB07, accuracy test-final = 0,81862)

---

## 0. TÓM TẮT

| Câu hỏi | Trả lời |
|---|---|
| **Khả thi về dữ liệu?** | **Có.** 5G-NIDD dùng **Argus**, cùng công cụ đã sinh UNSW-NB15. 21/31 feature của model ánh xạ trực tiếp, chiếm **87,5%** tổng permutation importance. 3 feature Bro bị thiếu chỉ chiếm **0,7%**. |
| **Đem model hiện tại sang dùng luôn được không (zero-shot)?** | **Có thể chạy, nhưng dự kiến không dùng được để vận hành.** Feature quan trọng nhất của model là `ackdat`, và ở UNSW nó là một **shortcut theo độ trễ mạng**: 99,6% flow TCP tấn công có `ackdat ≥ 10 ms`, so với chỉ 24,7% flow Normal. Trên mạng 5G gần như **mọi** flow TCP lành tính đều có độ trễ vô tuyến ≥ 10 ms. |
| **Dự đoán định lượng** | Stress test mô phỏng 5G trên UNSW: FPR @0,5 tăng **25,7% → 37,6–40,7%**. FPR trên các flow Normal có bắt tay TCP tăng **28,2% → 43,3–47,2%**. ROC-AUC giảm **0,959 → 0,911–0,922**. Recall gần như giữ nguyên ở **~0,95**. Model **vẫn bắt được tấn công nhưng báo động giả rất nhiều**. |
| **Đâu là con số đáng báo cáo?** | Nên báo cáo **ba con số tách biệt**: (1) zero-shot, (2) có hiệu chỉnh ngưỡng bằng một ít nhãn 5G, (3) huấn luyện trong miền 5G với chia theo trạm gốc. **Không** dùng cách chia ngẫu nhiên 70/30 như bài báo gốc (99,9%), vì cách đó có cả rò rỉ lẫn feature ô nhiễm (§4). |

---

## 1. 5G-NIDD — những gì đã xác minh từ bài báo gốc (arXiv 2212.01298)

| Mục | Giá trị |
|---|---|
| Hạ tầng | 5GTN Oulu, NSA option 3a, 2 pico base station (BS1, BS2), nạn nhân là server Ubuntu trong MEC |
| Điểm bắt gói | Giao diện S1-U của base station → có lớp GTP-U, đã bóc bằng Tracewrangler |
| Sinh flow | **Argus**, 112 feature → CSV. Có các tệp `BTS_1.csv`, `BTS_2.csv`, `Combined.csv`, `Encoded.csv` |
| Lưu lượng lành tính | Điện thoại thật (Moto g50 5G): HTTP/HTTPS (streaming, web), SSH, SFTP |
| Tổng | **1.215.890 flow**: 477.737 Benign (39,3%) và 738.153 Attack (60,7%) |

| Loại tấn công | Công cụ | Số flow | % Attack | Tương đương gần nhất trong UNSW |
|---|---|---|---|---|
| UDP Flood | hping3 `--rand-source` | 457.340 | 62,0% | DoS (không sát) |
| HTTP Flood | GoldenEye | 140.812 | 19,1% | DoS / Exploits (không sát) |
| Slowrate DoS | Slowloris, Torshammer | 73.124 | 9,9% | **không có** |
| TCP Connect Scan | nmap `-sT` | 20.052 | 2,7% | Reconnaissance |
| SYN Scan | nmap `-sS` | 20.043 | 2,7% | Reconnaissance |
| UDP Scan | nmap `-sU` | 15.906 | 2,2% | Reconnaissance |
| SYN Flood | hping3 `--rand-source` | 9.721 | 1,3% | DoS |
| ICMP Flood | hping3 `--rand-source` | 1.155 | 0,2% | DoS |

Khác biệt cấu trúc giữa hai bộ dữ liệu:
- **5G-NIDD chỉ có DoS và scan.** Không có Exploits, Fuzzers, Backdoor, Shellcode, Worms, Generic hay Analysis. Phép kiểm này đo được khả năng **tổng quát hoá miền mạng** cho hai họ tấn công, chứ không đo được toàn bộ năng lực của model.
- **Truy cập:** tệp trên IEEE DataPort cần đăng nhập và subscription. Bản sao trên Fairdata (`etsin.fairdata.fi/dataset/9d13ef28-2ca7-44b0-9950-225359afac65`) cần nhóm tự kiểm tra quyền truy cập. Chỉ cần tải `Combined.zip` (26,7 MB). Nếu muốn tính lại các feature Bro thì tải thêm pcap đã bóc GTP (BS1 2,17 GB + BS2 1,43 GB).

---

## 2. TÍNH KHẢ THI — ánh xạ 31 feature

Trọng số lấy theo permutation importance của model 31 feature (`models/random_forest_v2_importance.csv`).

| Nhóm | Feature UNSW → trường Argus 5G-NIDD | Số feature | % importance |
|---|---|---|---|
| **A. Trực tiếp** | dur→Dur, proto→Proto, state→State, spkts/dpkts→SrcPkts/DstPkts, sbytes/dbytes→SrcBytes/DstBytes, rate→Rate, sload/dload→SrcLoad/DstLoad, sloss/dloss→SrcLoss/DstLoss, swin/dwin→SrcWin/DstWin, stcpb/dtcpb→SrcTCPBase/DstTCPBase, tcprtt/synack/ackdat→TcpRtt/SynAck/AckDat, smean/dmean→sMeanPktSz/dMeanPktSz | 21 | **87,5%** |
| **B. Có trong Argus, phải xác minh có trong CSV** | sinpkt/dinpkt→SIntPkt/DIntPkt, sjit/djit→SrcJitter/DstJitter | 4 | 4,1% |
| **C. Tính lại được** | service ← suy từ Dport (80→http, 22→ssh, 53→dns, còn lại `-`); ct_src_ltm, ct_src_dport_ltm ← cửa sổ 100 kết nối theo StartTime, SrcAddr, Dport | 3 | 7,6% |
| **D. Thiếu (Bro/Zeek)** | trans_depth, response_body_len, ct_flw_http_mthd → gán 0, hoặc chạy Zeek trên pcap | 3 | 0,7% |

**Kết luận:** về mặt kỹ thuật, có thể chạy được ≥ 99% trọng số của model. Rủi ro **không** nằm ở chỗ thiếu feature mà ở **ngữ nghĩa** của feature:

1. **Đơn vị.** Argus cho phép cấu hình đơn vị (ms hay s, bit/s hay byte/s). Phải đối chiếu khoảng giá trị của `Dur`, `SIntPkt`, `Load` với UNSW trước khi đưa vào model. Không có hai CSV thô của UNSW (đã ghi ở NB07 §13.7), nên chỉ đối chiếu được qua phân bố.
2. **`ct_src_*` gần như vô nghĩa với hping3 `--rand-source`.** Mỗi gói mang một IP nguồn ngẫu nhiên, nên `ct_src_ltm` ≈ 1 với mọi flow flood. Hành vi này chưa từng xuất hiện trong UNSW.
3. **`stcpb`/`dtcpb` là số thứ tự ban đầu ngẫu nhiên.** Chúng không mang tín hiệu thật, nên bỏ trong mọi thí nghiệm mới.
4. **Model 39 feature (cấu hình chọn của NB05/NB07) không dùng được cho 5G-NIDD.** Nó cần `sttl`/`dttl`/`ct_state_ttl`. Đó là các feature ô nhiễm (D'hooge et al. 2022), và trong 5G-NIDD `sTtl` đứng **thứ 3** theo ANOVA. Ngoài ra không fit lại được vì thiếu CSV thô. → **Chỉ dùng RF 31 feature.**

---

## 3. KHẢ NĂNG PHÁT HIỆN — stress test trước khi có dữ liệu

### 3.1 Shortcut theo độ trễ

Trên `UNSW_NB15_training-set`, chỉ xét flow TCP có bắt tay (`ackdat > 0`):

| | Trung vị `ackdat` | q90 | Tỷ lệ `ackdat ≥ 10 ms` |
|---|---|---|---|
| Normal | **0,14 ms** | 75 ms | **24,7%** |
| Attack | **60,6 ms** | 109 ms | **99,6%** |

Trong UNSW, "độ trễ bắt tay lớn" gần như đồng nghĩa với "tấn công". Điều này khớp với NB07: `ackdat` đứng thứ nhất về permutation importance và lệch phân bố nhiều nhất (KS Normal 0,27).

Ở 5G-NIDD, đầu dò đặt ở S1-U, giữa UE và core/MEC:
- `synack` là chặng đầu dò → MEC, ngắn.
- `ackdat` là chặng đầu dò → **UE qua sóng vô tuyến** → đầu dò. Với 5G NSA, chặng này thường vào khoảng chục đến vài chục ms.

Như vậy mọi phiên HTTPS hay SSH lành tính từ điện thoại đều sẽ có `ackdat` nằm trong vùng "Attack" của UNSW.

### 3.2 Mô phỏng trên UNSW `test-final` (25.284 dòng)

Các kịch bản: (1) gán 0 cho ba feature Bro và `service='-'`; (2) cộng độ trễ vô tuyến U(10, 40) ms vào `ackdat` và `dur`, U(1, 5) ms vào `synack`, rồi tính lại `tcprtt`; (3) gộp (1) và (2); (4) như (3) nhưng trễ U(30, 80) ms. Hai ngưỡng: 0,5 và 0,6949 (ngưỡng RF 31f chọn trên test-dev với ràng buộc FPR ≤ 0,10 ở NB07).

| Kịch bản | ROC-AUC | FPR @0,5 | Recall @0,5 | Bal acc @0,5 | FPR @0,695 | Recall @0,695 | FPR Normal-TCP @0,5 |
|---|---|---|---|---|---|---|---|
| 0. Gốc | 0,9594 | 0,2569 | 0,9491 | 0,8461 | 0,1050 | 0,8607 | 0,2817 |
| 1. Thiếu Bro | 0,9433 | 0,2799 | 0,9452 | 0,8326 | 0,1399 | 0,8354 | 0,3110 |
| 2. Trễ 5G 10–40 ms | 0,9432 | 0,3499 | 0,9490 | 0,7995 | 0,1289 | 0,8554 | 0,4001 |
| **3. Thiếu Bro + trễ 10–40 ms** | **0,9223** | **0,3756** | 0,9455 | **0,7850** | **0,1707** | 0,8252 | **0,4327** |
| 4. Thiếu Bro + trễ 30–80 ms | 0,9108 | 0,4066 | 0,9479 | 0,7706 | 0,1948 | 0,8143 | 0,4721 |

Recall theo loại ở kịch bản 3 so với gốc, @0,695: Reconnaissance 0,979 → 0,899 · DoS 0,951 → 0,936 · Generic 0,978 → 0,973.

**Cách đọc:**
- Chỉ **hai** khác biệt đã biết chắc (thiếu Bro, độ trễ vô tuyến) đã đẩy FPR từ 25,7% lên 37,6%. Recall gần như không đổi. Đây đúng là dạng hỏng mà NB07 đã thấy (lệch tập trung ở lớp Normal), chỉ nặng hơn.
- Đây là **chặn dưới** của mức hỏng. Mô phỏng chưa gồm những khác biệt khác: lưu lượng lành tính là streaming và SSH thật, MTU và kích thước gói sau khi bóc GTP, cửa sổ TCP của Android, và IP nguồn ngẫu nhiên.

### 3.3 Flow ngắn — dấu vân tay của hping3 và nmap

Trên UNSW `test-final`, model xử lý flow ngắn (`spkts ≤ 2`, `dpkts ≤ 1`) như sau:

| | n | Tỷ lệ bị gán Attack @0,5 |
|---|---|---|
| Attack ngắn (chủ yếu `udp/INT`) | 2.041 | **97,2%** |
| Normal ngắn (chủ yếu `udp/INT`, `arp`, `tcp/REQ`) | 952 | **56,9%** |

Model gần như coi mọi flow UDP một chiều, ngắn là tấn công. Với 5G-NIDD điều đó có nghĩa là:
- **UDP Flood, ICMP Flood, SYN Flood, các loại scan** (≈ 71% số flow tấn công) **dự kiến bị bắt tốt.**
- Nhưng lưu lượng UDP lành tính của điện thoại (DNS, QUIC/HTTP3 của dịch vụ streaming) cũng sẽ bị gán Attack. Đây là một nguồn FP thứ hai, độc lập với `ackdat`.

### 3.4 Dự báo trên 5G-NIDD theo loại (zero-shot, RF 31f)

| Loại | % flow | Dự báo Recall | Lý do |
|---|---|---|---|
| UDP Flood | 37,6% | **Cao (≥ 0,9)** | Flow `udp/INT` ngắn, model bắt 97% loại flow này ở UNSW |
| SYN/TCP Connect/UDP Scan | 4,6% | **Cao (0,85–0,98)** | Tương ứng Reconnaissance (0,98 → 0,90 dưới stress) |
| SYN Flood, ICMP Flood | 0,9% | Khá–cao | Flow một chiều, không bắt tay; `proto=icmp` hiếm trong UNSW nên có rủi ro |
| HTTP Flood, Slowrate DoS | 17,6% | **Có thể cao, nhưng vì sai lý do** | Phiên TCP hoàn chỉnh qua 5G nên `ackdat` lớn. Model sẽ gán chúng giống hệt cách gán HTTPS lành tính, tức không phân biệt được |
| **Benign** | 39,3% | **FPR dự kiến 40–60%** | `ackdat` vô tuyến cộng UDP/QUIC ngắn |

**Phép tính minh hoạ** (giả định Recall 0,90 và FPR 0,45, π = 0,607):
Precision = 0,90·738.153 / (0,90·738.153 + 0,45·477.737) = **0,755** · Accuracy = **0,762** · **Balanced acc = 0,725**.
Accuracy 0,76 nghe chấp nhận được chỉ vì 61% số flow là tấn công. Balanced accuracy và FPR mới là con số thật. Cần nhắc lại bài học NB07: **không báo cáo Accuracy một mình.**

---

## 4. CẠM BẪY CỦA CHÍNH 5G-NIDD — phải xử lý trước khi đo

| # | Vấn đề | Bằng chứng | Xử lý |
|---|---|---|---|
| T1 | **Feature metadata đứng đầu bảng ANOVA:** `Seq` (329.589) và `Offset` (223.792) | Đây là số thứ tự bản ghi và offset trong tệp Argus, tức vị trí trong file, không phải hành vi mạng. Các phiên tấn công được bắt theo lịch riêng (Bảng III, IV của bài báo) | **Bỏ**, cùng với `StartTime`, `LastTime`, `SrcAddr`, `DstAddr`, `Sport`, `Dport`, `SrcId`, `Rank` |
| T2 | **TTL / Hops:** `sTtl` hạng 3, `sHops` hạng 13, `dTtl` hạng 15 | Kẻ tấn công là Raspberry Pi riêng → TTL mã hoá luôn danh tính máy. Đúng loại ô nhiễm D'hooge 2022 | Bỏ `sTtl`, `dTtl`, `sHops`, `dHops`. Riêng thí nghiệm E6 sẽ đo xem chúng làm điểm tăng thêm bao nhiêu |
| T3 | **Trùng lặp khổng lồ** | hping3 `--flood` sinh hàng trăm nghìn flow gần như giống nhau (UDP Flood 457k) | Khử trùng lặp như NB01, **và khử chéo** giữa train và test (NB07 phát hiện còn 3,22% rò rỉ do chỉ khử trong từng tập). Báo cáo n trước và sau khử |
| T4 | **Chia ngẫu nhiên 70/30** (cách của bài báo, ra 99,9%) | Rò rỉ theo thời gian và theo phiên; NB07 §3 đo được chia ngẫu nhiên làm tăng balanced acc thêm +0,073 trên UNSW | Chia theo **base station** và theo **loại tấn công** |
| T5 | Lưu lượng lành tính được bắt **cùng lúc** với tấn công | Benign có trong mọi phiên | Tốt: không có shortcut "thời điểm = nhãn" trong benign. Nhưng phải kiểm tra lại sau khi đã bỏ `Seq` |

---

## 5. KẾ HOẠCH THÍ NGHIỆM

Quy tắc chung, kế thừa NB07: **khai báo tiêu chí trước khi chạy** · chọn ngưỡng trên một tập, báo cáo trên tập khác · luôn báo cáo ROC-AUC, PR-AUC, Balanced acc, MCC, Recall, FPR, kèm **Recall theo loại tấn công** · paired bootstrap 1.000 lần cho mọi so sánh.

### Giai đoạn 0 — Thu thập và kiểm tra schema (0,5 ngày)
- Tải `Combined.zip` (và `BTS_1`, `BTS_2` nếu `Combined.csv` không có cột trạm).
- Kiểm tra: header có `SIntPkt`, `DIntPkt`, `SrcJitter`, `DstJitter`, `StartTime`, `SrcAddr`, `Dport` không; nhãn `Label`, `Attack Type`, `Attack Tool`; n mỗi lớp khớp Bảng XXII của bài báo.
- **Cổng 0:** nếu thiếu cả nhóm B lẫn C thì model chỉ còn 21 feature → dùng phương án ở Giai đoạn 1.

### Giai đoạn 1 — Ánh xạ, chuẩn hoá đơn vị, làm sạch (1–2 ngày) → `notebooks/08_5GNIDD_Prepare.ipynb`
- Áp bảng ánh xạ ở §2. Đối chiếu phân vị (q1, q50, q99) từng feature với UNSW để phát hiện lệch đơn vị (ms/s, bit/byte).
- Bỏ các cột ở T1 và T2. Khử trùng lặp (T3). Ghi `data/5gnidd/cleaned/*.parquet`.
- Phương án dự phòng nếu thiếu nhóm B/C: fit lại RF trên UNSW **chỉ với giao của hai bộ feature** (≈ 21–25 feature). So với RF 31f trên UNSW `test-final` để biết bỏ feature tốn bao nhiêu **trong miền**, trước khi đo chéo.

### Giai đoạn 2 — Các thí nghiệm → `notebooks/09_5GNIDD_CrossValidation.ipynb`

| ID | Thí nghiệm | Train | Chọn ngưỡng | Đánh giá | Câu hỏi |
|---|---|---|---|---|---|
| **E1** | Zero-shot | UNSW (RF 31f, đông cứng) | 0,5 / 0,6949 / EM-prior (không dùng nhãn 5G) | toàn bộ 5G-NIDD, tách theo BS | Model hiện tại dùng được ngay trên 5G không? |
| **E2** | Hiệu chỉnh ngưỡng ít nhãn | UNSW (đông cứng) | 1% có nhãn của **BS1**, FPR ≤ 0,10 | **BS2** | Nếu được phép gán nhãn một ít lưu lượng 5G, có cứu được không? |
| **E3** | Trong miền, chia theo trạm | 5G BS1 | val trong BS1 | BS2 (và ngược lại) | Chặn trên thực tế trên 5G |
| **E4** | Leave-one-attack-out | 5G, bỏ 1 loại tấn công | val | loại bị bỏ + benign | Có phát hiện được tấn công chưa thấy (zero-day) không? |
| **E5** | Huấn luyện gộp và thích ứng miền | UNSW + 5G BS1; thử CORAL | val | BS2 | Kiến thức UNSW có giúp gì cho 5G không? (CORAL nằm trong danh sách NB07 §14 "chưa thử") |
| **E6** | Kiểm tra ô nhiễm | 5G, mỗi lần 1 feature | — | blind generalization (D'hooge) | `sTtl`, `Seq`, `Offset` thổi phồng điểm bao nhiêu? |
| **E7** | Chiều ngược | 5G (BS1+BS2) | — | UNSW, lớp DoS + Reconnaissance | Lệch miền có đối xứng không? |

Trong E1 và E2 bắt buộc có thêm hai phân tích:
- **Phân rã FP**: FP theo `proto`/`state`, và theo khoảng `ackdat` (0, < 10 ms, 10–50 ms, > 50 ms) để kiểm chứng trực tiếp giả thuyết shortcut độ trễ ở §3.1.
- **Ablation `ackdat`/`synack`/`tcprtt`**: chạy lại E1 với model UNSW **không có** ba feature này (fit lại trên UNSW). Nếu FPR trên 5G giảm mạnh mà UNSW chỉ mất một chút, thì đây là cấu hình nên mang sang 5G.

### Tiêu chí khai báo trước

| Kết luận | Điều kiện |
|---|---|
| "Model UNSW **chuyển giao được** sang 5G" | E1: ROC-AUC ≥ 0,90 **và** Balanced acc ≥ 0,80 **và** FPR ≤ 0,20 ở một ngưỡng chọn không cần nhãn 5G |
| "Chuyển giao được **khi có ít nhãn**" | E2: Recall ≥ 0,90 với FPR ≤ 0,10 trên BS2 |
| "Cần huấn luyện trong miền 5G" | E1 và E2 đều không đạt; E3 đạt Balanced acc ≥ 0,95 |
| Báo cáo được con số kiểu bài báo gốc (99,9%) | **Không bao giờ** — chỉ được dẫn như tham chiếu, kèm ghi chú T1–T4 |

### Dự báo, ghi lại trước để đối chiếu sau

| | ROC-AUC | Balanced acc | FPR @0,5 |
|---|---|---|---|
| E1 zero-shot | 0,70–0,90 | 0,65–0,80 | **0,40–0,60** |
| E2 ít nhãn | ROC-AUC không đổi so với E1 (đổi ngưỡng không đổi xếp hạng — NB07 §7) | — | — |
| E3 trong miền, chia theo trạm | ≥ 0,98 | 0,95–0,99 | — |
| E4 leave-attack-out | thấp nhất với HTTP Flood và Slowrate DoS (bài báo cũng ghi hai lớp này hay bị nhầm với nhau) | — | — |

Nếu E1 thực tế **tốt hơn** dải dự báo, phải kiểm tra lại rò rỉ (T1, T3) trước khi tin kết quả.

### Tài nguyên tính toán
- Sau khi bỏ `Seq`/`Offset`, khử trùng lặp dự kiến giảm mạnh 1,2 triệu dòng, chủ yếu ở UDP Flood. Kể cả không giảm, RF 300 cây, `max_depth` 20, 25 feature trên 850k dòng train mất khoảng 10–20 phút trên máy hiện tại.
- E1, E2 không fit lại model (dùng lại `rf_A_trainfit.joblib`). E3 đến E7 cần khoảng 15 lần fit.
- Tổng thời gian ước tính: **4–6 ngày làm việc**, gồm cả báo cáo.

---

## 6. ĐIỀU CHƯA BIẾT / GIỚI HẠN CỦA BẢN KẾ HOẠCH NÀY

- **Chưa mở được tệp dữ liệu** (cần subscription IEEE DataPort). Danh sách cột của `Combined.csv` (nhóm B, C ở §2) được suy ra từ bài báo và tài liệu Argus, **chưa xác minh trực tiếp**.
- Stress test ở §3.2 là **mô phỏng trên dữ liệu UNSW**, không phải đo trên 5G-NIDD. Khoảng trễ 10–40 ms và 30–80 ms là giả định hợp lý cho 5G NSA đo tại S1-U, không phải số đo từ 5GTN. Mô phỏng chỉ nắm được hai khác biệt đã biết, nên các số trong bảng là **chặn dưới** của mức suy giảm.
- 5G-NIDD chỉ chứa DoS và scan. Dù kết quả tốt đến đâu, cũng **không** kết luận được gì về Exploits, Fuzzers hay Backdoor trên 5G.

---

**Nguồn:** Samarakoon et al., *5G-NIDD: A Comprehensive Network Intrusion Detection Dataset Generated over 5G Wireless Network*, arXiv 2212.01298 · IEEE DataPort 10203 · D'hooge et al., PST 2022 (`References/PST_CR.pdf`) · `reports/Bao_cao_ket_qua_notebook07.md`.
