# Dựng và kiểm tra dashboard

[`../config/dashboard.yaml`](../config/dashboard.yaml) là contract chấm điểm, không phụ thuộc việc bạn dựng dashboard trong Langfuse hay một công cụ local. File này quy định đúng nguồn dữ liệu, phép tổng hợp, đơn vị và threshold cho sáu panel.

Trường `query` trong YAML là pseudocode mô tả phép tính, không phải câu lệnh để copy nguyên vào mọi công cụ. Bạn chuyển cùng logic đó sang cú pháp của công cụ đã chọn.

## Mapping dữ liệu

| Panel | Event/field | Phép tổng hợp |
|---|---|---|
| Latency | `response_sent.latency_ms/ttft_ms` | latency P50/P95/P99 và TTFT P95 |
| Traffic | `request_received` | count, request/phút |
| Errors | `request_received`, `request_failed`, `error_type`, `tool_success` | error rate, breakdown và retrieval success |
| Cost | `response_sent.cost_usd` | tổng theo phút và toàn cửa sổ |
| Tokens | `response_sent.tokens_in/tokens_out` | tổng theo từng field |
| Quality | `response_sent.quality_score` | mean |

Giữ time range mặc định 60 phút, refresh 30 giây và hiển thị threshold/SLO line. Giá trị chính xác nằm trong `config/dashboard.yaml`; không tự đổi contract chỉ để ảnh dashboard đẹp hơn.

## Cách dựng

1. Hoàn thiện logging/PII và chạy API.
2. Chạy `python scripts/load_test.py --concurrency 5` để tạo baseline.
3. Chạy dashboard local từ repo root:

	```bash
	streamlit run scripts/dashboard.py
	```

	App đọc `data/logs.jsonl` và `config/dashboard.yaml`, tự refresh theo config và dựng đúng sáu panel. Nếu cần đổi cổng API cho workload, đặt `BASE_URL`, ví dụ `BASE_URL=http://127.0.0.1:8001 python scripts/load_test.py`. Langfuse vẫn là nơi mở trace/prompt version để điều tra sâu.
4. Đặt tên panel, đơn vị và threshold giống contract.
5. Chạy validator:

```bash
python scripts/validate_dashboard.py
```

Validator kiểm tra cấu trúc contract; nó không thể chứng minh biểu đồ trong ảnh dùng đúng dữ liệu. Evidence runtime vẫn bắt buộc.

## Cách kiểm tra runtime

1. Lưu ảnh baseline và giá trị P95/error/cost hiện tại.
2. Bật một incident practice, ví dụ `python scripts/inject_incident.py --scenario rag_slow`.
3. Chạy lại load test với cùng input và concurrency.
4. Xác nhận panel liên quan thay đổi theo đúng hướng; với `rag_slow`, P95 phải tăng rõ ràng.
5. Lọc log chậm, lấy correlation ID rồi mở trace có cùng ID.
6. Tắt incident bằng `python scripts/inject_incident.py --scenario rag_slow --disable`.

Ảnh dashboard phải nhìn được tên panel, time range, đơn vị và threshold. Báo cáo phải dẫn lại trace ID hoặc log line dùng để giải thích thay đổi.

## Xem lại incident đã lưu

Có thể dùng `DASHBOARD_LOG_PATH=data/logs.before-final-<timestamp>.jsonl` để mở
bản log được lưu trước khi chạy workload cuối. Thêm query string
`?end=2026-09-29T10:41:00Z&session_prefix=k4-l3a-challenge` để xem cửa sổ
60 phút kết thúc ở thời điểm incident, lọc đúng session. Dashboard hiển thị
rõ **Historical replay**, tên nguồn và mốc UTC; không sửa timestamp trong log.
Không commit file log archive; chỉ nộp evidence đã kiểm tra PII.
