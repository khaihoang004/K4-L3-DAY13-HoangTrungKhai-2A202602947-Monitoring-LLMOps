# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Kết quả được đối chiếu với code, workload mới, Langfuse API và ảnh evidence. Ảnh đã được bổ sung ngày 30/09/2026; mục 2 ghi rõ ảnh phù hợp và ảnh cần thay/chụp lại trước khi nộp.

## 1. Thông tin học viên

- **Họ và tên:** Hoàng Trung Khải (suy ra từ tên repository; học viên kiểm tra lại dấu).
- **MSSV:** 2A202602947.
- **Lớp:** K4-L3A.
- **Repository URL:** https://github.com/khaihoang004/K4-L3-DAY13-HoangTrungKhai-2A202602947-Monitoring-LLMOps
- **Commit SHA cuối:** **CẦN BỔ SUNG sau khi commit/push**. HEAD khi bắt đầu kiểm tra: `786e55c5b2fad503d57da95e3ff0de7ed55fea1f`; không dùng SHA này để đại diện cho thay đổi chưa commit.
- **Challenge ID theo report hiện có:** `day13-k4-l3a-monitoring-llmops-v1`; cần xác nhận đã được mở chính thức.
- **Project Langfuse yêu cầu:** `day13-k4-l3a-2A202602947`.
- **Project API thực tế:** `day13-k4-l3a-2A202602947`, ID `cmumgxbul00uzad0er8e65lfm`. Học viên đã đổi tên và API đã xác nhận; IDs/evidence vẫn thuộc cùng project.

## 2. Evidence index

| Evidence | Đường dẫn thực tế / trạng thái |
|---|---|
| Baseline | [00-baseline.txt](evidence/00-baseline.txt) |
| Pytest cuối | [01-pytest.txt](evidence/01-pytest.txt) |
| Log validator | [02-log-validator.txt](evidence/02-log-validator.txt) |
| Dashboard validator | [03-dashboard-validator.txt](evidence/03-dashboard-validator.txt) |
| Structured log | [04-structured-log.png](evidence/04-structured-log.png) |
| PII redaction | [05-pii-redaction.png](evidence/05-pii-redaction.png) |
| Trace list | [06-trace-list.png](evidence/06-trace-list.png), [kiểm chứng qua API](evidence/06-trace-verification.txt) |
| Trace waterfall | [07-trace-waterfall.png](evidence/07-trace-waterfall.png) |
| Trace metadata | [08-trace-metadata.png](evidence/08-trace-metadata.png) — cần che public key; [usage/cost và metadata API](evidence/17-langfuse-observations.json) |
| Prompt versions | [09-prompt-versions.png](evidence/09-prompt-versions.png), [cặp trace cùng input](evidence/09-prompt-comparison.json) |
| Promote production v2 | [10a-production-v2.png](evidence/10a-production-v2.png) — **cần chụp lại: ảnh hiện là candidate v2** |
| Production sau rollback | [10b-rollback-v1.png](evidence/10b-rollback-v1.png) — thấy production v1 ở lượt chạy mới; cần che public key |
| Dashboard runtime | [11-dashboard-overview.png](evidence/11-dashboard-overview.png) |
| Incident metric | [12-incident-metric.png](evidence/12-incident-metric.png) |
| Incident log | [13-incident-log.png](evidence/13-incident-log.png) |
| Incident trace và correlation | [14b-incident-correlation.png](evidence/14b-incident-correlation.png) — đúng trace, có duration và correlation ID; cần che public key |
| Ảnh incident không dùng để đối chiếu request | [14a-incident-waterfall.png](evidence/14a-incident-waterfall.png) — đang mở trace khác; dùng ảnh 14b cho request trong mục 7 |
| Workload mới | [15-load-test.txt](evidence/15-load-test.txt) |
| Response headers | [16-response-headers.txt](evidence/16-response-headers.txt) |
| Observations đã loại key | [17-langfuse-observations.json](evidence/17-langfuse-observations.json) |
| Metrics lượt cuối | [18-metrics-summary.json](evidence/18-metrics-summary.json) |

Các ảnh logs thay thế các file `04`, `05`, `13` dạng `.txt` đã không còn trong thư mục evidence. Ảnh `08`, `10b` và `14b` còn hiển thị `scope.attributes.public_key`; cần che trường này hoặc chụp lại vùng cần thiết theo quy định evidence của bài lab. Không chỉnh sửa giá trị metric, label, trace ID hoặc correlation ID.

## 3. Kết quả kỹ thuật

Baseline trong bảng là trạng thái repo khi bắt đầu lượt hỗ trợ này, không phải kết quả starter chưa sửa. Log cũ đã được đổi tên `data/logs.before-final-*.jsonl` và API đã được khởi động lại trước workload mới; archive nằm ngoài Git.

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 100/100, 121 records | 100/100, 49 records, 24 correlation IDs | Đọc toàn bộ file mới |
| `validate_dashboard.py` | 6/6 | 6/6 | Có ảnh runtime riêng |
| `pytest` | 25 passed | 29 passed | Có regression PII lồng nhau và dashboard rỗng/chỉ có lỗi |
| Số traces hợp lệ | Chưa đo baseline | 24 traces mới có root và 2 children | Đối chiếu parent IDs và correlation IDs qua API |
| Số PII leak | 0 trong log baseline | 0 trong log mới; 0 phát hiện trong input/output observations đã kiểm tra | Regex không bảo đảm nhận diện mọi loại PII |
| Latency P95 / TTFT P95 | Chưa lưu riêng | 151.85 ms / 50 ms | TTFT do FakeLLM báo, không phải end-to-end streaming TTFT |
| Retrieval success rate | Chưa lưu riêng | 100% (24/24) | Runtime đã tính cả record thất bại |
| Error / cost | Chưa lưu riêng | 0/24 lỗi; $0.049821 | Cost là ước lượng FakeLLM |

Cửa sổ đo mới: `2026-09-29T16:46:23.390500Z`–`16:46:47.506138Z`. Ảnh dashboard xem 60 phút gần thời điểm chụp.

## 4. Logging và PII

- **Correlation ID:** [middleware](../app/middleware.py) clear context mỗi request, nhận `x-request-id` nếu có; nếu thiếu sinh `req-` + 8 hex. ID được bind vào context, đặt trong request state, truyền xuống agent và trả qua response header. `x-response-time-ms` dùng đồng hồ monotonic `perf_counter`.
- **Metadata:** [main.py](../app/main.py) bind `user_id_hash`, `session_id`, `feature`, `model`, `env` trước `request_received`; log có `ts`, `level`, `service`, `event`, `correlation_id`. Response thêm latency, TTFT, token, cost, quality và retrieval status.
- **PII:** [pii.py](../app/pii.py) che email (cả alias `+`), điện thoại Việt Nam dạng `0`/`+84` có dấu cách/chấm/gạch, CCCD 12 số và thẻ 13–19 số. Xử lý thẻ trước điện thoại để tránh chỉ che một phần số thẻ. User ID được SHA-256 rồi lấy 12 hex; đây là pseudonym hóa để nối sự kiện, không phải cam kết ẩn danh tuyệt đối.
- **Thứ tự processors:** merge context → timestamp/level → stack/exception formatting → scrub đệ quy string trong dict/list → file writer → JSON renderer. Do scrub sau exception formatting nên cả exception và payload lồng nhau cũng được xử lý.
- **Kiểm chứng:** 4 request PII giả riêng từng loại, kiểm tra log đã che và headers khớp JSON response; validator dùng detector độc lập. [Tests](../tests/test_pii.py) và [observability tests](../tests/test_chat_observability.py) kiểm chứng các hành vi trên. Giá trị PII thô không được đưa vào evidence.

## 5. Tracing và prompt versioning

- **Nguồn trace:** 24 request mới do API local tạo, IDs khớp logs. [API export](evidence/17-langfuse-observations.json) chỉ giữ metadata cần thiết, bỏ public key/resource metadata và raw input/output. Ảnh [trace list](evidence/06-trace-list.png) và [metadata](evidence/08-trace-metadata.png) đã được bổ sung từ project cá nhân.
- **Cấu trúc:** [LabAgent.run](../app/agent.py) có root `lab-agent-run` kiểu agent; `knowledge-retrieval` kiểu retriever và `fake-llm-generation` kiểu generation là children trực tiếp. Generation có model, managed prompt, usage input/output/total và cost. Root không auto-capture raw input/output; previews được scrub.
- **Nối log–trace:** tìm `metadata.correlation_id` đúng `correlation_id` trong log. User hash, session, feature/model và environment truyền xuống observations.
- **Prompt name:** `day13-chat`. v1 giữ `Feature={{feature}}`, `Docs={{docs}}`, `Question={{message}}`; v2 thêm câu `Answer in no more than three concise bullet points.` trước ba biến. Nội dung hai version đã đọc lại qua API.
- **Labels đã xác minh:** v1 có `baseline`, `production`; v2 có `candidate`, `latest`. Những trace `local-v1` cũ không được dùng để chứng minh versioning.

| Bước | Label / version | Trace ID đã xác minh | Thời gian UTC |
|---|---|---|---|
| Baseline | baseline / 1 | `b72794e8be52963e5ea8a9862bcc3592` | 09:43:42 |
| Candidate | candidate / 2 | `c6c15216f1bfa4f7724cb7ae92b70e1b` | 10:14:44 |
| Promote | production / 2 | `215a52888bd94718b90e1d6977fb7559` | 10:20:36 |
| Rollback | production / 1 | `490863aaea550e5f00b904dc532a6053` | 10:23:27 |

Các trace trên thuộc lịch sử ngày 2026-09-29, đã đọc lại từ API. Trạng thái hiện tại `production → v1` cũng được xác minh bằng prompt API. Khi chuyển label, restart API để bỏ cache rồi chạy cùng workload theo [PROMPT_VERSIONING](../docs/PROMPT_VERSIONING.md). Hai trace baseline/candidate có cùng session `s10` và cùng query đầy đủ `How should alerts be designed?` (ngắn hơn giới hạn preview), xem [so sánh prompt](evidence/09-prompt-comparison.json). Ảnh [prompt versions](evidence/09-prompt-versions.png) đã có. Ảnh [10b](evidence/10b-rollback-v1.png) thực tế chụp trace `afae55ff4274f502b75e7b8ecd94d429` lúc `16:46:47 UTC`, cho thấy `production / 1` vẫn được sử dụng sau rollback; đây là trace khác với trace rollback lịch sử trong bảng. **Cần thay ảnh [10a](evidence/10a-production-v2.png):** ảnh hiện chụp trace `46628ea7a50cea96528742afee234fdd`, label `candidate / 2`, nên chưa chứng minh promote `production / 2`. Trace promote đúng trong bảng đã được kiểm chứng qua API.

## 6. Dashboard, SLO và alerts

[Dashboard Streamlit](../scripts/dashboard.py) đọc JSONL theo [contract](../config/dashboard.yaml), có đúng sáu panel, cửa sổ 60 phút và threshold lines:

| Panel | Nội dung / đơn vị | Threshold |
|---|---|---|
| Latency | P50/P95/P99, TTFT P95 / ms | P95 ≤ 2.000 ms |
| Traffic | Request count và requests/min | ≥ 1 request/min (guardrail workload lab) |
| Errors | Error rate, breakdown; retrieval success / % | Error ≤ 2%; retrieval ≥ 90% |
| Cost | Cost/min và tổng cửa sổ / USD | Tổng 60 phút ≤ $2.50 |
| Tokens | Tổng input/output riêng / tokens | Mỗi chuỗi ≤ 50.000 |
| Quality | Mean heuristic score / 0–1 | ≥ 0.75 |

- **SLO:** [slo.yaml](../config/slo.yaml), 99,5% request thành công trong ≤2 giây trên cửa sổ 28 ngày. Ngưỡng 2 giây cao hơn baseline ~0,15 giây nhưng phát hiện retrieval delay ~2,5 giây. Ngưỡng 3 giây trước đó bỏ sót incident này nên đã chỉnh thống nhất YAML/dashboard/runbook. Đây là hiệu chỉnh cho lab, cần baseline production để chọn mục tiêu thật.
- **Error budget:** `total × (1 − 0.995) = total × 0.005`; 1.000 request cho phép 5 request xấu. `bad = total − good`; budget còn lại = `0.005 × total − bad`; budget consumed = `bad / (0.005 × total) × 100%`. Lượt mới 24 request, bad=0, budget thống kê=0,12 request, consumed=0%; mẫu lab ngắn không chứng minh đạt SLO 28 ngày. 201,6 phút chỉ là quy đổi availability tương đương trên 28 ngày, không thay cho request-based SLI.
- **Ba alert:** latency P95 >2.000 ms trong 5 phút, critical, `llmops-on-call`; error rate >2% trong 5 phút (≥20 samples), critical, `api-on-call`; retrieval success <90% trong 10 phút (≥10 samples), warning, `retrieval-on-call`. Tất cả khai báo Slack `#llmops-alerts` và [runbook](../docs/alerts.md) tương ứng trong [alert_rules.yaml](../config/alert_rules.yaml).
- **Giới hạn:** alert mới ở mức contract/runbook, chưa có evaluator hoặc Slack delivery. P95 alert là triệu chứng latency, không phải phép tính burn-rate. Cost panel 60 phút không thay thế daily cost guardrail. Quality heuristic không phải đánh giá chất lượng ngữ nghĩa độc lập.

## 7. Điều tra challenge

Dữ liệu dưới đây có sẵn từ lượt chạy trước và đã được đối chiếu lại với logs/observations API; không chạy lại challenge trong lượt hoàn thiện này. **Cần học viên xác nhận lượt chạy đã được Lab Coach cho phép.** Không đọc lại hay đưa nội dung `config/challenge.json` vào evidence.

Evidence: [metric runtime lịch sử](evidence/12-incident-metric.png) → [log request](evidence/13-incident-log.png) → [trace và correlation ID](evidence/14b-incident-correlation.png); duration chính xác được đối chiếu thêm trong [observations API đã loại key](evidence/17-langfuse-observations.json). Ảnh 14b hiển thị root ~2,66 s, retrieval ~2,50 s và generation 152 ms, cùng `req-f767c9bf`. Ảnh 14a đang mở trace `46628ea7a50cea96528742afee234fdd`, correlation ID `req-4ba7dbb4`, nên không dùng làm bằng chứng cho request được chọn ở đây.

Ảnh metric là **Historical replay** của log gốc đã lưu, cửa sổ `09:41–10:41 UTC`, lọc session prefix `k4-l3a-challenge`; không sửa timestamp hay tạo lại dữ liệu. Khoảng request thực tế nằm bên trong cửa sổ đó.

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** `2026-09-29 10:40:33–10:40:46 UTC` (request window)
- **Triệu chứng từ metrics:** panel latency, feature `monitoring`; 5/5 request vượt ngưỡng 2,000 ms, P95 = 2,657.2 ms (nội suy tuyến tính; dashboard làm tròn 2,657 ms), P50 = 2,654 ms, TTFT P95 = 50 ms. Không có request lỗi; retrieval success = 100%.
- **Log line và correlation ID liên quan:** `request_received` / `response_sent` lúc `2026-09-29T10:40:33.165995Z`–`10:40:35.835633Z`; correlation ID `req-f767c9bf`, latency `2,658 ms`, `tool_success=true`.
- **Trace ID và span gây ảnh hưởng:** `ca0c54ea93d38503f76cc9171ae6f371`; `knowledge-retrieval` child span `2.505 s` (parent `62573ac3dac25d1d`), so với `fake-llm-generation` `0.152 s`. Root span `lab-agent-run` dài `2.663 s` và có cùng correlation ID.
- **Root cause:** độ trễ nằm trong bước retrieval; trace cho thấy retriever chiếm khoảng 94% tổng thời gian root, còn generation gần mức nền. Metrics, log và trace cùng xác nhận latency cao không đến từ LLM generation.
- **Fix action:** tắt incident sau khi thu thập evidence; nếu xảy ra trong production, giới hạn timeout retrieval và trả kết quả fallback có kiểm soát thay vì giữ request chờ.
- **Preventive measure:** duy trì histogram/percentile riêng cho retriever, alert theo retrieval latency và SLO; giữ correlation ID trong root/child metadata để phân biệt retrieval với generation khi điều tra.

## 8. Giải thích và tự đánh giá

Phần giải thích dưới đây bám theo thay đổi và evidence trong repo; học viên cần đọc lại, chỉnh theo trải nghiệm của mình trước khi nộp.

- **Quyết định kỹ thuật:** scrub tập trung sau exception formatting và trước mọi writer để tránh payload lồng nhau hoặc exception bỏ qua redaction; giữ cùng correlation ID xuyên logs/traces.
- **Lỗi tìm được:** dashboard chỉ dùng `response_sent` để tính retrieval success nên không đếm retrieval failures; dashboard rỗng còn có thể truy cập cột không tồn tại. Đã tính trên mọi record có `tool_success` và xử lý cửa sổ rỗng; kiểm chứng runtime bằng trình duyệt và regression test.
- **Blocker evidence:** API legacy `/api/public/traces` trả 410 với tổ chức Langfuse mới; dùng `/api/public/v2/observations` và fields phù hợp để đối chiếu. Ảnh UI đã được bổ sung thủ công; khi đối chiếu thấy ảnh 10a dùng label candidate thay vì production, nên cần chụp lại đúng trace promote.
- **Metrics → Logs → Traces:** metrics chỉ ra lúc nào/tín hiệu nào bất thường; logs chọn request cụ thể; correlation ID dẫn sang trace để so sánh child spans. Incident đã có cho thấy retrieval chiếm khoảng 94% root duration, trong khi generation vẫn ~0,15 giây.
- **Vận hành LLM:** prompt version/label giúp truy vết thay đổi và rollback; token/cost kiểm soát chi phí; SLO xác định mức ảnh hưởng người dùng và budget cho phép. Không suy nguyên nhân từ một metric đơn lẻ.
- **Điều rút ra:** validator pass chỉ chứng minh một phần contract. Cần kiểm tra dữ liệu thật, mẫu số metrics, quan hệ cha–con và evidence cùng request; ảnh runtime phải khớp code/config cuối.
- **Phần chưa hoàn thành:** thay ảnh promote 10a đúng production v2; che public key trong ảnh; xác nhận mở challenge; ghi SHA cuối, commit/push và nộp LMS. Ảnh incident 14b đã nối đúng metric/log/trace; ảnh 14a không được dùng cho request này.

## 9. Checklist và cách nộp

- [x] Lưu baseline, đổi tên log cũ, restart API và chạy workload mới.
- [x] Log validator đạt ≥80, dashboard contract 6/6, headers hợp lệ, không phát hiện PII leak.
- [x] Có 24 traces mới với root/retrieval/generation qua API.
- [x] Có ảnh dashboard runtime sáu panel và metric incident lịch sử.
- [x] Đối chiếu metric → log `req-f767c9bf` → trace incident.
- [x] Tên project cá nhân đúng mẫu, đã xác minh qua API.
- [ ] Xác nhận họ tên và Lab Coach đã mở challenge.
- [x] Bổ sung ảnh `04`, `05`, `06`–`10`, `13`, `14` theo mục 2; không chụp API Keys hoặc metadata chứa key.
- [x] Kết quả/evidence thuộc source cuối; tất cả ảnh/links mở được trên GitHub.
- [x] Học viên đọc lại và tự xác nhận phần giải thích trong báo cáo.
- [x] Kiểm tra staged diff không có `.env`, raw logs, challenge, secrets hoặc PII.
- [x] Commit/push repo và nộp URL + SHA trên VLearn LMS/Codelabs.

