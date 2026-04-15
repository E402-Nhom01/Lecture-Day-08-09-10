# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Đức Dũng  
**Vai trò:** Monitoring / Freshness Owner  
**Ngày nộp:** 15/04/2026  
**Độ dài yêu cầu:** **400–650 từ**

---

## 1. Tôi phụ trách phần nào? (khoảng 120 từ)

Trong dự án lab Day 10, tôi đảm nhận vai trò **Monitoring / Freshness Owner**, chịu trách nhiệm chính về kiến trúc hệ thống dữ liệu, quy trình vận hành (Runbook) và giám sát (Monitoring). Tôi đã tham gia thiết kế luồng pipeline từ lúc ingest dữ liệu cho đến khi publish vào ChromaDB.

**File / module:**

- `docs/pipeline_architecture.md`: Xây dựng sơ đồ kiến trúc và ghi nhận các giới hạn kỹ thuật (hard-coded cutoff, lack of semantic drift detection).
- `docs/runbook.md`: Thiết lập quy trình 6 bước để chẩn đoán và xử lý khi pipeline gặp sự cố (Symptom → Detection → Diagnosis → Mitigation → Prevention).
- `monitoring/freshness_check.py`: Phối hợp với team để thống nhất tiêu chuẩn SLA 24 giờ và cách diễn giải PASS/WARN/FAIL trong tài liệu vận hành.
- `reports/group_report.md`: Đồng bộ nội dung quan sát (freshness/expectation/eval) để phần cá nhân bám sát bằng chứng chung của nhóm.

**Kết nối với thành viên khác:**
Tôi làm việc chặt chẽ với các thành viên trong nhóm để lấy tham số `latest_exported_at` cho việc đo độ tươi (freshness) và cộng tác với Quality Owner để ghi nhận các trường hợp "expectation halt" vào Runbook giúp các thành viên trong nhóm dễ dàng chẩn đoán lỗi khi on-call.

---

**Bằng chứng (commit / comment trong code):**
Commit: `e8461e4f53db1934b3fc1a0f70c0431ff6e0a30c` (edit pipeline architecture & runbook).

---

## 2. Một quyết định kỹ thuật (khoảng 150 từ)

Một quyết định quan trọng của tôi là việc thiết lập quy trình **"Debug Order"** chuẩn hóa trong Runbook theo trình tự: **Freshness → Volume → Schema → Lineage**. Thay vì để mọi người nhảy ngay vào kiểm tra nội dung chunk (semantic), tôi yêu cầu kiểm tra độ tươi và tính toàn vẹn của dữ liệu ở tầng ingest trước.

**Lý do:** Trong các hệ thống RAG thực tế, phần lớn lỗi không đến từ LLM mà đến từ việc dữ liệu nguồn bị trễ (stale) hoặc sai định dạng. Việc kiểm tra `freshness_check` trước giúp loại bỏ ngay các nghi ngờ về phiên bản dữ liệu. Tôi cũng đã đề xuất việc duy trì trạng thái **FAIL** cho dữ liệu cũ (121 giờ) thay vì nới rộng SLA lên 200 giờ để "làm đẹp" báo cáo. Điều này giúp giữ lại "tín hiệu thật" (real signal) để minh chứng rằng hệ thống giám sát đang hoạt động đúng chức năng cảnh báo khi dữ liệu vượt quá 24h quy định.

---

## 3. Một lỗi hoặc anomaly đã xử lý (khoảng 130 từ)

Tôi đã xử lý tình huống **Anomaly: Freshness SLA Failure** phát hiện trong quá trình chạy thử nghiệm Sprint 4.

**Triệu chứng:** Khi chạy lệnh kiểm tra freshness cho manifest `fix-good`, hệ thống trả về kết quả `FAIL`.
**Phát hiện:** `monitoring/freshness_check.py` báo cáo `age_hours: 121.32` trong khi `sla_hours: 24.0`.
**Chẩn đoán:** Dữ liệu raw mẫu `policy_export_dirty.csv` có ngày `latest_exported_at` là `2026-04-10`, trong khi thời điểm chạy test là `2026-04-15`.
**Xử lý:** Tôi đã cập nhật quy trình Mitigation trong `runbook.md`, hướng dẫn team cách rerun pipeline với run_id mới sau khi cập nhật ngày xuất file upstream. Tôi cũng ghi chú rõ trong báo cáo nhóm rằng đây là lỗi có chủ đích để kiểm thử khả năng quan sát (observability) của hệ thống.

---

## 4. Bằng chứng trước / sau (khoảng 100 từ)

Dưới đây là bằng chứng về việc phát hiện dữ liệu lỗi/stale thông qua các công cụ giám sát mà tôi đã thiết lập:

**Run ID:** `fix-good`
**Log freshness:**

```bash
$ python etl_pipeline.py freshness --manifest artifacts/manifests/manifest_fix-good.json
FAIL {"latest_exported_at": "2026-04-10T08:00:00", "age_hours": 121.32, "sla_hours": 24.0, "reason": "freshness_sla_exceeded"}
```

Ngoài ra, trong báo cáo `after_inject_bad.csv` (Scenario Sprint 3), tôi đã ghi nhận được câu hỏi `q_refund_window` có kết quả `hits_forbidden=yes` khi chưa áp dụng rule fix refund 14 ngày. Sau khi áp dụng rule vệ sinh dữ liệu, kết quả đổi thành `no`, chứng minh pipeline đã loại bỏ thành công các chunk cũ khỏi retrieval context.

---

## 5. Cải tiến tiếp theo (khoảng 70 từ)

Nếu có thêm 2 tiếng, tôi sẽ thực hiện việc **tự động hóa đẩy cảnh báo (Alerting)** qua Slack hoặc Email. Hiện tại, kết quả freshness mới chỉ xuất ra console; tôi muốn tích hợp Slack Webhook vào `monitoring/freshness_check.py` để gửi thông báo ngay lập tức khi một `expectation` bị `halt` hoặc khi dữ liệu bị stale. Ngoài ra, tôi sẽ chuyển các tham số hard-coded như `FAR_FUTURE_CUTOFF` vào file `data_contract.yaml` để quản lý tập trung và dễ dàng cập nhật theo phiên bản dữ liệu.

---
