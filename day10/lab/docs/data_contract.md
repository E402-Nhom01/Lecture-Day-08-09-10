# Data contract — Lab Day 10

> Bắt đầu từ `contracts/data_contract.yaml` — mở rộng và đồng bộ file này.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| `data/raw/policy_export_dirty.csv` (export từ hệ policy master) | DictReader UTF-8, batch đầy đủ mỗi run | Duplicate, doc_id lạ, ngày không ISO, conflict version HR 10/12, refund stale 14 ngày | `raw_records` vs `cleaned_records` (gap = quarantine_records); `freshness_check` trên `latest_exported_at` |
| `data/raw/policy_export_inject_rules.csv` (kịch bản kiểm rule mới Sp4.1) | Cùng loader | Mojibake `\ufffd`, exported_at non-ISO, effective_date 2099 | `quarantine_records` tăng ≥3 so với baseline; reason khớp R7/R8/R9 |
| `data/docs/*.txt` (canonical Day 09 — 4 tài liệu) | Không ingest trực tiếp; là source-of-truth để đối chiếu | Lệch version với CSV export | So khớp manual khi update allowlist |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | `{doc_id}_{seq}_{sha256[:16]}` — stable qua run |
| doc_id | string | Có | Phải thuộc allowlist `ALLOWED_DOC_IDS` |
| chunk_text | string | Có | NFKC + strip BOM/ZWSP; min_length 8 (warn), không U+FFFD (halt R7) |
| effective_date | date | Có | ISO `YYYY-MM-DD`; quarantine nếu rỗng/sai format/xa tương lai (>2028-01-01) |
| exported_at | datetime | Có | ISO 8601 (regex `^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}...`); sai → quarantine (R8) |

---

## 3. Quy tắc quarantine vs drop

- **Quarantine (giữ lại, có thể xét lại)**: ghi vào `artifacts/quarantine/quarantine_<run_id>.csv` kèm cột `reason`. KHÔNG embed. Owner nhóm review theo batch — nếu fix được (vd sửa encoding nguồn) thì merge lại vào raw round sau.
- **Drop (không ghi)**: hiện pipeline **không drop im lặng** — mọi record bị loại đều được log với reason, để reviewer truy xuất được. Đây là nguyên tắc observability.
- **Approve merge lại**: Cleaning & Quality Owner chạy lại pipeline sau khi fix raw → kiểm tra `quarantine_records` giảm → commit evidence.

**Reason codes hiện có:**
`unknown_doc_id`, `missing_effective_date`, `invalid_effective_date_format`, `stale_hr_policy_effective_date`, `missing_chunk_text`, `duplicate_chunk_text`, `mojibake_detected` (R7), `invalid_exported_at_format` (R8), `effective_date_far_future` (R9).

---

## 4. Phiên bản & canonical

- **Source of truth policy refund:** `data/docs/policy_refund_v4.txt` — cửa sổ hoàn tiền **7 ngày** làm việc. Mọi chunk `policy_refund_v4` trong export CSV phải khớp; nếu xuất hiện "14 ngày làm việc" → rule `apply_refund_window_fix` tự replace thành "7 ngày làm việc [cleaned: stale_refund_window]", đồng thời expectation `refund_no_stale_14d_window` halt nếu fix không chạy.
- **Source of truth HR leave:** `data/docs/hr_leave_policy.txt` — bản 2026, **12 ngày phép năm** cho nhân viên < 3 năm kinh nghiệm. Chunk có `effective_date < 2026-01-01` bị quarantine (`stale_hr_policy_effective_date`) — giữ bản cũ khỏi Chroma. Expectation `hr_leave_has_current_2026_version` là positive invariant: halt nếu clean quá tay làm mất cả bản mới.
- **Versioning cutoff:** `hr_leave_min_effective_date: "2026-01-01"` và `FAR_FUTURE_CUTOFF = "2028-01-01"` hiện hard-code — planned move sang env/YAML.
