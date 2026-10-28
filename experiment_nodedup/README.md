# experiment_nodedup — làm sạch KHÔNG bỏ dòng trùng

Thư mục này **độc lập hoàn toàn** với phần còn lại của project.

- Chỉ **đọc** `../data/raw/` và `../data/cleaned/` (tập đánh giá đối chứng) và
  `../models/random_forest_v2_metrics.json` (để lấy đúng bộ siêu tham số của lần 2).
- **Không ghi** bất cứ thứ gì ra ngoài `experiment_nodedup/`.
- `../notebooks/`, `../data/cleaned/`, `../models/`, `../reports/` không bị động tới.

## Câu hỏi của thực nghiệm

Vấn đề nằm ở **dữ liệu** hay ở **thuật toán train**?

Để quy được trách nhiệm, thuật toán phải **giữ nguyên tuyệt đối**: cùng cấu hình
Random Forest, cùng tiền xử lý, cùng cách chia, cùng seed, cùng chỉ số. Thứ duy
nhất thay đổi là bộ dữ liệu huấn luyện. Nếu đổi cả hai cùng lúc thì không kết luận
được gì.

## Các biến thể làm sạch

Đều bỏ `id`, thu nhỏ kiểu dữ liệu, bỏ 8 cột ô nhiễm (`sttl`, `dttl`,
`ct_state_ttl`, `ct_dst_ltm`, `ct_srv_dst`, `ct_dst_src_ltm`, `ct_srv_src`,
`ct_dst_sport_ltm`) và 3 cột không phân biệt được — **giống hệt notebook 01**.
Khác nhau ở bước xoá dòng:

| Biến thể | Bỏ dòng trùng | Bỏ dòng mâu thuẫn | Dùng để |
|---|---|---|---|
| `V1_nodedup` | **không** | có | Biến thể chính — đúng yêu cầu "không xoá dòng trùng" |
| `V2_nodedup_nocontra` | **không** | **không** | Biến thể cực đoan, không xoá dòng nào |
| `V0_official_recipe` | có | có | Đối chứng — phải tái lập đúng `../data/cleaned` |

`V0` tồn tại để tự kiểm tra: hàm làm sạch ở đây phải dựng lại **trùng khít từng giá
trị** với bộ cleaned chính thức. Nếu assert đó fail thì mọi so sánh phía sau vô nghĩa.

## Hai cách đánh giá

Kết quả chỉ đọc được nếu phân biệt rạch ròi hai cách:

- **(A) Native** — đánh giá trên tập test *không khử trùng lặp*. Đây là con số mà
  một nhóm sẽ nhận được nếu họ đơn giản bỏ qua bước khử trùng lặp.
- **(B) Đối chứng** — đánh giá trên **đúng 25.284 dòng `test-final` chính thức** mà
  mọi thực nghiệm trước đã dùng. Vì tập đánh giá giữ nguyên, khác biệt duy nhất là
  dữ liệu huấn luyện.

Cách (B) mới là cách trả lời được câu hỏi. Cách (A) dùng để cho thấy vì sao bỏ bước
khử trùng lặp lại nguy hiểm.

## Cấu trúc

```
experiment_nodedup/
├── README.md
├── data/cleaned_nodedup/     parquet của các biến thể + file chia test
├── notebooks/                notebook làm sạch và notebook chạy model
├── models/                   model đã fit trong thực nghiệm này
└── reports/                  số liệu JSON/CSV và báo cáo
```

## Tái chạy

```
python notebooks/... # xem notebook, chạy tuần tự từ trên xuống
```

Seed cố định 42 ở mọi bước chia dữ liệu và mọi model.
