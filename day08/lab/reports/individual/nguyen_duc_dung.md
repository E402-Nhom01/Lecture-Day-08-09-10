# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Đức Dũng  
**MSSV:** 2A202600148  
**Vai trò trong nhóm:** Tech Lead / Retrieval Owner / Eval Owner / Documentation Owner  
**Ngày nộp:** 13/04/2026
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

> Mô tả cụ thể phần bạn đóng góp vào pipeline:
> - Sprint nào bạn chủ yếu làm?
> - Cụ thể bạn implement hoặc quyết định điều gì?
> - Công việc của bạn kết nối với phần của người khác như thế nào?

_________________

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

> Chọn 1-2 concept từ bài học mà bạn thực sự hiểu rõ hơn sau khi làm lab.
> Ví dụ: chunking, hybrid retrieval, grounded prompt, evaluation loop.
> Giải thích bằng ngôn ngữ của bạn — không copy từ slide.

_________________

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

> Điều gì xảy ra không đúng kỳ vọng?
> Lỗi nào mất nhiều thời gian debug nhất?
> Giả thuyết ban đầu của bạn là gì và thực tế ra sao?

_________________

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

> Câu hỏi: q09 — "ERR-403-AUTH là lỗi gì và cách xử lý?"
Phân tích:
Đây là test case để kiểm tra khả năng abstain khi hệ thống không có dữ liệu. Trong corpus hiện tại không tồn tại bất kỳ thông tin nào về mã lỗi ERR-403-AUTH.
Baseline (dense): Dense retrieval vẫn trả về một số chunk từ IT Helpdesk FAQ có liên quan như “đăng nhập”, “tài khoản bị khóa”. Về mặt semantic thì gần với auth error, nhưng không match trực tiếp với ERR-403-AUTH. Nếu prompt không đủ strict, LLM sẽ infer từ các chunk này và generate câu trả lời không grounded → dẫn đến hallucination, làm giảm faithfulness.
Root cause: Nằm ở bước generation, không phải retrieval. Retriever đã trả về best-effort candidates, nhưng LLM cần detect được lack of exact evidence và trigger abstain.
Variant (hybrid + rerank): Khi thêm rerank (cross-encoder), các chunk chỉ “semantic match” sẽ bị score thấp hơn do không align trực tiếp với query. Kết hợp với prompt anti-hallucination, pipeline sẽ filter context tốt hơn và output đúng hành vi: abstain với thông báo không có dữ liệu liên quan.

_________________

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

> 1-2 cải tiến cụ thể bạn muốn thử.
> Không phải "làm tốt hơn chung chung" mà phải là:
> "Tôi sẽ thử X vì kết quả eval cho thấy Y."

_________________

---

*Lưu file này với tên: `reports/individual/nguyen_duc_dung.md`*
