# Đối chiếu 5G-NIDD với UNSW-NB15 và cross-validate model hiện tại

**Dự án:** 5G IDS · model **RF 31 feature** (`reports/exp05/rf_A_trainfit.joblib`, đã kiểm tra tái lập accuracy test-final = 0,81862 như NB07)
**Ngày:** 26/10/2026
**Dữ liệu đích:** 5G-NIDD, bản trên Fairdata (CC BY 4.0, truy cập mở) — tải trực tiếp, không cần tài khoản IEEE
**Mã nguồn (chạy lại được từ đầu):**

| Bước | Lệnh | Ra |
|---|---|---|
| 1. Ánh xạ | `python -I -X utf8 reports/5gnidd/build_5gnidd_unsw31.py <dự án>` | `data/5gnidd/cleaned/*.parquet`, `build_stats.json` |
| 2. Cross-validate | `python -I -X utf8 reports/5gnidd/eval_5gnidd.py <dự án>` | `ket_qua_5gnidd.json`, `so_sanh_feature.csv`, `chan_doan_feature.csv` |
| 3. Chẩn đoán | `python -I -X utf8 reports/5gnidd/chan_doan_tuong_tu.py <dự án>` | `chan_doan_tuong_tu_ket_qua.txt` |

**Không file nào trong `data/cleaned/`, `models/`, `notebooks/` bị thay đổi.**

---

## 0. TÓM TẮT

| Câu hỏi | Kết quả |
|---|---|
| **5G-NIDD có đưa được vào model hiện tại không?** | **CÓ — đã làm xong.** Tệp `data/5gnidd/cleaned/5gnidd_unsw31.parquet` có **đúng 31 feature, đúng tên, đúng kiểu, đúng đơn vị** của UNSW đã làm sạch. Pipeline của model chạy trên tệp này mà không cần sửa gì. Gồm 379.563 flow (63.283 Benign, 316.280 Attack), đã tách BS1/BS2. |
| **Ánh xạ có đáng tin không?** | **Có.** 19/31 feature (83% importance) lấy chính xác, theo công thức Argus đã kiểm khớp 99,6–100% trên cả hai bộ, hoặc hiệu chỉnh có bằng chứng. Phép thử round-trip (áp đúng các phép xấp xỉ lên UNSW-test) chỉ làm ROC-AUC giảm **0,9594 → 0,9525** (−0,007). Nghĩa là phần ánh xạ chỉ tốn khoảng 0,7 điểm ROC-AUC. |
| **Model hiện tại phát hiện được tấn công trên 5G không?** | **KHÔNG.** ROC-AUC = **0,399** (thấp hơn ngẫu nhiên), balanced accuracy @0,5 = **0,446**, MCC = **−0,080**. Model gán điểm tấn công cho lưu lượng 5G **lành tính** (FPR 61%) và bỏ sót gần hết **UDP flood, SYN flood, ICMP flood và các loại scan** (recall ≈ 0). Hiệu chỉnh ngưỡng bằng nhãn của trạm kia cũng không cứu được, vì thứ tự xếp hạng đã bị đảo. |
| **Vì sao?** | Không phải do ánh xạ, mà do **hai bộ dữ liệu gọi cùng một tên tấn công cho những hành vi khác hẳn nhau** (§8). Ví dụ "Reconnaissance" của UNSW là kết nối hoàn chỉnh (FIN, 8 gói về, 354 byte về); SYN scan của nmap trong 5G là **một gói SYN trơn, 0 byte về**. Model chưa từng thấy loại flow này được gắn nhãn tấn công. |
| **Phát hiện phụ về chất lượng 5G-NIDD** | **281.529 flow (59% lớp Benign) bị gán nhãn sai.** Đó là bản sao của UDP flood từ máy tấn công BS2, bị bắt lại ở BS1 và gán nhãn Benign (§5.1). Ngoài ra `SIntPkt`/`DIntPkt`/jitter **rỗng 100%**, `SAppBytes`/`DAppBytes` **luôn bằng 0**, và `StartTime` chỉ có `mm:ss.f`. |

**Một câu:** 5G-NIDD **đã cross-validate được** bằng model hiện tại; kết quả cross-validate là model **không chuyển giao** sang 5G (ROC-AUC 0,40). Đây là kết quả đo được với ánh xạ đã kiểm chứng, không phải do thiếu dữ liệu hay sai đơn vị.

> **Sửa dự báo của bản kế hoạch trước** (`Ke_hoach_validate_cheo_5G-NIDD.md`): tôi đã dự báo flood và scan "bị bắt tốt", và ROC-AUC zero-shot 0,70–0,90. **Cả hai đều sai.** Dự báo về FPR cao trên Benign do độ trễ vô tuyến thì đúng: FPR Benign-TCP ở dải `ackdat` 10–50 ms là **71,5%**. Nhưng điều tôi không lường trước là model **bỏ sót** flood và scan, vì hình dạng flow của chúng khác hẳn tấn công trong UNSW.

---

## 1. DỮ LIỆU ĐÃ TẢI

Nguồn: Fairdata/Etsin `9d13ef28-2ca7-44b0-9950-225359afac65`. Truy cập **Open**, giấy phép **CC BY 4.0**. Bắt buộc trích dẫn bài báo gốc (IEEE Xplore 11098458 / arXiv 2212.01298).

| Tệp | Kích thước | SHA-256 (12 ký tự đầu) | Dùng làm gì |
|---|---|---|---|
| `README.pdf` | 147 KB | — | Mô tả tệp |
| `BTS1_BTS2_fields_preserved.zip` → `.csv` | 46,5 MB → 472 MB | `625F4D178C8A` | **Nguồn chính**: 113 trường Argus, giữ cả trường rỗng |
| `Combined.zip` → `.csv` | 28,0 MB → 275 MB | `07531B251F3F` | Đối chiếu: 52 cột, khớp 100% với tệp trên ở các cột chung |
| `BTS_1.zip`, `BTS_2.zip` | 14,0 / 10,7 MB | `01E6C4669E64` / `6C420140E7DC` | Xác định ranh giới trạm: 728.316 dòng đầu = BS1 (khớp 100%), 487.574 dòng sau = BS2 |

Vị trí: `data/5gnidd/raw/` (zip), `data/5gnidd/extracted/` (CSV giải nén, khoảng 1 GB, có thể xoá và giải nén lại từ zip).
Không tải pcap (≈ 7,8 GB), vì mọi feature cần thiết đã có trong CSV hoặc suy ra được (§3).

---

## 2. HAI BỘ DỮ LIỆU — ĐỐI CHIẾU TỔNG QUAN

| | UNSW-NB15 (đã làm sạch, `data/cleaned`) | 5G-NIDD |
|---|---|---|
| Công cụ sinh flow | Argus + Bro (Zeek) | **Argus** (bản mới hơn), không có Bro |
| Môi trường | Mạng LAN mô phỏng, IXIA PerfectStorm | Mạng 5G NSA thật (5GTN Oulu), bắt ở S1-U, đã bóc GTP |
| Lưu lượng lành tính | Do IXIA sinh | Điện thoại thật: streaming, web, SSH, SFTP (90% là UDP/QUIC) |
| Tấn công | 9 họ: Exploits, Fuzzers, Generic, DoS, Recon, Backdoor, Analysis, Shellcode, Worms | 8 loại, **chỉ DoS và scan**: UDP/SYN/ICMP/HTTP flood, Slowrate, SYN/TCP-Connect/UDP scan |
| Số dòng thô | 257.673 (train + test chính thức) | 1.215.890 |
| Sau làm sạch | 98.934 + 50.567 | **379.563** (§5) |
| Tỷ lệ Attack | 0,50 (train) / 0,37 (test) | **0,833** |
| Số feature | 31 (sau khi bỏ 9 cột ô nhiễm + 3 cột vô dụng ở NB01) | 112 trường Argus (52 trong `Combined.csv`) |

---

## 3. BẢNG ÁNH XẠ CHI TIẾT — 31 FEATURE CỦA MODEL

Cột **Mức** có năm giá trị:
- **CX** — chính xác: copy trường cùng định nghĩa Argus.
- **CT** — công thức: tính lại theo công thức đã kiểm khớp trên cả hai bộ.
- **HC** — hiệu chỉnh: đổi đơn vị hoặc ngữ nghĩa cho khớp UNSW.
- **XX** — xấp xỉ: suy ra vì trường gốc rỗng.
- **SL** — suy luận: thay cho feature Bro.

Cột **Perm.imp** là tỷ trọng importance của feature trong model (`random_forest_v2_importance.csv`).

| # | Feature UNSW | Định nghĩa UNSW | Nguồn 5G-NIDD | Phép biến đổi | Mức | Bằng chứng kiểm chứng | Perm.imp |
|---|---|---|---|---|---|---|---|
| 1 | `dur` | Thời lượng flow (s) | `Dur` | copy | CX | cùng trường Argus | 1,0% |
| 2 | `proto` | Giao thức | `Proto` | copy (chuỗi) | CX | cùng từ vựng Argus; 0,03% giá trị chưa gặp (`llc`, `lldp`) | 1,6% |
| 3 | `service` | Dịch vụ do Bro nhận diện | `Dport` (tên cổng) | http→http, https→ssl, domain→dns, ssh, ftp…; TCP chưa bắt tay xong (`AckDat`=0) → `-` | SL | UNSW: TCP có `ackdat`=0 → `-` ở **96,4%** dòng | 5,5% |
| 4 | `state` | Trạng thái Argus | `State` | copy; riêng **UDP `REQ` → `INT`** | HC | UNSW: UDP một chiều là `INT` (8.900) và chỉ 118 `REQ`; 5G: UDP `REQ` và `INT` đều có `DstPkts`=0 ở 100% dòng | 2,4% |
| 5 | `spkts` | Số gói src→dst | `SrcPkts` | copy | CX | — | 1,0% |
| 6 | `dpkts` | Số gói dst→src | `DstPkts` | copy | CX | — | 0,9% |
| 7 | `sbytes` | Byte src→dst | `SrcBytes` | **− 14 × SrcPkts** (bỏ header Ethernet) | HC | UNSW ARP = 46 byte (khung tối thiểu 60 − 14) và 28 byte; 5G ARP/UDP-flood = 60/42 byte (có Ethernet). UDP rỗng của hping3: 42 = 14 + 20 + 8 | 12,8% |
| 8 | `dbytes` | Byte dst→src | `DstBytes` | − 14 × DstPkts | HC | như trên | 6,3% |
| 9 | `rate` | Gói/giây | `Rate` | copy | CT | UNSW: `rate = (spkts+dpkts−1)/dur` khớp **100%** (q05–q95 = 1,0000); 5G: `Rate = (TotPkts−1)/Dur` khớp **100%** | 2,2% |
| 10 | `sload` | bit/s src→dst | tính lại | `8·sbytes·(spkts−1)/spkts/dur` (0 nếu spkts ≤ 1) | CT | công thức khớp **99,6%** dòng UNSW và **100%** dòng 5G (`SrcLoad`). Tính lại sau khi bỏ Ethernet | 1,0% |
| 11 | `dload` | bit/s dst→src | tính lại | như trên với dbytes, dpkts | CT | như trên | 10,1% |
| 12 | `sloss` | "Gói src mất/truyền lại" | bảng tra UNSW-train | trung vị `sloss` của UNSW-train theo (proto, state, spkts); UDP = 0 | XX | `sloss` của UNSW **không phải** mất gói thật: TCP 10 gói → 2, 14 gói → 6, UDP luôn 0. Trong 5G, `SrcLoss` > 0 chỉ ở 3,4% flow TCP. Round-trip: Spearman 0,97, khớp chính xác 79,8% | 1,5% |
| 13 | `dloss` | như trên, chiều về | bảng tra | như trên với dpkts | XX | Spearman 0,96, khớp chính xác 64,8% | 2,8% |
| 14 | `sinpkt` | Khoảng cách gói src (ms) | **`SIntPkt` rỗng 100%** → tính từ `Dur` | `Dur·1000/(SrcPkts−1)` | XX | Trên UNSW: 89,4% sai lệch ≤ 20%, Spearman 0,95 | 0,9% |
| 15 | `dinpkt` | như trên, chiều về | `DIntPkt` rỗng → tính từ `Dur` | `Dur·1000/(DstPkts−1)` | XX | 80,6% sai lệch ≤ 20%, Spearman 0,84 | 1,8% |
| 16 | `sjit` | Jitter src (ms) | **jitter rỗng 100%** → model hồi quy | HGB học trên UNSW-train (từ sinpkt xấp xỉ, spkts, dur, sbytes, proto); = 0 nếu spkts ≤ 2 | XX | Spearman với giá trị thật trên UNSW-test **0,98**. UNSW: jitter = 0 ở 98% flow ≤ 2 gói | 0,8% |
| 17 | `djit` | Jitter dst | như trên | như trên | XX | Spearman 0,98 | 0,6% |
| 18 | `swin` | Cửa sổ TCP src | `Proto` | **tcp → 255, còn lại 0** | HC | UNSW chỉ có 0/255: 99,98% TCP = 255, 100% không-TCP = 0. 5G `SrcWin` là giá trị thật (64.256…), khác thang | 1,1% |
| 19 | `stcpb` | Số thứ tự TCP ban đầu | `SrcTCPBase` | copy, rỗng → 0 | CX | UNSW: không-TCP = 0 ở 100% dòng | 0,2% |
| 20 | `dtcpb` | như trên, chiều về | `DstTCPBase` | như trên | CX | — | 0,8% |
| 21 | `dwin` | Cửa sổ TCP dst | `Proto`, `DstPkts` | tcp có gói về → 255, còn lại 0 | HC | UNSW: TCP có `dpkts`=0 → `dwin`=0 ở 100% (813/813) | 0,0% |
| 22 | `tcprtt` | RTT bắt tay (s) | `TcpRtt` | copy | CX | `tcprtt = synack + ackdat` đúng 100% ở cả hai bộ | 3,6% |
| 23 | `synack` | SYN → SYN/ACK (s) | `SynAck` | copy | CX | — | 4,2% |
| 24 | `ackdat` | SYN/ACK → ACK (s) | `AckDat` | copy | CX | — | **25,0%** |
| 25 | `smean` | Cỡ gói TB src | tính lại | `round(sbytes/spkts)` | CT | UNSW: khớp **100%**. Tính sau khi bỏ Ethernet | 5,7% |
| 26 | `dmean` | Cỡ gói TB dst | tính lại | `round(dbytes/dpkts)`, 0 nếu không có gói | CT | UNSW: khớp **100%**; `dpkts`=0 → 0 ở 100% | 3,1% |
| 27 | `trans_depth` | Độ sâu pipeline HTTP (Bro) | `service` | `service == http` → 1, còn lại 0 | SL | UNSW: http + bắt tay xong → 1 ở **91%**; round-trip khớp 98,0% | 0,2% |
| 28 | `response_body_len` | Độ dài body HTTP (Bro) | không có | 0 | SL | `DAppBytes` = 0 ở mọi dòng nên không tách được body | 0,4% |
| 29 | `ct_src_dport_ltm` | Số kết nối cùng src và dport trong 100 kết nối gần nhất | `SrcAddr`, `Dport` | cửa sổ trượt 100 bản ghi, theo thứ tự trong từng file BS | XX | `StartTime` chỉ có `mm:ss.f` nên dùng thứ tự dòng. Không round-trip được vì UNSW đã làm sạch không còn IP/cổng | 1,7% |
| 30 | `ct_flw_http_mthd` | Số flow có lệnh HTTP (Bro) | `service` | như `trans_depth` | SL | UNSW http: = 1 ở 88% | 0,1% |
| 31 | `ct_src_ltm` | Số kết nối cùng src trong 100 kết nối gần nhất | `SrcAddr` | như #29 | XX | như #29 | 0,4% |

**Tổng hợp theo mức (theo perm. importance):**

| Mức | Số feature | Tỷ trọng importance |
|---|---|---|
| CX + CT (chính xác / công thức đã kiểm) | 14 | **60,4%** |
| HC (hiệu chỉnh có bằng chứng) | 5 | 22,6% (`sbytes`, `dbytes` chiếm 19,1%) |
| XX (xấp xỉ / tra bảng / cửa sổ) | 8 | 10,5% |
| SL (suy luận thay Bro) | 4 | 6,2% |

→ **83,0%** importance nằm ở feature lấy chính xác, theo công thức, hoặc hiệu chỉnh có bằng chứng. 16,7% còn lại là xấp xỉ và suy luận, đã kiểm bằng round-trip ở dưới.

**Round-trip — các phép xấp xỉ tốn bao nhiêu?** Áp đúng phép xấp xỉ #12–17, #18, #21, #27–28, #30 lên UNSW `test-final`, rồi chấm lại bằng model:

| | ROC-AUC | PR-AUC | Bal acc @0,5 | MCC @0,5 | Recall @0,5 | FPR @0,5 |
|---|---|---|---|---|---|---|
| UNSW test-final gốc | 0,9594 | 0,9414 | 0,8461 | 0,6672 | 0,9491 | 0,2569 |
| UNSW test-final qua xấp xỉ | **0,9525** | 0,9318 | 0,8318 | 0,6410 | 0,9539 | 0,2903 |
| Δ | **−0,0069** | −0,0096 | −0,0143 | −0,0262 | +0,0048 | +0,0334 |

Các phép xấp xỉ chỉ làm mất **0,7 điểm ROC-AUC**. Mức tụt trên 5G là **0,56 điểm** (0,96 → 0,40), tức **lớn gấp khoảng 80 lần**. Phần ánh xạ không giải thích được kết quả trên 5G.

---

## 4. PHÂN BỐ TỪNG FEATURE — HAI BỘ ĐẶT CẠNH NHAU

Số liệu: `so_sanh_feature.csv`. Ký hiệu q50/q90 = trung vị / phân vị 90. KS = khoảng cách Kolmogorov–Smirnov (0 = trùng, 1 = tách hẳn).
**Δ ROC chẩn đoán** (§8.2): ROC-AUC trên 5G thay đổi bao nhiêu khi thay riêng feature đó bằng trung vị UNSW. Giá trị dương nghĩa là feature đó đang **kéo model sai**.

| Feature | UNSW Normal | UNSW Attack | 5G Benign | 5G Attack | KS Normal↔Benign | KS Attack↔Attack | % 5G ngoài khoảng UNSW | Δ ROC chẩn đoán |
|---|---|---|---|---|---|---|---|---|
| `dur` | 0,109 / 1,34 | 0,671 / 2,50 | 0,161 / 5,00 | 2,28 / 4,58 | 0,356 | 0,410 | 0 | −0,001 |
| `spkts` | 12 / 66 | 10 / 32 | 3 / 150 | 2 / 7 | 0,370 | **0,749** | 9,6% | −0,023 |
| `dpkts` | 10 / 66 | 8 / 24 | 3 / 24 | 1 / 9 | 0,353 | 0,604 | 0 | −0,004 |
| `sbytes` | 1.514 / 7.820 | 862 / 10.880 | 489 / 196.900 | **60 / 700** | 0,351 | 0,639 | 9,6% | +0,013 |
| `dbytes` | 1.092 / 45.700 | 354 / 5.262 | 161 / 6.085 | **52** / 11.700 | 0,413 | 0,512 | 0 | −0,089 |
| `rate` | 475 / 5.625 | 35,8 / 125.000 | 28,0 / 134 | **0,44** / 6,1 | 0,482 | **0,869** | 0,04% | −0,008 |
| `sload` | 274k / 1,9M | 14,6k / 133M | 14,4k / 360k | **87** / 1.601 | 0,390 | **0,884** | 0 | −0,002 |
| `dload` | 204k / 7,9M | 3.973 / 54,7k | 5.610 / 163k | 0 / 17,9k | 0,448 | 0,542 | 0,2% | −0,041 |
| `sloss` | 3 / 11 | 2 / 8 | 0 / 3 | 1 / 3 | 0,561 | 0,290 | 0 | +0,006 |
| `dloss` | 2 / 26 | 1 / 8 | 0 / 1 | 1 / 4 | 0,654 | 0,227 | 0 | −0,009 |
| `sinpkt` | 4,2 / 111 | 52,5 / 153 | 26,7 / 1.499 | 574 / 2.582 | 0,287 | 0,517 | 0 | −0,005 |
| `dinpkt` | 1,3 / 116 | 62,1 / 166 | 23,4 / 394 | 0 / 1.111 | 0,354 | 0,400 | 0 | −0,015 |
| `sjit` | 132 / 8.652 | 2.890 / 8.800 | 35,0 / 1.658 | 0 / 36.290 | 0,311 | 0,470 | 0 | +0,005 |
| `djit` | 30,6 / 709 | 123 / 1.738 | 20,4 / 810 | 0 / 28.170 | 0,261 | 0,446 | 0 | +0,013 |
| `swin` | 255 / 255 | 255 / 255 | 0 / 255 | 255 / 255 | 0,547 | 0,004 | 0 | +0,007 |
| `stcpb` | 1,5e9 / 3,7e9 | 1,5e9 / 3,7e9 | 0 / 2,4e9 | 1,5e9 / 3,7e9 | 0,537 | 0,017 | 0 | +0,009 |
| `dtcpb` | 1,5e9 / 3,7e9 | 1,5e9 / 3,7e9 | 0 / 7,6e8 | 1,2e9 / 3,7e9 | 0,644 | 0,068 | 0 | +0,007 |
| `dwin` | 255 / 255 | 255 / 255 | 0 / 255 | 255 / 255 | 0,645 | 0,120 | 0 | +0,002 |
| `tcprtt` | 0,0007 / 0,179 | 0,099 / 0,201 | 0 / 0 | 0,015 / 0,035 | **0,681** | **0,699** | 0 | +0,001 |
| `synack` | 0,0005 / 0,095 | 0,049 / 0,106 | 0 / 0 | 0,0016 / 0,0022 | **0,681** | **0,764** | 0 | +0,008 |
| `ackdat` | 0,0001 / 0,082 | 0,049 / 0,100 | 0 / 0 | 0,014 / 0,032 | **0,681** | 0,595 | 0 | −0,019 |
| `smean` | 73 / 252 | 88 / 680 | 162 / 1.326 | **52 / 105** | 0,327 | 0,541 | 9,6% | **+0,115** |
| `dmean` | 89 / 785 | 45 / 406 | 84 / 554 | 52 / 1.012 | 0,201 | 0,201 | 0 | +0,027 |
| `trans_depth` | 0 / 1 | 0 / 1 | 0 / 0 | 1 / 1 | 0,104 | 0,444 | 0 | −0,013 |
| `response_body_len` | 0 / 0 | 0 / 140 | 0 / 0 | 0 / 0 | 0,098 | 0,120 | 0 | 0 |
| `ct_src_dport_ltm` | 1 / 3 | 1 / 3 | 6 / 57 | **99 / 100** | 0,642 | **0,914** | **76,1%** | −0,035 |
| `ct_flw_http_mthd` | 0 / 1 | 0 / 1 | 0 / 0 | 1 / 1 | 0,104 | 0,444 | 0 | −0,001 |
| `ct_src_ltm` | 3 / 8 | 2 / 7 | 12 / 56 | **99 / 100** | 0,487 | **0,973** | **81,3%** | +0,001 |

| Feature phân loại | UNSW (tỷ lệ) | 5G (tỷ lệ) | % 5G chưa gặp trong UNSW-train |
|---|---|---|---|
| `proto` | tcp 0,775 · udp 0,161 · unas 0,013 · ospf 0,006 | tcp 0,683 · udp 0,290 · icmp 0,017 · **sctp 0,009** | 0,03% |
| `service` | - 0,624 · http 0,174 · dns 0,078 · smtp 0,045 | **http 0,564** · - 0,380 · ssl 0,052 · dns 0,004 | 0% |
| `state` | FIN 0,747 · CON 0,124 · INT 0,119 · REQ 0,008 | CON 0,345 · INT 0,206 · **RST 0,199** · FIN 0,152 | 0,36% (URP, RSP, TST, NRS) |

**Cách đọc:**
- **Không còn lỗi đơn vị.** Gần như mọi giá trị 5G nằm trong khoảng giá trị của UNSW. Ngoại lệ là `ct_*` (76–81% dòng 5G vượt mức tối đa 60 của UNSW) và `spkts`/`sbytes`/`smean` (9,6%, chủ yếu là Benign streaming lớn).
- **Lệch lớn nhất nằm ở lớp Attack** (KS Attack↔Attack 0,6–0,97 ở `rate`, `sload`, `spkts`, `ct_*`), không phải lớp Normal. Ngược với tình huống UNSW train→test của NB07, nơi lệch tập trung ở Normal. Tức là **tấn công của 5G không giống tấn công của UNSW.**
- **Benign 5G có `tcprtt`/`synack`/`ackdat` = 0 ở hơn 90% dòng**, vì 90% Benign là UDP. Phần TCP còn lại thì đúng như dự báo: FPR @0,5 ở dải `ackdat` 10–50 ms là **71,5%**, và **86,3%** khi > 50 ms, so với 6,5% khi `ackdat` = 0.

---

## 5. CHẤT LƯỢNG DỮ LIỆU 5G-NIDD — PHÁT HIỆN KHI KIỂM TRA

### 5.1 Lỗi nhãn: 281.529 flow tấn công bị gán Benign

| Kiểm tra | Kết quả |
|---|---|
| Flow từ máy tấn công `10.155.15.7` → server nạn nhân `10.41.150.68` | 281.529 nhãn `UDPFlood` (trong file **BS2**) + **281.529 nhãn `Benign`** (trong file **BS1**) |
| So sánh từng cặp theo thứ tự | `Sport`, `Dur`, `SrcPkts`, `sIpId` (IP-ID ngẫu nhiên của hping3), `StartTime`… **trùng khít**. Chỉ khác `Seq`/`Offset` (vị trí trong file) và nhãn |
| Cỡ gói | 42 byte ở 100% dòng, đúng dấu vân tay hping3 `--udp` không payload |
| Diễn giải | Flood của kẻ tấn công BS2 đi qua điểm bắt gói của BS1. Bộ gán nhãn BS1 chỉ đánh dấu kẻ tấn công của BS1, nên bản sao này nhận nhãn Benign |
| Mức ảnh hưởng | **59%** lớp Benign đã công bố (281.529/477.737) thực chất là tấn công, đồng thời là **rò rỉ giữa hai trạm**: cùng flow nằm ở cả BS1 lẫn BS2 |
| Xử lý | **Loại** 281.529 bản sao khỏi BS1 (cột `dup_capture` trong `_full.parquet` giữ dấu để kiểm tra lại) |

Quy tắc phát hiện chỉ dùng thông tin không phải nhãn: *Benign ở trạm X, nguồn là IP tấn công của trạm kia, đích là server nạn nhân*. Quy tắc này bắt đúng 281.529 dòng ở BS1 và **0** dòng ở BS2.

### 5.2 Các vấn đề khác

| Vấn đề | Ảnh hưởng | Xử lý |
|---|---|---|
| `SIntPkt`, `DIntPkt`, `SrcJitAct`, `DstJitter`… **rỗng 100%** (Argus không bật thống kê jitter) | Thiếu 4 feature `sinpkt`/`dinpkt`/`sjit`/`djit` | Xấp xỉ (§3 #14–17) |
| `SAppBytes`, `DAppBytes` **= 0 ở mọi dòng** (Argus không bật `-A`) | Không biết flow có payload ứng dụng không | `service` suy từ cổng + trạng thái bắt tay |
| `StartTime`, `LastTime` chỉ có `mm:ss.f` (mất giờ và ngày) | Không sắp được theo thời gian tuyệt đối | `ct_*` dùng thứ tự dòng trong từng file BS |
| `Dport` rỗng ở 100% UDPFlood và 83,8% Benign | `ct_src_dport_ltm` gộp theo khoá "rỗng" | Giữ nguyên, có ghi chú |
| `Seq`, `Offset` đứng đầu bảng ANOVA trong bài báo gốc | Chúng là vị trí bản ghi trong file, tức metadata thuần | Không dùng (model không có các cột này) |
| `sTtl` hạng 3 ANOVA trong bài báo gốc | Feature ô nhiễm (D'hooge 2022), đã bị NB01 loại khỏi UNSW | Không dùng |

### 5.3 Làm sạch — đúng quy tắc NB01

| Bước | Số dòng |
|---|---|
| Thô | 1.215.890 |
| − bản sao bắt nhầm (§5.1) | 934.361 |
| − trùng lặp hoàn toàn trên 31 feature + nhãn | **−554.798** (hping3/nmap sinh hàng loạt flow giống hệt) |
| − nhóm mâu thuẫn nhãn | −0 |
| **Còn lại** | **379.563** |

| Lớp | BS1 | BS2 | Tổng |
|---|---|---|---|
| Benign | 40.267 | 23.016 | 63.283 |
| HTTPFlood | 76.120 | 64.691 | 140.811 |
| SlowrateDoS | 36.091 | 37.032 | 73.123 |
| UDPFlood | 39.265 | 30.656 | 69.921 |
| TCPConnectScan | 10.014 | 10.028 | 20.042 |
| SYNFlood | 4.792 | 4.929 | 9.721 |
| SYNScan | 529 | 519 | 1.048 |
| ICMPFlood | 568 | 462 | 1.030 |
| UDPScan | 375 | 209 | 584 |

---

## 6. CÁC TỆP DỮ LIỆU ĐÃ TẠO

| Tệp | Nội dung | Dùng khi |
|---|---|---|
| `data/5gnidd/cleaned/5gnidd_unsw31.parquet` | **Tập validate chính**: 31 feature + `label`, `attack_cat`, `bs`, `attack_tool`, `src_addr`. Nhãn đã sửa, đã khử trùng lặp | Mọi phép cross-validate |
| `data/5gnidd/cleaned/5gnidd_unsw31_full.parquet` | 1.215.890 dòng, 31 feature + `label_published`, `dup_capture` | Tái lập điều kiện như bài báo gốc |
| `data/5gnidd/cleaned/5gnidd_unsw31_raw.parquet` | Cùng các dòng với tập chính, nhưng **ánh xạ thô**: không bỏ Ethernet, `SrcLoss`/`SrcWin` nguyên giá trị, thiếu thì gán 0 | Đo độ nhạy với các bước hiệu chỉnh |
| `data/5gnidd/cleaned/unsw_test_roundtrip.parquet` | UNSW-test sau đúng các phép xấp xỉ | Kiểm chứng round-trip |

Cách dùng với model hiện tại (cùng hàm `X_of` của NB07):

```python
g = pd.read_parquet('data/5gnidd/cleaned/5gnidd_unsw31.parquet')
p = rf.predict_proba(g[FEATS].astype({c: str for c in ['proto', 'service', 'state']}))[:, 1]
```

---

## 7. KẾT QUẢ CROSS-VALIDATE

### 7.1 Zero-shot — model UNSW giữ nguyên, không dùng nhãn 5G

| Cấu hình | n | π | ROC-AUC | PR-AUC | Accuracy | Bal acc | MCC | Precision | Recall | FPR |
|---|---|---|---|---|---|---|---|---|---|---|
| @0,5 | 379.563 | 0,833 | **0,399** | 0,747 | 0,484 | **0,446** | **−0,080** | 0,805 | 0,503 | **0,611** |
| @0,6949 (ngưỡng UNSW test-dev) | 379.563 | 0,833 | 0,399 | 0,747 | 0,199 | 0,357 | −0,286 | 0,596 | 0,120 | 0,407 |
| EM sửa prior, @0,5 | 379.563 | 0,833 | 0,399 | 0,747 | 0,820 | 0,503 | 0,013 | 0,834 | 0,978 | **0,973** |
| BS1 @0,5 | 208.021 | 0,806 | 0,425 | 0,725 | 0,477 | 0,454 | −0,074 | 0,778 | 0,491 | 0,584 |
| BS2 @0,5 | 171.542 | 0,866 | 0,354 | 0,776 | 0,493 | 0,430 | −0,096 | 0,835 | 0,517 | 0,658 |

- **PR-AUC 0,747 < π = 0,833**: đúng dấu hiệu của một bộ xếp hạng **tệ hơn ngẫu nhiên**.
- Accuracy 0,820 của dòng EM chỉ là ảo: model gán gần như mọi flow là Attack (FPR 97%), trong khi 83% dữ liệu là Attack. Đây đúng là bẫy "Accuracy một mình" mà NB07 đã cảnh báo.
- EM ước lượng π = 0,831, rất sát π thật 0,833. Nhưng sửa prior không thay đổi thứ tự xếp hạng, nên không cứu được.

### 7.2 Hiệu chỉnh ngưỡng có nhãn (few-shot) — chọn trên một trạm, báo cáo trên trạm kia

| Chọn ngưỡng trên | Ngưỡng tìm được (FPR ≤ 0,10) | Báo cáo trên | Recall | FPR |
|---|---|---|---|---|
| BS1 | **1,000** | BS2 | 0,000 | 0,000 |
| BS2 | **1,000** | BS1 | 0,000 | 0,000 |

Vì ROC < 0,5, không có ngưỡng nào đạt FPR ≤ 0,10 mà vẫn bắt được tấn công. Quy tắc buộc phải chọn ngưỡng 1,0. **Kịch bản "có ít nhãn 5G để đặt lại ngưỡng" (E2 trong kế hoạch) thất bại.**

### 7.3 Recall theo loại tấn công

| Loại | n | Recall @0,5 | Recall @0,6949 | Giống gì trong UNSW? |
|---|---|---|---|---|
| **Benign (= FPR)** | 63.283 | **0,611** | 0,407 | — |
| HTTPFlood | 140.811 | 0,694 | 0,245 | Kết nối TCP hoàn chỉnh, `ackdat` 13 ms |
| SlowrateDoS | 73.123 | **0,834** | 0,044 | Kết nối TCP dài, `ackdat` lớn |
| UDPScan | 584 | 0,401 | 0,331 | — |
| **UDPFlood** | 69.921 | **0,003** | 0,000 | — |
| **TCPConnectScan** | 20.042 | **0,001** | 0,000 | — |
| **SYNFlood** | 9.721 | **0,000** | 0,000 | — |
| **SYNScan** | 1.048 | **0,000** | 0,000 | — |
| **ICMPFlood** | 1.030 | **0,000** | 0,000 | — |

FPR trên Benign theo giao thức @0,5: UDP **0,782** (39.453 flow) · SCTP **0,902** (3.514; báo hiệu S1-AP của 5G, trong UNSW 100% SCTP là tấn công) · TCP 0,308 (14.678) · ICMP 0,007 (5.496).

### 7.4 Độ nhạy theo cách ánh xạ và cách gán nhãn

| Biến thể | ROC-AUC | Bal acc @0,5 | Recall | FPR |
|---|---|---|---|---|
| **Chính** (hiệu chỉnh đầy đủ, nhãn đã sửa, đã khử trùng lặp) | 0,399 | 0,446 | 0,503 | 0,611 |
| Ánh xạ thô (không bỏ Ethernet, không chuẩn hoá `swin`/`sloss`/state, thiếu → 0) | 0,352 | 0,431 | 0,499 | 0,638 |
| Nhãn công bố, **không** khử trùng lặp, giữ cả bản sao lỗi (1.215.890 dòng) | 0,400 | 0,448 | 0,501 | 0,606 |

Các bước hiệu chỉnh nâng ROC-AUC thêm **+0,047**, đúng hướng. Nhưng không biến thể nào vượt 0,5. **Kết luận "không chuyển giao" đứng vững với mọi cách xử lý dữ liệu đã thử.**

---

## 8. VÌ SAO MODEL THẤT BẠI — CƠ CHẾ

### 8.1 So từng loại tấn công 5G với "họ hàng" gần nhất trong UNSW

Bảng dưới lấy trung vị feature của nhóm 5G và của nhóm UNSW tương ứng. Cột cuối cho biết xác suất Attack trung bình tăng bao nhiêu khi **chỉ** thay feature đó bằng giá trị UNSW (`chan_doan_tuong_tu_ket_qua.txt`).

| Loại 5G | p(Attack) TB 5G | Nhóm UNSW tương tự | p(Attack) UNSW | Feature khác biệt quyết định (5G → UNSW, Δp) |
|---|---|---|---|---|
| UDPFlood | 0,46 | UDP tấn công, INT, ≤ 2 gói | **0,97** | `smean` 28 → 112 (**+0,15**), `sinpkt` 2.576 → 0,008 ms (+0,10), `dur` 2,6 s → 8 µs (+0,03) |
| SYNScan | 0,04 | Reconnaissance TCP | **1,00** | `smean` 44 → 56 (**+0,37**), `dbytes` 0 → 354 (+0,18), `ackdat` 0 → 0,056 (+0,15) |
| TCPConnectScan | 0,44 | Reconnaissance TCP | 1,00 | `dbytes` 0 → 354 (+0,10), `state` REQ → FIN (+0,07), `ackdat` 0 → 0,056 (+0,05) |
| SYNFlood | 0,16 | TCP tấn công chưa bắt tay | 0,53 | `smean` 40 → 63 (+0,25), `dbytes` 44 → 586 (+0,18) |
| Benign UDP | **0,70** | Normal UDP (DNS) | **0,00** | Khoảng cách giữa các gói 30 ms vs 0,01 ms, `dload` 7 kB/s vs 635 kB/s |

**Ba cơ chế, theo thứ tự quan trọng:**

1. **Tấn công trong UNSW mang payload; flood và scan của 5G thì không.** IXIA sinh tấn công UNSW ở mức ứng dụng: Reconnaissance của UNSW là kết nối TCP *hoàn chỉnh* (state FIN, 8 gói về, 354 byte về, bắt tay 56 ms). nmap `-sS` và hping3 trong 5G gửi **gói trần** (40–58 byte, không payload, không bắt tay). Model đã học "gói nhỏ, không byte về → Normal", vì Normal UDP/ARP của UNSW trông như thế. `smean` là feature có tác động chẩn đoán lớn nhất (+0,115 ROC-AUC khi trung hoà).
2. **Độ trễ vô tuyến: shortcut `ackdat` mà bản kế hoạch đã dự báo.** Benign TCP có `ackdat` 10–50 ms bị báo động giả 71,5%. Lý do: trong UNSW, `ackdat` ≥ 10 ms gần như đồng nghĩa với tấn công (99,6% flow tấn công TCP, so với 24,7% Normal).
3. **Lưu lượng lành tính của điện thoại 5G (QUIC/streaming qua UDP, SCTP S1-AP) không có trong UNSW.** UDP Benign dài, khoảng cách giữa các gói ~30 ms, bị chấm 0,70. SCTP bị chấm tấn công vì trong UNSW 100% SCTP là tấn công.

### 8.2 Không có một feature nào "sửa" được

Trung hoà từng feature (thay bằng trung vị UNSW-train, không dùng nhãn) trên mẫu 8.000 dòng mỗi lớp:
- Feature cải thiện nhiều nhất là `smean`: ROC-AUC chỉ đi từ 0,296 lên **0,411**, vẫn dưới 0,5.
- Trung hoà `ct_*` (đưa về 1) **làm xấu thêm** (0,267). Vậy `ct_*` vượt khoảng không phải nguyên nhân.

Thất bại là **phân tán trên nhiều feature**, đúng như khi khái niệm "tấn công" khác nhau giữa hai miền. Không có một lỗi ánh xạ đơn lẻ nào để sửa.

---

## 9. KẾT LUẬN

| Mục tiêu | Trạng thái |
|---|---|
| Tải 5G-NIDD | ✅ Fairdata, CC BY 4.0, 4 tệp CSV, đã kiểm hash |
| Đối chiếu từng feature của hai bộ | ✅ §3 (định nghĩa, nguồn, phép biến đổi, bằng chứng), §4 (phân bố, KS, chẩn đoán), §10 (toàn bộ 52 cột 5G-NIDD) |
| **5G-NIDD cross-validate được bằng model hiện tại** | ✅ **Đạt.** `5gnidd_unsw31.parquet` khớp schema 31 feature; 83% importance ánh xạ chính xác, theo công thức đã kiểm, hoặc hiệu chỉnh có bằng chứng; round-trip chỉ mất 0,007 ROC-AUC |
| Model hiện tại phát hiện tốt trên 5G | ❌ ROC-AUC 0,40, bal acc 0,45. Hiệu chỉnh ngưỡng bằng nhãn 5G cũng không cứu được |

**Không nên** báo cáo rằng model "đã được kiểm chứng trên 5G". Cách nói đúng: *"Model UNSW-NB15 được cross-validate trên 5G-NIDD theo ánh xạ feature đã kiểm chứng; nó không tổng quát hoá sang mạng 5G (ROC-AUC 0,40), vì tấn công và lưu lượng lành tính của hai bộ khác nhau về bản chất."* Đây vẫn là một kết quả có giá trị, cùng hướng với phát hiện của NB07 về lệch phân bố, nhưng ở mức nặng hơn nhiều.

### Khuyến nghị

1. **Muốn có IDS cho 5G thì phải học trên dữ liệu 5G.** Tập `5gnidd_unsw31.parquet` có sẵn cột `bs`, nên có thể làm ngay thí nghiệm E3 trong kế hoạch: train BS1 → test BS2 và ngược lại. Chia theo trạm chứ không chia ngẫu nhiên.
2. **Trong mọi thí nghiệm trên 5G-NIDD**, phải loại 281.529 bản sao (§5.1) và khử trùng lặp. Nếu không, lớp Benign bị nhiễm 59% tấn công, và có rò rỉ giữa hai trạm.
3. Nếu vẫn muốn một model dùng chung hai miền, hãy thử E5: train gộp UNSW + 5G-BS1, test trên BS2. Bỏ các feature chỉ mang tính "dấu vân tay môi trường": `ackdat`/`synack`/`tcprtt` (độ trễ), `stcpb`/`dtcpb` (số ngẫu nhiên).
4. Nếu cần `sinpkt`/jitter chính xác thay vì xấp xỉ, có thể chạy lại Argus (có bật jitter) trên pcap đã bóc GTP (≈ 3,8 GB) bằng WSL. Tuy nhiên round-trip cho thấy phần này chỉ đáng khoảng 0,01 ROC-AUC, không đổi kết luận.
5. Cập nhật slide và báo cáo: nếu nhắc tới 5G, dùng con số ở §7.1, kèm ghi chú phương pháp ở §3.

---

## 10. PHỤ LỤC — TOÀN BỘ 52 CỘT CỦA `Combined.csv` VÀ VAI TRÒ

| Cột 5G-NIDD | Vai trò trong ánh xạ | Ghi chú |
|---|---|---|
| `Unnamed: 0`, `Seq`, `Offset` | Bỏ: metadata | Vị trí trong file; `Seq`/`Offset` đứng đầu ANOVA của bài báo gốc nên là rủi ro rò rỉ |
| `Dur` | → `dur`; đầu vào cho `sinpkt`, `dinpkt`, `sload`, `dload` | |
| `RunTime`, `Mean`, `Sum`, `Min`, `Max` | Không dùng | Thống kê thời lượng bản ghi Argus; UNSW không có |
| `Proto` | → `proto`, `swin`, `dwin`, `service` | |
| `sTos`, `dTos`, `sDSb`, `dDSb` | Không dùng | UNSW không có |
| `sTtl`, `dTtl`, `sHops`, `dHops` | **Bỏ: ô nhiễm** | `sttl`/`dttl` đã bị NB01 loại (D'hooge 2022); hops suy ra từ TTL |
| `Cause` | Không dùng | Lý do Argus xuất bản ghi (Start/Status) |
| `TotPkts`, `TotBytes` | Không dùng | = src + dst |
| `SrcPkts`, `DstPkts` | → `spkts`, `dpkts` | |
| `SrcBytes`, `DstBytes` | → `sbytes`, `dbytes` (−14 byte/gói) | |
| `sMeanPktSz`, `dMeanPktSz` | Thay bằng tính lại → `smean`, `dmean` | Giá trị gốc còn chứa Ethernet |
| `Load`, `SrcLoad`, `DstLoad` | Thay bằng tính lại → `sload`, `dload` | Đã kiểm công thức khớp 100% |
| `Loss`, `pLoss` | Không dùng | |
| `SrcLoss`, `DstLoss` | Chỉ dùng trong biến thể "thô" | Ngữ nghĩa khác `sloss` của UNSW (§3 #12) |
| `SrcGap`, `DstGap` | Không dùng | UNSW không có |
| `Rate` | → `rate` | Công thức khớp 100% |
| `SrcRate`, `DstRate` | Không dùng | |
| `State` | → `state` (UDP REQ → INT) | |
| `SrcWin`, `DstWin` | Chỉ dùng trong biến thể "thô" | Giá trị thật, khác thang 0/255 của UNSW |
| `sVid`, `dVid` | Không dùng | VLAN |
| `SrcTCPBase`, `DstTCPBase` | → `stcpb`, `dtcpb` | |
| `TcpRtt`, `SynAck`, `AckDat` | → `tcprtt`, `synack`, `ackdat` | |
| `Label` | → `label` (Malicious = 1) | |
| `Attack Type` | → `attack_cat` | |
| `Attack Tool` | → `attack_tool` (meta) | |

Lấy thêm từ `BTS1_BTS2_fields_preserved.csv` (không có trong `Combined.csv`):

| Cột | Dùng cho |
|---|---|
| `SrcAddr`, `DstAddr` | `ct_src_ltm`; phát hiện bản sao bắt nhầm (§5.1). Không đưa vào model |
| `Dport` | `service`, `ct_src_dport_ltm` |
| `SAppBytes`, `DAppBytes` | Đã kiểm: = 0 mọi dòng, **không dùng được** |
| `SIntPkt`, `DIntPkt`, jitter | Đã kiểm: rỗng 100%, **không dùng được** |

---

## 11. GIỚI HẠN

- `ct_src_ltm`/`ct_src_dport_ltm` dùng thứ tự dòng thay cho thời gian, vì `StartTime` bị cắt còn `mm:ss`. Đây là hai feature duy nhất không kiểm chứng được bằng round-trip (UNSW đã làm sạch không còn IP/cổng). Chẩn đoán §8.2 cho thấy trung hoà chúng không cải thiện kết quả.
- `service` dựa trên cổng, còn Bro nhận diện theo payload. Với HTTPFlood/Slowrate (cổng 80, bắt tay xong) thì hai cách cho kết quả như nhau. Với lưu lượng mã hoá trên cổng lạ thì có thể khác.
- Bảng tra `sloss`/`dloss` và model hồi quy jitter học từ UNSW-**train** và không dùng nhãn. Chúng chuyển "ngữ nghĩa UNSW" sang 5G; kiểm chứng round-trip ở §3.
- Model đánh giá là RF 31 feature. Cấu hình RF 39 feature (NB05/NB07) cần `sttl`/`dttl`, vừa là feature ô nhiễm vừa không fit lại được, nên không đánh giá.
- 5G-NIDD chỉ có DoS và scan. Kết quả này không nói gì về Exploits, Fuzzers, Backdoor… trên 5G.
