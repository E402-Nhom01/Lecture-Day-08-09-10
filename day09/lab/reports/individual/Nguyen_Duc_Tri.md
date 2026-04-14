# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Đức Trí
**Vai trò trong nhóm:** Trace & Docs Owner
**Ngày nộp:** 14/04/2026
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

**Module/file tôi chịu trách nhiệm:**
- File chính: `docs/routing_decisions.md`, `docs/single_vs_multi_comparison.md`, `reports/group_report.md`

**Cách công việc của tôi kết nối với phần của thành viên khác:**
Tôi chịu trách nhiệm phân tích vòng đời luồng chạy từ Orchestrator (Supervisor) do một bạn khác làm, đồng thời thu thập các log input/output tạo ra từ các Worker (Retrieval, Policy, Synthesis) và gọi MCP. Tôi phải thiết lập contract chuẩn (JSON schema trace) để mọi người có thể push log vào `artifacts/traces/`, từ đó tôi đọc data để tính Metrics (Latency, Confidence, Routing accuracy) cho cả nhóm. 

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**
Commit hash: `#7f8e9a2` - Feat(trace): Implement analyze_trace and update doc templates.
---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Thống nhất định dạng lưu Trace file thành dạng JSONL (`.jsonl`) thay vì JSON array thông thường.

**Lý do:**
Với cấu trúc pipeline phức tạp và phải lưu log liên tục, việc dùng JSON array nguyên khối sẽ khiến quá trình ghi gặp rủi ro nếu tiến trình bị crash giữa chừng, gây mất trắng toàn bộ trace log của các câu hỏi đã xử lý xong trước đó. Dùng `JSONL` (JSON Lines) với mỗi dòng là một JSON object của một `run_id` cho phép ghi append (nối tiếp) một cách an toàn và độc lập. Điều này cũng rút ngắn rất nhiều thời gian deserialize khi phân tích hàng loạt bằng pandas. 

**Trade-off đã chấp nhận:**
JSONL khó format thụt lề trực tiếp bằng mắt (pretty-print) như JSON thông thường, đòi hỏi người xem trace phải dùng script helper hoặc tool chuyên dụng định dạng khi muốn debug thủ công.

**Bằng chứng từ trace/code:**
```python
# Đoạn code ghi trace trong eval_trace.py
def append_trace_log(trace_data):
    with open("artifacts/traces/trace_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(trace_data, ensure_ascii=False) + "\n")
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** Hàm tính toán Metric bị ném lỗi `KeyError: 'route_reason'` khi phân tích log của nhóm câu hỏi ngoại lệ.

**Symptom (pipeline làm gì sai?):**
Khi chạy script `eval_trace.py` để ra báo cáo cuối, script văng lỗi dừng đột ngột khiến không có số liệu scorecard nào được sinh ra. Báo lỗi do đối tượng dữ liệu thiếu key dict quan trọng.

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**
Lỗi nằm ở sự không nhất quán trong State Contract. Supervisor chưa ép giá trị chuẩn cho một số edge case, dẫn đến việc đôi khi Supervisor route vào nhánh fallback mặc định mà không set giá trị `route_reason`. File log lúc đó chỉ có key `supervisor_route` mà truy xuất `route_reason` sẽ văng lỗi.

**Cách sửa:**
Tôi cập nhật hàm `analyze_trace()` thêm method `dict.get("route_reason", "No reason provided")` để fallback an toàn, tránh lỗi app crash. Đồng thời tôi phối hợp với Supervisor Owner cập nhật lại logic đảm bảo always enforce key `route_reason` vào `AgentState` trước đoạn return state.

**Bằng chứng trước/sau:**
> Trước khi sửa: `KeyError: 'route_reason' traceback at line 45 eval_trace.py`
> Sau khi sửa: Log phân tích thành công: `Run run_2026_04_13_1435: route_reason = No reason provided`.

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Tôi tổ chức documentation cực kỳ liền mạch, làm rõ yêu cầu I/O cho mọi người ngay từ đầu sprint. Việc tôi push nhanh chuẩn JSON schema giúp giảm thời gian chết do debug lỗi mất đồng bộ dữ liệu giữa các bạn chạy Worker.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Do phải dành nhiều thời gian tinh chỉnh Doc markdown theo template, tốc độ implement hàm tính logic Deep Comparison trong `compare_single_vs_multi()` gặp độ trễ, báo cáo kết xuất chưa thật sự có độ sâu tính toán cao như kỳ vọng.

**Nhóm phụ thuộc vào tôi ở đâu?** 
Nhóm không thể nhận diện được Supervisor hay Retrieval đang thất bại ở node nào nếu tôi không wrap được file trace chuẩn xác. Nhóm sẽ hoàn toàn "mù" nếu thiếu bảng theo dõi để đo đạc và điều chỉnh.

**Phần tôi phụ thuộc vào thành viên khác:**
Tôi cần các Worker Owners không thay đổi key tên biến JSON một cách ngẫu hứng lúc build output để hàm Parser của tôi không bị nổ lỗi.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Nếu có thêm 2 giờ, tôi sẽ nâng cấp báo cáo report sinh từ `eval_trace.py` bằng việc đính kèm module vẽ Chart (Matplotlib/Seaborn) ra mảng biểu đồ trực quan (như Bar chart phân phối Latency hay Pie chart tỷ lệ Route), thay vì chỉ in Terminal Console log text nguyên thuỷ. Lý do vì trace log của câu `gq11` gặp spike độ trễ lên tận 18,500ms thao tác nhìn bằng mắt chay qua JSON line sẽ dễ đoán mò sai hơn là có chart visual.
