# Báo Cáo Nhóm — Lab Day 08: Full RAG Pipeline

**Tên nhóm:** Nhóm 1 - E402  
**Thành viên:**

| Tên | MSSV | Vai trò |
|-----|------|---------|
| Phạm Đoàn Phương Anh | 2A202600257 | Tech Lead (Sprint 1) |
| Trương Minh Tiền | 2A202600438 | Retrieval Owner (Sprint 2) |
| Nguyễn Đức Trí | 2A202600394 | Retrieval Owner (Sprint 3 — Hybrid + Rerank) |
| Huỳnh Thái Bảo | 2A202600373 | Eval Owner (Sprint 4) |
| Nguyễn Đức Dũng | 2A202600148 | Documentation Owner |

**Ngày nộp:** 2026-04-13  
**Repo:** https://github.com/truongminhtien/20KAI-day8-lab8  
**Độ dài khuyến nghị:** 600–900 từ

---

## 1. Pipeline nhóm đã xây dựng (150–200 từ)

**Chunking decision:**  
Nhóm dùng `chunk_size=400 tokens`, `overlap=80 tokens`, tách theo **section headers** (`=== Section ===`) vì tài liệu policy có cấu trúc phân mục rõ ràng. Sau vòng eval đầu, nhóm bổ sung 2 cải tiến quan trọng: (1) **merge section ngắn** (< 300 chars) với section kế tiếp để tránh tách rời scope khỏi chi tiết (ví dụ: Section 1 "Phạm vi áp dụng contractor" của access_control_sop bị tách riêng khỏi Section 2 "Level 4 Admin Access"); (2) **thêm document preamble** `[Tài liệu: source | Hiệu lực: date]` vào mỗi chunk để embedding capture được context tài liệu + temporal metadata.

**Embedding model:**  
`paraphrase-multilingual-MiniLM-L12-v2` (sentence-transformers, local, miễn phí, hỗ trợ tiếng Việt).

**Retrieval variant (Sprint 3):**  
**Hybrid (Dense + BM25 với Weighted RRF) + Cross-encoder Rerank.** Dense (weight 0.6) + BM25 (weight 0.4) dùng Reciprocal Rank Fusion, sau đó `ms-marco-MiniLM-L-6-v2` rerank top-15 xuống top-4 trước khi đưa vào prompt. Lý do: corpus có cả ngôn ngữ tự nhiên (policy) lẫn keyword/alias (mã lỗi, tên tài liệu cũ) — hybrid bắt được cả hai; rerank lọc nhiễu sau khi search rộng.

---

## 2. Quyết định kỹ thuật quan trọng nhất (200–250 từ)

**Quyết định:** Chọn **Hybrid + Rerank** làm variant chính cho Sprint 3 thay vì Query Transformation.

**Bối cảnh vấn đề:**  
Baseline dense fail hai dạng query đối lập: (a) query chứa alias/tên cũ như q07 "Approval Matrix" (tên hiện tại là "Access Control SOP") — dense semantic match kém; (b) query chứa mã lỗi như q09 "ERR-403-AUTH" — embedding không capture được token hiếm. Context Recall baseline chỉ đạt 3.50/5.

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|-----------|
| Hybrid (Dense + BM25) | Giải quyết cả alias và keyword. BM25 bắt exact match, dense hiểu semantic | Cần tuning weight (0.6/0.4). Merge score phức tạp hơn |
| Rerank only (dense + cross-encoder) | Cải thiện precision sau search rộng | Vẫn fail nếu dense không retrieve được chunk đúng từ đầu |
| Query Transformation (HyDE/Expansion) | Xử lý query mơ hồ bằng hypothetical answer | Thêm 1 LLM call → tăng latency + cost. Không giải quyết root cause dense yếu với keyword |

**Phương án đã chọn và lý do:**  
**Hybrid + Rerank.** Hybrid giải quyết root cause (dense bỏ lỡ keyword/alias), Rerank là bước lọc tinh để giảm noise sau khi search rộng. Đây là hai biến bổ trợ nhau — hybrid tăng recall, rerank tăng precision. Query Transformation bị loại vì tốn thêm 1 LLM call mà không fix được vấn đề dense yếu với exact match.

**Bằng chứng từ tuning-log:**  
Sau Hybrid+Rerank: Context Recall 3.50 → 4.67 (+1.17), Relevance 3.80 → 4.60 (+0.80), Faithfulness 4.20 → 4.60 (+0.40). q07 và q09 từ recall 1/5 lên 5/5.

---

## 3. Kết quả grading questions (100–150 từ)

**Ước tính điểm raw:** ~72 / 98

**Câu tốt nhất:** **gq01** (SLA P1 version history) — nhờ document preamble thêm `Hiệu lực: 2026-01-15` vào mỗi chunk, LLM reasoning được đúng lịch sử thay đổi (v2026.1: 6h → 4h). Faithful/Relevant/Recall/Complete đều 5/5.

**Câu fail:** **gq10** (chính sách hoàn tiền áp dụng trước 01/02/2026?) — Faithful 1, Complete 1. Root cause ở **generation**, không phải retrieval. Retriever đã lấy đúng chunk Điều 1 "áp dụng cho đơn hàng từ 01/02/2026" (Recall 5/5), nhưng LLM đọc ngược ngữ cảnh "kể từ ngày" thành "trước ngày". Đây là lỗi reasoning của Gemini Flash-lite với mốc thời gian.

**Câu gq07 (abstain):** Pipeline xử lý **đúng** — sau khi thêm rule ABSTAIN trong prompt ("penalties, fines NOT in context → MUST abstain"), variant trả lời: "Không đủ dữ liệu trong tài liệu để trả lời." thay vì hallucinate mức phạt từ SLA document.

---

## 4. A/B Comparison — Baseline vs Variant (150–200 từ)

**Biến đã thay đổi:** `retrieval_mode: dense → hybrid` + bật `use_rerank=True` (A/B hợp nhất vì hai biến bổ trợ, cùng mục tiêu tăng retrieval quality).

| Metric | Baseline (Dense) | Variant (Hybrid+Rerank) | Delta |
|--------|---------|---------|-------|
| Faithfulness | 4.20 /5 | 4.60 /5 | **+0.40** |
| Answer Relevance | 3.80 /5 | 4.60 /5 | **+0.80** |
| Context Recall | 3.50 /5 | 4.67 /5 | **+1.17** |
| Completeness | 3.20 /5 | 3.50 /5 | **+0.30** |

**Kết luận:**  
Variant tốt hơn baseline rõ rệt ở **Context Recall** (+1.17) và **Relevance** (+0.80). Hybrid giải quyết được các query alias/keyword mà dense miss (q07, q09), rerank lọc chunk "gần nghĩa nhưng không match" giúp context đưa vào prompt sạch hơn. **Completeness chỉ tăng +0.30** — đây là bottleneck còn lại: LLM (Gemini Flash-lite) không đủ reasoning để tổng hợp đầy đủ nhiều chi tiết (điển hình gq10 fail vì đọc sai mốc thời gian dù chunk đúng). Nâng retrieval đã chạm trần; muốn tăng Completeness tiếp, cần upgrade LLM hoặc thêm prompt engineering mạnh hơn.

---

## 5. Phân công và đánh giá nhóm (100–150 từ)

**Phân công thực tế:**

| Thành viên | Phần đã làm | Sprint |
|------------|-------------|--------|
| Phạm Đoàn Phương Anh | Baseline pipeline, chunking strategy, điều phối nhóm | 1 |
| Trương Minh Tiền | `retrieve_dense`, `retrieve_sparse`, grounded prompt baseline, `call_llm` Gemini | 2 |
| Nguyễn Đức Trí | `retrieve_hybrid` (RRF), `rerank` (cross-encoder), prompt anti-hallucination | 3 |
| Huỳnh Thái Bảo | `eval.py` 4 metrics (LLM-as-Judge), scorecard, A/B comparison | 4 |
| Nguyễn Đức Dũng | `architecture.md`, `tuning-log.md`, merge code, chạy regression test | Xuyên suốt |

**Điều nhóm làm tốt:**  
Phân vai rõ theo sprint → không overlap. Tuân thủ A/B rule (chỉ đổi 1 biến nhóm mỗi lần) giúp đo được delta chính xác. Documentation cập nhật liên tục sau mỗi sprint nên ai cũng nắm được context chung.

**Điều nhóm làm chưa tốt:**  
Chưa phát hiện sớm bottleneck ở Completeness — nếu có thêm 1 iteration, nhóm sẽ thử upgrade LLM hoặc thêm chain-of-thought prompt. Chưa tận dụng hết BM25 weight tuning (0.6/0.4 cố định, chưa thử 0.5/0.5 hoặc 0.7/0.3).

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì? (50–100 từ)

1. **Upgrade LLM hoặc thêm reasoning prompt cho gq10**: Scorecard cho thấy Completeness 3.50 là trần hiện tại do Gemini Flash-lite fail reasoning mốc thời gian. Thử `gemini-2.5-flash` (không phải lite) hoặc thêm chain-of-thought bắt LLM verify điều kiện temporal trước khi kết luận.

2. **Multi-query retrieval cho câu cross-document** (gq02, gq06): Decompose query phức tạp thành 2-3 sub-queries, retrieve riêng rồi merge. Scorecard cho thấy câu cross-document vẫn thiếu chunk từ document thứ hai — đây là gốc rễ của Completeness thấp.

---

*File này lưu tại: `reports/group_report.md`*  
*Commit sau 18:00 được phép theo SCORING.md*
