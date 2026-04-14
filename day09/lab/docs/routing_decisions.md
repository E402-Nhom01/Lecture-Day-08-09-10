# Routing Decisions Log — Lab Day 09

**Nhóm:** E402 - Nhóm 1 
**Ngày:** 2026-04-14

> **Hướng dẫn:** Ghi lại ít nhất **3 quyết định routing** thực tế từ trace của nhóm.
> Không ghi giả định — phải từ trace thật (`artifacts/traces/`).
> 
> Mỗi entry phải có: task đầu vào → worker được chọn → route_reason → kết quả thực tế.

---

## Routing Decision #1

**Task đầu vào:**
> Đúng theo SLA, ai nhận thông báo đầu tiên và qua kênh nào? Deadline escalation là mấy giờ?

**Worker được chọn:** `retrieval_worker`  
**Route reason (từ trace):** `retrieval keyword matched: ['p1', 'sla', 'ticket', 'escalation'] | risk_high: emergency signal`  
**MCP tools được gọi:** `[]`  
**Workers called sequence:** `['retrieval_worker', 'synthesis_worker']`

**Kết quả thực tế:**
- final_answer (ngắn): On-call engineer nhận thông báo qua Slack + email, deadline escalation 22:57.
- confidence: `0.95`
- Correct routing? **Yes**

**Nhận xét:** _(Routing này đúng hay sai? Nếu sai, nguyên nhân là gì?)_

Đúng. Câu hỏi thiên về SLA/ticket/escalation nên retrieval-first là hợp lý.

---

## Routing Decision #2

**Task đầu vào:**
> Khách hàng đặt đơn 31/01/2026, yêu cầu hoàn tiền ngày 07/02/2026 vì lỗi NSX. Chính sách nào áp dụng và có hoàn tiền không?

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `policy keyword ['hoàn tiền', 'flash sale'] + exception signal ['flash sale', 'kỹ thuật số']`  
**MCP tools được gọi:** `[null]`  
**Workers called sequence:** `['policy_tool_worker', 'synthesis_worker']`

**Kết quả thực tế:**
- final_answer (ngắn): Áp dụng policy v3 (đơn trước 01/02/2026), không đủ thông tin để kết luận hoàn tiền.
- confidence: `0.48`
- Correct routing? **Yes**

**Nhận xét:**

Đúng hướng policy; tuy nhiên route_reason có tín hiệu “flash sale/kỹ thuật số” chưa thật khớp câu hỏi, cần làm sạch signal extraction.

---

## Routing Decision #3

**Task đầu vào:**
> Khi khách hàng chọn store credit thay vì hoàn tiền, họ nhận bao nhiêu % so với tiền gốc?

**Worker được chọn:** `retrieval_worker`  
**Route reason (từ trace):** `policy keyword ['hoàn tiền'] but no exception signal → retrieval fact`  
**MCP tools được gọi:** `[]`  
**Workers called sequence:** `['retrieval_worker', 'synthesis_worker']`

**Kết quả thực tế:**
- final_answer (ngắn): Nhận `110%` store credit so với số tiền gốc cần hoàn.
- confidence: `0.05`
- Correct routing? **Yes** (theo rule hiện tại)

**Nhận xét:**

Dù trả lời đúng fact, confidence rất thấp (0.05) cho thấy confidence calibration chưa tốt.

---

## Routing Decision #4 (tuỳ chọn — bonus)

**Task đầu vào:**
> Sự cố P1 lúc 2am + cần cấp Level 2 access tạm thời cho contractor để emergency fix.

**Worker được chọn:** `policy_tool_worker`  
**Route reason:** `policy keyword ['level 2'] + exception signal ['level 2', 'emergency', 'contractor'] | risk_high: emergency signal`

**Nhận xét: Đây là trường hợp routing khó nhất trong lab. Tại sao?**

Vì câu hỏi multi-hop: vừa SLA incident response vừa access control emergency. Nếu route sai sẽ thiếu 1 nửa thông tin.

---

## Tổng kết

### Routing Distribution

| Worker | Số câu được route | % tổng |
|--------|------------------|--------|
| retrieval_worker | 6 | 60% |
| policy_tool_worker | 4 | 40% |
| human_review | 0 | 0% |

### Routing Accuracy

> Trong số X câu nhóm đã chạy, bao nhiêu câu supervisor route đúng?

- Câu route đúng: **10 / 10** (theo rule routing hiện tại của nhóm)
- Câu route sai (đã sửa bằng cách nào?): **0**
- Câu trigger HITL: **0**

### Lesson Learned về Routing

> Quyết định kỹ thuật quan trọng nhất nhóm đưa ra về routing logic là gì?  
> (VD: dùng keyword matching vs LLM classifier, threshold confidence cho HITL, v.v.)

1. Dùng **rule-based keyword routing** làm baseline để dễ debug và giải thích route.
2. Gắn **risk signal** trong route_reason (emergency/unknown) để mở đường cho HITL ở vòng sau.

### Route Reason Quality

> Nhìn lại các `route_reason` trong trace — chúng có đủ thông tin để debug không?  
> Nếu chưa, nhóm sẽ cải tiến format route_reason thế nào?

Đủ để debug cơ bản, nhưng chưa nhất quán. Nhóm sẽ chuẩn hóa dạng có cấu trúc: `intent_signals`, `risk_signals`, `fallback_rule`, `decision_confidence`.
