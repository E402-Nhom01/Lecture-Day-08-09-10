# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Đức Trí  
**MSSV:** 2A202600394  
**Vai trò trong nhóm:** Tech Lead / Retrieval Owner / Eval Owner / Documentation Owner  
**Ngày nộp:** ___________  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

> Sprint 3 em lựa chọn implement hybrid retrieval kết hợp rerank để tối ưu cả recall và precision. Cụ thể, pipeline được giữ nguyên bước retrieve rộng với retrieve_hybrid() nhằm tận dụng ưu điểm của dense (hiểu ngữ nghĩa) và sparse/BM25 (match keyword chính xác), giúp giảm miss các chunk quan trọng. Sau đó, bật use_rerank=True để áp dụng cross-encoder (ms-marco-MiniLM-L-6-v2) chấm lại độ liên quan giữa query và từng chunk, từ đó chọn ra top-3 chunk chất lượng cao nhất trước khi đưa vào prompt. Quyết định này dựa trên thực tế rằng hybrid giúp tăng coverage nhưng vẫn có noise, nên rerank đóng vai trò “lọc tinh”. So với baseline dense, variant này cải thiện rõ độ chính xác câu trả lời và giảm hallucination do context đầu vào sạch và sát hơn.

_________________

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

> Sau lab này, tôi hiểu rõ hơn về hybrid retrieval và grounded prompt. Với hybrid retrieval, trước đây tôi nghĩ chỉ cần dense là đủ, nhưng khi làm thực tế mới thấy dense có thể bỏ sót keyword quan trọng, còn BM25 lại không hiểu ngữ nghĩa. Kết hợp cả hai giúp tăng khả năng tìm đúng tài liệu liên quan, đặc biệt trong các query có cả thuật ngữ kỹ thuật và cách diễn đạt tự nhiên. Ngoài ra, grounded prompt giúp kiểm soát LLM tốt hơn rất nhiều. Thay vì để model trả lời tự do, việc ép nó chỉ dùng context đã retrieve và phải trích dẫn nguồn giúp giảm hallucination rõ rệt. Tôi nhận ra prompt không chỉ để “hỏi” mà còn là công cụ để “ràng buộc hành vi” của model.

_________________

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

> Điều gì xảy ra không đúng kỳ vọng?
> Lỗi nào mất nhiều thời gian debug nhất?
> Giả thuyết ban đầu của bạn là gì và thực tế ra sao?

_________________

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

> Chọn 1 câu hỏi trong test_questions.json mà nhóm bạn thấy thú vị.
> Phân tích:
> - Baseline trả lời đúng hay sai? Điểm như thế nào?
> - Lỗi nằm ở đâu: indexing / retrieval / generation?
> - Variant có cải thiện không? Tại sao có/không?

**Câu hỏi:** ___________

**Phân tích:**

_________________

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

> 1-2 cải tiến cụ thể bạn muốn thử.
> Không phải "làm tốt hơn chung chung" mà phải là:
> "Tôi sẽ thử X vì kết quả eval cho thấy Y."

_________________

---

*Lưu file này với tên: `reports/individual/nguyen_duc_tri.md`*
