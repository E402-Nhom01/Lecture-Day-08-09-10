# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Đức Dũng  
**Vai trò trong nhóm:** Worker Owner, MCP Owner  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

> **Lưu ý quan trọng:**
>
> - Viết ở ngôi **"tôi"**, gắn với chi tiết thật của phần bạn làm
> - Phải có **bằng chứng cụ thể**: tên file, đoạn code, kết quả trace, hoặc commit
> - Nội dung phân tích phải khác hoàn toàn với các thành viên trong nhóm

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

Trong dự án lab này, tôi đảm nhận hai vai trò chính: tối ưu worker tổng hợp câu trả lời (`synthesis.py`) và chạy thử nghiệm, debug hệ thống trong sprint 3.

**Module/file tôi chịu trách nhiệm:**

- File chính: `workers/synthesis.py` (nâng cấp từ bản `synthesis_old.py`)
- Ngoài ra tôi trực tiếp phụ trách luồng kiểm thử pipeline cuối của Sprint 3: mcp_server, mcp_http_server, mcp_ui.

**Functions tôi implement:**

- `synthesize()`: Nâng cấp luồng tạo câu trả lời, tinh chỉnh prompt và thêm các cơ chế bảo vệ.
- Xử lý logic fallback và post-processing cho kết quả từ LLM (bảo đảm có citations).

**Cách công việc của tôi kết nối với phần của thành viên khác:**

- Nhận input là `state["retrieved_chunks"]` từ `retrieval_worker` và `state["policy_result"]` từ `policy_tool_worker`.
- Trả về câu trả lời cuối cùng (`final_answer`), trích dẫn (`sources`) và độ tin cậy (`confidence`) cho User/Supervisor.

**Bằng chứng: hash aa405c7**
File `workers/synthesis.py`

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Tôi áp dụng cơ chế **Hard Guard** (chặn cứng) kết hợp **Post-processing** thay vì phó mặc hoàn toàn cho LLM tự quyết định việc từ chối trả lời hoặc tự chèn nguồn.

**Lý do:**
Khi hệ thống retrieval không tìm thấy bất kỳ mảnh tài liệu nào (chunks rỗng), việc gọi LLM là vô nghĩa và tiềm ẩn rủi ro hallucination. Việc tôi chặn luôn từ đầu (`if not chunks: return ...`) giúp tiết kiệm chi phí gọi API và tăng độ chính xác lên tối đa.

**Trade-off đã chấp nhận:**
Code có thêm vài rule manual bên ngoài LLM thay vì sử dụng hoàn toàn prompt. Đôi lúc LLM sinh ra thông tin có ích nhưng không có source sẽ bị ép phải chèn chuỗi `[Nguồn:...]`.

**Bằng chứng từ trace/code:**
Code tôi triển khai trong `synthesis.py` `aa405c7`:

```python
# ✅ HARD GUARD: no chunks → abstain immediately (avoid hallucination)
if not chunks:
    return {
        "answer": "Không đủ thông tin trong tài liệu nội bộ.",
        "sources": [],
        "confidence": 0.1,
    }

#... sau khi gọi LLM
# ✅ Enforce citation if missing
if sources and not any(src in answer for src in sources):
    answer += "\n\n[Nguồn: " + ", ".join(sources) + "]"
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** Trả lời hallucinate khi thiếu thông tin và thiếu nguồn (source) đính kèm.

**Symptom:**
Trong quá trình thử nghiệm Sprint 3, với một vài câu hỏi không có data, `synthesis_worker` bản cũ (gọi là `synthesis_old.py`) vẫn trả ra câu trả lời do LLM tự bịa ra. Đồng thời, một số câu hỏi có kết quả nhưng phần sources không xuất hiện trong câu trả lời sinh ra.

**Root cause:**
Prompt cũ ở bản `synthesis_old.py` khá đơn giản và không có can thiệp tiền trích xuất: `"Hãy trả lời câu hỏi dựa vào tài liệu trên"`. Mô hình đôi khi bỏ qua quy tắc không có trong context thì không được trả lời.

**Cách sửa:**

- Cải tiến User Prompt với chỉ thị rõ ràng (`Stronger user instruction`).
- Cài đặt thêm Hard guard kiểm tra `if not chunks:` và `if not answer or len(answer.strip()) < 5`.

**Bằng chứng trước/sau:**
Trước khi sửa (Sprint 2 - chạy bằng `synthesis_old.py`):

```json
"final_answer": "SLA của ticket P1 thường là 2 tiếng tuy nhiên tôi không chắc chắn."
```

Sau khi sửa (Sprint 3 - chạy bằng `synthesis_new.py`):

```json
"final_answer": "Dựa theo tài liệu, Ticket P1 có thời gian xử lý và khắc phục là 4 giờ. [Nguồn: sla_p1_2026.txt]"
```

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Tôi đã tạo ra những chốt chặn an toàn (Hard Guard, Post-processing) cho khâu synthesis, giảm tỉ lệ phát sinh Hallucination (trả lời bậy) gần như về mức lí tưởng (0%).

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Khả năng liên kết điểm `confidence` của worker tôi chưa trực tiếp tác động lên hành vi định tuyến lại (route-back) của supervisor. Điểm `confidence` này hiện là tĩnh chứ không đánh giá semantic của câu trả lời.

**Nhóm phụ thuộc vào tôi ở đâu?**
Hệ thống không thể cho ra một output sạch, có format rõ ràng, có trích xuất đúng cấu trúc [Nguồn: ...] nếu thiếu module Synthesis của tôi. Do đây là terminal node (node xuất cuối) nên nhóm bị tắc kết quả nếu synthesis hỏng.

**Phần tôi phụ thuộc vào thành viên khác:**
Tôi phụ thuộc rất lớn vào chất lượng của module Retrieval. Nếu retrieval lấy lầm chunks chứa thông tin lạc đề, dù có Synthesis tốt đến mấy thì câu trả lời cũng không có giá trị.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ biến bước tính điểm `confidence` thành một cơ chế **LLM-as-a-Judge** (thay vì tự tính toán thủ công như hiện tại). Cụ thể, sau khi LLM 1 tạo ra `answer`, tôi sẽ gọi thêm LLM 2 để kiểm tra xem "Câu trả lời có thực sự khớp 100% với chunks đưa vào không? Hãy tự cho điểm 1-10". Khi tự đánh giá bằng mô hình, điểm `confidence` sẽ khách quan và thực tiễn hơn các phép tính trọng số (`avg_score` + `exception_penalty`) hiện dùng.
