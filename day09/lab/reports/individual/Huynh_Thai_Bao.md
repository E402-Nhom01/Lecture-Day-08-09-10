# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Huỳnh Thái Bảo  
**Vai trò trong nhóm:** Worker Owner  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

> **Lưu ý quan trọng:**
> - Viết ở ngôi **"tôi"**, gắn với chi tiết thật của phần bạn làm
> - Phải có **bằng chứng cụ thể**: tên file, đoạn code, kết quả trace, hoặc commit
> - Nội dung phân tích phải khác hoàn toàn với các thành viên trong nhóm
> - Deadline: Được commit **sau 18:00** (xem SCORING.md)
> - Lưu file với tên: `reports/individual/[ten_ban].md` (VD: `nguyen_van_a.md`)

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

> Mô tả cụ thể module, worker, contract, hoặc phần trace bạn trực tiếp làm.
> Không chỉ nói "tôi làm Sprint X" — nói rõ file nào, function nào, quyết định nào.

**Module/file tôi chịu trách nhiệm:**
- File chính: `lab/workers/retrieval.py`
- Functions tôi implement: `retrieve_dense`, `_get_embedding_fn`, `_keyword_overlap_score`, `run`

**Cách công việc của tôi kết nối với phần của thành viên khác:**

Module của tôi đóng vai trò là "Retrieval Worker". Nhóm sẽ truyền `task` (truy vấn) qua object `AgentState` từ Supervisor. Module sẽ kết nối vào ChromaDB (`day09_docs`), lấy ra các văn bản liên quan có đánh giá score, và trả về qua cấu trúc contract chuẩn (`retrieved_chunks`, `retrieved_sources`, `worker_io`). Các kết quả văn bản chunk này sẽ trở thành nguồn Context quan trọng cho Module Answer/Generator của các thành viên khác sinh ra câu trả lời dựa trên kiến thức. Nếu phần Retrieval fail hoặc rỗng, các node tiếp theo sẽ bị mất đầu vào tài liệu.

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**

Toàn bộ logic hybrid search, deduplication và quản lý fallback log trong hàm `retrieve_dense` và `run` tại `lab/workers/retrieval.py` do tôi triển khai.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

> Chọn **1 quyết định** bạn trực tiếp đề xuất hoặc implement trong phần mình phụ trách.
> Giải thích:
> - Quyết định là gì?
> - Các lựa chọn thay thế là gì?
> - Tại sao bạn chọn cách này?
> - Bằng chứng từ code/trace cho thấy quyết định này có effect gì?

**Quyết định:** Kết hợp Hybrid Retrieval (Dense Vector + Keyword Overlap) thay vì chỉ dùng một mình thuật toán Dense Search cơ chuẩn của ChromaDB.

**Ví dụ:**
> "Tôi chọn dùng keyword-based routing trong supervisor_node thay vì gọi LLM để classify.
>  Lý do: keyword routing nhanh hơn (~5ms vs ~800ms) và đủ chính xác cho 5 categories.
>  Bằng chứng: trace gq01 route_reason='task contains P1 SLA keyword', latency=45ms."

**Lý do:**

ChromaDB cung cấp dense distances search khá tốt trên câu hỏi chung về ý nghĩa ngữ nghĩa (semantic), nhưng khi user tìm kiếm theo các keyword hoặc đặc thù của dữ liệu, nó sẽ dễ gặp tình trạng điểm cách biệt (distance) không ổn định. Tôi đã tính toán hợp nhất `score = 0.7 * dense_score + 0.3 * keyword_score` với keyword score đếm sự trùng lặp (overlap) các từ vựng của document và câu truy vấn. Quyết định kết hợp này giúp nâng cao độ chính xác đáng kể đối với từ khóa cụ thể.

**Trade-off đã chấp nhận:**

Cách tính _keyword_overlap_score hiện tại khá thô, làm chương trình xử lý tốn thêm một vòng lặp Python. Thuật toán này cũng thiếu tính chính xác về mặt học thuật so với BM25 chuẩn (như chưa xét được IDF, tần suất từ khóa chung thường gặp), đổi lại là tôi tránh được việc cài đặt & quản lý instance phức tạp cho component search riêng biệt ở quy mô level lab này.

**Bằng chứng từ trace/code:**

```python
# ✅ safer similarity conversion
dense_score = 1 / (1 + dist) if dist is not None else 0.0
keyword_score = _keyword_overlap_score(query, doc)

# hybrid
score = 0.7 * dense_score + 0.3 * keyword_score
```

**Trace thực tế (từ test run local):**
```text
▶ Query: Điều kiện được hoàn tiền là gì?
✅ Collection loaded. Total docs: 5
  Retrieved: 3 chunks
    [0.587] policy_refund_v4.txt: CHÍNH SÁCH HOÀN TIỀN - PHIÊN BẢN 4
```
Log sinh ra phản ánh rõ cách Hybrid Score giúp kéo file `policy_refund` lên đúng vị trí tốt nhất với confidence > 0.5.

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

> Mô tả 1 bug thực tế bạn gặp và sửa được trong lab hôm nay.
> Phải có: mô tả lỗi, symptom, root cause, cách sửa, và bằng chứng trước/sau.

**Lỗi:** Nút thắt hiệu năng (Performance bottleneck) do tải model khởi tạo LLM và kết nối DB lặp lại nhiều lần.

**Symptom (pipeline làm gì sai?):**

Pipeline tốn độ trễ (latency) rất dài và bị chững lại ở node `retrieval_worker`. Trace bài bản từ phần log chạy script test độc lập hiển thị thanh progress bar `Loading weights: 100%|...` và warning model cấu trúc `UNEXPECTED embeddings` lặp lại tới **3 lần** cho 3 lượt truy vấn liên tiếp nhau.

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**

Lỗi nằm ở Worker Logic. Trong hàm lấy embedding `_get_embedding_fn()` và hàm kết nối database `_get_collection()`, mã nguồn gọi lệnh sinh thực thể `SentenceTransformer("all-MiniLM-L6-v2")` và `PersistentClient` của ChromaDB ở phạm vi cục bộ. Vì gọi bởi hàm `retrieve_dense()`, kết quả là mỗi lượt trả lời đều bắt thiết bị phải fetch & load lại LLM Weights (>100MB) rồi tốn thời gian I/O disk khiến chương trình chậm kinh hoàng.

**Cách sửa:**

Tôi áp dụng cơ chế **Caching State với biến Global (Singleton pattern)**. Khai báo 2 biến cờ `_embed_model` và `_client` gắn với trạng thái `None`. Khi gọi lần đầu, framework sẽ load object một lần định danh vào RAM. Các queries task phía sau của nhánh routing AgentState chỉ việc dùng phiên bản đã mở mà không hề tạo mới để bypass độ trễ hoàn toàn.

**Bằng chứng trước/sau:**
> Dán trace/log/output trước khi sửa và sau khi sửa.

Trace lúc lỗi (tiến trình báo tải cấu trúc Model tới tận 3 lớp):
```text
▶ Query 1: SLA ticket...
Loading weights: 100%|███| 103/103
▶ Query 2: Điều kiện hoàn tiền...
Loading weights: 100%|███| 103/103
▶ Query 3: Ai phê duyệt...
Loading weights: 100%|███| 103/103
```
Sau khi thêm logic fix cache: Model chỉ tốn RAM loading duy nhất 1 lần ở câu Query khởi động bằng lệnh if, sau đó trả output tức thì cho số chunk.

Code fix:
```python
_embed_model = None
def _get_embedding_fn():
    global _embed_model
    if _embed_model is None: # Tối ưu Cache tránh bị Leak memory / Load đè
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
...
```

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

> Trả lời trung thực — không phải để khen ngợi bản thân.

**Tôi làm tốt nhất ở điểm nào?**

Tích hợp được luồng điểm đánh giá Hybrid Search an toàn có khả năng giảm thiểu nhược điểm của Dense vector (sử dụng distance convert và overlap score kết hợp và kiểm soát lỗi fallbacks an toàn). Đầu ra xuất trả `worker_io` và log history đầy đủ cho `AgentState` để dễ dàng trace lỗi và debug.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

Chưa phân loại và tối ưu được chỉ số Reranker từ các mô hình Cross-Encoder chất lượng cao. Hệ số Hybrid cố định tỷ lệ `0.7 - 0.3` có thể chưa tối ưu với toàn bộ context mà chưa có auto-test đánh giá độ chính xác chéo (Precision/Recall). Bộ xử lý từ keyword trùng lặp cũng sử dụng quy tắc tách chuỗi cơ bản khá đơn giản thay cho việc tokenize chuyên sâu như ElasticSearch.

**Nhóm phụ thuộc vào tôi ở đâu?** _(Phần nào của hệ thống bị block nếu tôi chưa xong?)_

Nếu Generator không có tài liệu được retrieve chính xác từ node của tôi, LLM sẽ bị tình trạng ảo giác (hallucinate) sinh ra câu trả lời sai lệnh khỏi tri thức. Ngắn gọn, phần Generator LLM Worker trực tiếp yêu cầu kết quả của `retrieval.py` này để làm ngữ cảnh.

**Phần tôi phụ thuộc vào thành viên khác:** _(Tôi cần gì từ ai để tiếp tục được?)_

Tôi phụ thuộc vào quá trình Index data của Data / Indexing Owner để đảm bảo ChromaDB (collection `day09_docs`) đã có sẵn toàn bộ dữ liệu sạch và sẵn sàng để tìm kiếm. Tôi cũng cần Supervisor điều hướng task hợp lệ vào đúng Worker tên `retrieval_worker`.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

> Nêu **đúng 1 cải tiến** với lý do có bằng chứng từ trace hoặc scorecard.
> Không phải "làm tốt hơn chung chung" — phải là:
> *"Tôi sẽ thử X vì trace của câu gq___ cho thấy Y."*

Tôi sẽ tích hợp Cross-Encoder (như mô hình HuggingFace `cross-encoder/ms-marco-MiniLM-L-6-v2`) làm bước "Re-ranking" ở khâu cuối, ngay sau khi có top_k hiện tại từ Hybrid. Lý do: dựa trên log test từ query trả về, mặc dù `retrieved_chunks` lọc được keyword có vẻ khớp, nhưng đôi khi context không thể đáp ứng chính xác về ngữ nghĩa cho câu hỏi phức tạp khiến `retrieval_confidence` khá nhiễu. Bổ sung Reranker giúp đưa chunk tốt thực sự lên hạng #0 để trả lời chính xác nhất.

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*  
*Ví dụ: `reports/individual/nguyen_van_a.md`*
