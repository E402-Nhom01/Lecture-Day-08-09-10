# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Đức Dũng  
**MSSV:** 2A202600148  
**Vai trò trong nhóm:** Documentation Owner  
**Ngày nộp:** 13/04/2026
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Trong phần lab này, tôi đảm nhận vai trò chính là Documentation Owner. Xuyên suốt 4 sprint, đặc biệt là ở Sprint 3 và Sprint 4, tôi đóng vai trò điều phối như theo dõi tiến độ các thành viên và hỗ trợ nhóm giải quyết các vấn đề về Git để việc ghép code diễn ra suôn sẻ. Không chỉ vậy, tôi còn cùng nhóm thảo luận, đề xuất các ý tưởng tuning cho quá trình retrieval và liên tục chạy kiểm thử (`index.py`, `rag_answer.py`, `eval.py`) lại toàn bộ hệ thống để đảm bảo code tổng không gặp lỗi.

Sau mỗi sprint, công việc thiết yếu của tôi là làm tài liệu, bao gồm thu thập logs của các thành viên khác, cũng như kết quả cập nhật kiến trúc hệ thống (`architecture.md`) và ghi chú lại tất cả lý do hoặc quyết định vào file `tuning-log.md`. Các ghi chép này giúp mọi thành viên bám sát tiến độ chung, đồng thời cung cấp đầy đủ thông tin liên quan để Eval Owner có thể chạy thử nghiệm chính xác.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Sau khi hoàn thành hệ thống, concept tôi thấy nhớ nhất chính là quá trình tuning theo nguyên tắc "Điều chỉnh tối thiểu" (Minimal tuning) trong pipeline RAG. Trước đây, tôi thường nghĩ việc kết hợp tất cả các thuật toán retrieval khủng nhất thì sẽ tự động đưa ra kết quả tốt nhất. Tuy nhiên, qua quá trình làm báo cáo từ các phiên bản Baseline và Hybrid/Rerank, tôi nhận thấy nhiều khi, áp dụng các kỹ thuật tốt, phức tạp hơn vào lại không cho ra kết quả tốt như tưởng tượng.

Ngoài ra, tôi hiểu rất rõ định nghĩa của phần grounded generation. Tôi đã tận mắt thấy rằng, cho dù Retriever có xuất sắc đến đâu, nếu đoạn Prompt gửi vào mô hình tạo sinh không chặt chẽ, LLM vẫn có xu hướng tự biên tự diễn ảo giác (hallucination). Grounded generation phải được gắn chặt vào context từ bước Retrieval để duy trì tính trung thực của toàn bộ hệ thống.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Một điều khác làm tôi ngạc nhiên là sự "mong manh" của hiệu suất hệ thống khi thay đổi kích thước mô hình ngôn ngữ. Để tối ưu tốc độ phản hồi và chi phí, nhóm đã thử nghiệm một mô hình nhỏ. Tuy nhiên, kết quả thu được là tệ; mô hình thường xuyên gặp lỗi logic cơ bản, chẳng hạn như hiểu sai mốc thời gian hiệu lực của chính sách (trong câu gq10), dẫn đến hiện tượng ảo giác dù dữ liệu đầu vào hoàn toàn chính xác. Điều này khiến tôi nhận ra rằng trong RAG, khả năng suy luận (reasoning) của mô hình quan trọng không kém gì độ chính xác của bước truy xuất.

Về mặt công việc, với vai trò Documentation Owner, tôi gặp khó khăn trong việc chuẩn hóa dữ liệu từ các lần chạy thử nghiệm (logs) khác nhau của thành viên. Mỗi cấu hình (Baseline, Dense, Hybrid) lại cho ra các chỉ số scorecard rất khác biệt, và việc ghi chép lại chính xác "tại sao thay đổi này lại làm Recall tăng nhưng Completeness giảm" đòi hỏi sự quan sát tỉ mỉ để không làm sai lệch báo cáo cuối cùng của nhóm.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

> Câu hỏi: [gq10] — "Chính sách hoàn tiền hiện tại áp dụng cho đơn hàng đặt trước ngày 01/02/2026 không?"

> Phân tích:

Đây là một ca kiểm thử quan trọng để đánh giá tính Faithfulness (trung thực) và Completeness (đầy đủ) của hệ thống. Kết quả từ scorecard cho thấy đây là câu hỏi bị chấm điểm thấp nhất (Faithful: 1, Complete: 1) do mô hình đưa ra thông tin hoàn toàn mâu thuẫn với thực tế.

- Về Retrieval: Hệ thống đã thực hiện tốt khi truy xuất đúng nguồn tài liệu policy/refund-v4.pdf [1], trong đó nêu rõ chính sách chỉ áp dụng cho đơn hàng từ ngày 01/02/2026. Chỉ số Recall đạt 5 cho thấy bước tìm kiếm không có lỗi.
- Về Generation (Root Cause): Lỗi nằm ở khả năng suy luận của LLM. Dù ngữ cảnh (context) cung cấp dữ liệu đúng, nhưng LLM lại khẳng định chính sách áp dụng cho các đơn hàng trước ngày 01/02/2026. Đây là lỗi logic nghiêm trọng khi mô hình không phân biệt được mốc thời gian "kể từ ngày" và "trước ngày". Ngoài ra, mô hình cũng bỏ sót thông tin quan trọng về việc các đơn hàng cũ sẽ áp dụng phiên bản chính sách trước đó.
- Giải pháp: Cần tinh chỉnh (fine-tune) lại System Prompt để yêu cầu LLM đặc biệt chú ý đến các mốc thời gian và điều kiện loại trừ, đồng thời cân nhắc sử dụng mô hình có khả năng suy luận logic (reasoning) tốt hơn để tránh tình trạng đọc hiểu sai lệch context đã tìm được.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Nếu có thêm thời gian, tôi sẽ thử nghiệm kỹ thuật Query Transformation (đặc biệt là Query Expansion) cho hệ thống của nhóm. Từ bài giảng, tôi cảm thấy đây là một ý tưởng hay, tuy nhiên thời gian của lab không cho phép chúng tôi nghiên cứu thêm về phương án này. Kỳ vọng: Transform mở rộng câu hỏi đầu vào và có thể khớp nhiều ngữ cảnh hơn, hứa hẹn sẽ cải thiện đáng kể tính trung thực trong generation.

---
