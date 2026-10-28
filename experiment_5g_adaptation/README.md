# experiment_5g_adaptation — Kế hoạch A: cho model thích nghi với 5G bằng nhãn 5G

Kế hoạch đầy đủ (input, output, kỳ vọng, tiêu chí): [`docs/Ke_hoach_A_hoc_co_nhan_5G.md`](docs/Ke_hoach_A_hoc_co_nhan_5G.md)

## Cấu trúc

```
experiment_5g_adaptation/
├── README.md                     tệp này
├── docs/                         kế hoạch
├── src/                          một script cho mỗi bước: A1_model_gop.py, A2_few_shot.py, A3_loao.py, (A4_dong_goi.py)
├── results/
│   ├── A1_model_gop/             mỗi bước có cùng 3 thư mục con:
│   ├── A2_few_shot/                tables/  bảng số liệu (.csv) và kết quả máy đọc (.json)
│   └── A3_loao/                    figures/ hình (.png) · logs/ log lần chạy chính thức
├── models/
│   └── A1_model_gop/             model được chọn (.joblib)
└── reports/                      báo cáo từng bước, so với kỳ vọng
```

## Trạng thái

| Bước | Script | Kết quả | Báo cáo | Trạng thái |
|---|---|---|---|---|
| A1 Model gộp | `src/A1_model_gop.py` | `results/A1_model_gop/` | `reports/Bao_cao_A1.md` | ✅ Đã chạy |
| A2 Đường cong số nhãn | `src/A2_few_shot.py` | `results/A2_few_shot/` | `reports/Bao_cao_A2.md` | ✅ Đã chạy |
| A3 Leave-one-attack-out | `src/A3_loao.py` | `results/A3_loao/` | `reports/Bao_cao_A3.md` | ✅ Đã chạy |
| A4 Đóng gói | — | — | — | ⏳ Chưa làm |
| A5 Tự sinh nhãn (tuỳ chọn) | — | — | — | ⏸ Cần testbed |

## Chạy lại

```bash
python -I -X utf8 experiment_5g_adaptation/src/A1_model_gop.py <thư mục dự án>          # bản đầy đủ, ~12 phút
python -I -X utf8 experiment_5g_adaptation/src/A2_few_shot.py <thư mục dự án>           # ~50 phút
python -I -X utf8 experiment_5g_adaptation/src/A3_loao.py <thư mục dự án>               # ~20 phút
QUICK=1 python -I -X utf8 experiment_5g_adaptation/src/<script>.py <thư mục dự án>     # thử nhanh, 40 cây
```

**Input (chỉ đọc, không sửa):**
- `experiment_5gnidd/data/cleaned/5gnidd_unsw31.parquet`, sinh bởi `experiment_5gnidd/src/01_lam_sach_5gnidd.py`
- `data/cleaned/UNSW_NB15_{training,testing}-set.parquet`
- `data/cleaned/test_split_v3.csv`
- `reports/exp05/rf_A_trainfit.joblib` (model NB07)

Mọi thứ ghi ra chỉ nằm trong thư mục này.
