# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Huỳnh Thái Bảo  
**MSSV:** 2A202600373  
**Vai trò trong nhóm:** Eval Owner
**Ngày nộp:** 13/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Trong lab Day 08, phần mình làm chính nằm ở **Sprint 4 (Evaluation & Scorecard)**, tập trung vào file `eval.py`. Mình thiết kế luồng chấm điểm để chạy bộ câu hỏi qua pipeline và đo theo 4 metric: Faithfulness, Relevance, Context Recall, Completeness. Cụ thể, mình hoàn thiện các hàm chấm điểm, chuẩn hóa output theo từng question, tạo summary markdown và hỗ trợ so sánh baseline/variant theo đúng tinh thần A/B test (đổi một biến mỗi lần). Ngoài ra, mình làm phần xử lý lỗi khi pipeline fail để vẫn ghi nhận kết quả rõ ràng thay vì làm vỡ toàn bộ lượt chấm. Công việc này kết nối trực tiếp với phần retrieval/generation của các bạn khác: nếu retrieval đổi mode (dense/hybrid, rerank), `eval.py` phải phản ánh đúng khác biệt để nhóm biết thay đổi nào thực sự cải thiện chất lượng.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Sau lab này, điều mình hiểu rõ nhất là **evaluation loop** trong RAG không chỉ là “chạy rồi lấy điểm trung bình”, mà là công cụ để ra quyết định kỹ thuật. Trước đây mình nghĩ chỉ cần nhìn answer đúng/sai là đủ, nhưng khi tách thành 4 metric thì thấy từng lỗi nằm ở tầng khác nhau: retrieval thiếu bằng chứng sẽ kéo Context Recall xuống; prompt hoặc synthesis yếu thì Completeness thấp dù nguồn đúng; còn Faithfulness giúp phát hiện hallucination dù câu trả lời nghe hợp lý. Mình cũng hiểu rõ hơn việc dùng **LLM-as-judge**: cần prompt chặt, yêu cầu JSON strict, và phải xử lý parse/error cẩn thận để scorecard không nhiễu. Nói ngắn gọn, eval không phải phần “trang trí” cuối pipeline mà là vòng phản hồi quan trọng để tune hệ thống có cơ sở.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Khó khăn lớn nhất mình gặp là lúc đầu kết quả chấm chưa ổn định và khó giải thích cho cả nhóm. Có hai vấn đề chính: (1) output từ judge đôi khi không đúng format JSON, làm đứt flow scoring; (2) metric Completeness có lúc thấp dù answer nhìn “có vẻ đúng”, do answer thiếu chi tiết so với expected answer. Ban đầu mình giả thuyết lỗi chủ yếu nằm ở retrieval, nhưng khi soi kỹ từng metric thì thấy nhiều case retrieval đã lấy đúng nguồn, còn thiếu ở bước generation (trả lời ngắn hoặc bỏ sót điều kiện). Mình xử lý bằng cách siết prompt evaluator, thêm hàm `extract_json`, và ghi notes theo từng metric để debug theo evidence thay vì cảm tính. Bài học rút ra là phải đọc score theo cấu trúc, không kết luận nhanh chỉ từ một chỉ số.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi:** q09 — "ERR-403-AUTH là lỗi gì và cách xử lý?"

**Phân tích:**

Đây là câu hỏi kiểm tra khả năng abstain — thông tin về mã lỗi ERR-403-AUTH không tồn tại trong bất kỳ tài liệu nào trong corpus.
Baseline (dense): Dense retrieval trả về các chunk từ IT Helpdesk FAQ có chứa từ "đăng nhập", "tài khoản bị khóa" — semantic gần với "auth error" nhưng không phải ERR-403-AUTH. Nếu prompt không đủ mạnh, model sẽ suy diễn từ các chunk này và bịa ra câu trả lời. Điểm Faithfulness thấp nếu model hallucinate.
Lỗi nằm ở: Generation — retriever đúng khi trả về chunk liên quan nhất có thể, nhưng generation phải nhận ra rằng không chunk nào thực sự chứa "ERR-403-AUTH" và abstain. Đây là bài test cho grounded prompt design.
Variant (hybrid + rerank): Rerank giúp vì cross-encoder chấm lại relevance chính xác hơn — score thấp cho chunk chỉ "gần nghĩa" nhưng không match. Kết hợp với prompt anti-hallucination mạnh, variant abstain đúng: "Không tìm thấy thông tin về ERR-403-AUTH trong tài liệu hiện có."

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Nếu có thêm thời gian, mình sẽ làm hai việc cụ thể. Thứ nhất, mình sẽ thêm một lượt **calibration cho LLM-as-judge** bằng bộ câu chuẩn nhỏ để giảm độ dao động giữa các lần chấm, vì kết quả eval hiện vẫn phụ thuộc wording của prompt. Thứ hai, mình sẽ thử một biến thể prompt synthesis có ràng buộc mạnh hơn về evidence (trích source bắt buộc cho từng claim), vì score cho thấy một số câu bị giảm Faithfulness/Completeness dù retrieval không tệ.

---

*Lưu file này với tên: `reports/individual/huynh_thai_bao.md`*
