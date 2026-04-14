"""
workers/synthesis.py — Synthesis Worker
Sprint 2: Tổng hợp câu trả lời từ retrieved_chunks và policy_result.

Input (từ AgentState):
    - task: câu hỏi
    - retrieved_chunks: evidence từ retrieval_worker
    - policy_result: kết quả từ policy_tool_worker

Output (vào AgentState):
    - final_answer: câu trả lời cuối với citation
    - sources: danh sách nguồn tài liệu được cite
    - confidence: mức độ tin cậy (0.0 - 1.0)

Gọi độc lập để test:
    python workers/synthesis.py
"""

import os

WORKER_NAME = "synthesis_worker"

SYSTEM_PROMPT = """Bạn là trợ lý IT Helpdesk nội bộ.

Quy tắc nghiêm ngặt:
1. CHỈ trả lời dựa vào context được cung cấp. KHÔNG dùng kiến thức ngoài.
2. Nếu context không đủ để trả lời → nói rõ "Không đủ thông tin trong tài liệu nội bộ".
3. Trích dẫn nguồn cuối mỗi câu quan trọng: [tên_file].
4. Trả lời súc tích, có cấu trúc. Không dài dòng.
5. Nếu có exceptions/ngoại lệ → nêu rõ ràng trước khi kết luận.
"""


def _call_llm(messages: list) -> str:
    """
    Gọi LLM để tổng hợp câu trả lời.
    TODO Sprint 2: Implement với OpenAI hoặc Gemini.
    """
    # Option A: OpenAI
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,  # Low temperature để grounded
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception:
        pass

    # Option B: Gemini
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash")
        combined = "\n".join([m["content"] for m in messages])
        response = model.generate_content(combined)
        return response.text
    except Exception:
        pass

    # Fallback: trả về message báo lỗi (không hallucinate)
    return "[SYNTHESIS ERROR] Không thể gọi LLM. Kiểm tra API key trong .env."


def _build_context(chunks: list, policy_result: dict) -> str:
    """Xây dựng context string từ chunks và policy result."""
    parts = []

    if chunks:
        parts.append("=== TÀI LIỆU THAM KHẢO ===")
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("source", "unknown")
            text = chunk.get("text", "")
            score = chunk.get("score", 0)
            parts.append(f"[{i}] Nguồn: {source} (relevance: {score:.2f})\n{text}")

    if policy_result and policy_result.get("exceptions_found"):
        parts.append("\n=== POLICY EXCEPTIONS ===")
        for ex in policy_result["exceptions_found"]:
            parts.append(f"- {ex.get('rule', '')}")

    if not parts:
        return "(Không có context)"

    return "\n\n".join(parts)


_JUDGE_PROMPT = """Bạn là Judge đánh giá chất lượng câu trả lời của hệ RAG.
Chấm theo 4 tiêu chí, mỗi tiêu chí float từ 0.0 đến 1.0.

1. faithfulness — Câu trả lời CHỈ dùng thông tin trong CONTEXT? (1.0 = hoàn toàn grounded, 0.0 = hallucinate hoàn toàn)
2. relevance — Câu trả lời có address đúng câu hỏi không? (1.0 = trả lời trọng tâm, 0.0 = lạc đề)
3. correctness — Các facts trong câu trả lời có đúng với CONTEXT không? (1.0 = mọi fact đều khớp, 0.0 = sai lệch)
4. completeness — Có bao phủ đủ các điểm quan trọng để trả lời câu hỏi không? (1.0 = đầy đủ, 0.0 = bỏ sót hoàn toàn)

Quy tắc:
- Nếu answer là abstain ("Không đủ thông tin...") và CONTEXT thật sự không đủ → faithfulness=1.0, correctness=1.0, relevance~0.6, completeness~0.3
- Nếu answer là abstain nhưng CONTEXT ĐỦ để trả lời → penalize completeness và relevance thấp
- Nếu answer có citation [source] → không cộng điểm thêm, đó là yêu cầu tối thiểu

Trả về ĐÚNG JSON format:
{"faithfulness": 0.0, "relevance": 0.0, "correctness": 0.0, "completeness": 0.0, "note": "<1 câu giải thích>"}
"""


def _llm_judge_scores(task: str, answer: str, chunks: list) -> dict:
    """
    LLM-as-Judge — chấm 4 tiêu chí RAG. Trả về dict với 4 floats + note.
    Nếu LLM fail, trả về dict rỗng (caller sẽ fallback heuristic).
    """
    context = "\n\n".join(
        f"[{i+1}] {c.get('source','?')}: {c.get('text','')[:500]}"
        for i, c in enumerate(chunks[:5])
    ) or "(Không có context)"

    user_prompt = (
        f"CÂU HỎI:\n{task}\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"CÂU TRẢ LỜI:\n{answer}\n\n"
        f"Chấm theo 4 tiêu chí và trả về JSON."
    )

    # Option A: OpenAI
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _JUDGE_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=200,
        )
        import json as _json
        return _json.loads(resp.choices[0].message.content)
    except Exception:
        pass

    # Option B: Gemini
    try:
        import google.generativeai as genai
        import json as _json
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash")
        raw = model.generate_content(_JUDGE_PROMPT + "\n\n" + user_prompt).text
        start, end = raw.find("{"), raw.rfind("}") + 1
        return _json.loads(raw[start:end])
    except Exception:
        return {}


def _estimate_confidence(
    chunks: list, answer: str, policy_result: dict, task: str = ""
) -> tuple[float, dict]:
    """
    Tính confidence + trả về 4 metrics từ LLM-as-Judge.

    Returns:
        (confidence: float, judge_scores: dict với 4 keys + note)

    Khi LLM judge thất bại → fallback heuristic cũ, judge_scores={}.
    """
    judge: dict = {}

    # Hard guard: no chunks → low confidence, skip judge
    if not chunks:
        return 0.1, {}

    abstained = ("không đủ thông tin" in answer.lower()
                 or "không có trong tài liệu" in answer.lower())

    # Gọi LLM judge khi có task (được gọi từ synthesize → task có sẵn)
    if task:
        judge = _llm_judge_scores(task, answer, chunks)

    if judge and all(k in judge for k in ("faithfulness", "relevance", "correctness", "completeness")):
        # Weighted: faithfulness + correctness quan trọng nhất (anti-hallucinate)
        f, r, c, cp = (
            float(judge.get("faithfulness", 0)),
            float(judge.get("relevance", 0)),
            float(judge.get("correctness", 0)),
            float(judge.get("completeness", 0)),
        )
        confidence = 0.3 * f + 0.2 * r + 0.3 * c + 0.2 * cp
        confidence = round(min(0.95, max(0.05, confidence)), 2)
        return confidence, judge

    # Fallback heuristic cũ khi LLM judge không chạy được
    if abstained:
        return 0.3, {}

    avg_score = sum(c.get("score", 0) for c in chunks) / len(chunks)
    exception_penalty = 0.05 * len(policy_result.get("exceptions_found", []))
    confidence = min(0.95, avg_score - exception_penalty)
    return round(max(0.1, confidence), 2), {}


def synthesize(task: str, chunks: list, policy_result: dict) -> dict:
    """
    Tổng hợp câu trả lời từ chunks và policy context.

    Returns:
        {"answer": str, "sources": list, "confidence": float}
    """

    # ✅ HARD GUARD: no chunks → abstain immediately (avoid hallucination)
    if not chunks:
        return {
            "answer": "Không đủ thông tin trong tài liệu nội bộ.",
            "sources": [],
            "confidence": 0.1,
        }

    context = _build_context(chunks, policy_result)

    # ✅ Stronger user instruction
    user_prompt = f"""
Câu hỏi: {task}

{context}

Yêu cầu:
- Chỉ sử dụng thông tin trong phần "TÀI LIỆU THAM KHẢO"
- Không suy diễn, không bổ sung kiến thức ngoài
- Nếu thông tin không đủ → trả lời: "Không đủ thông tin trong tài liệu nội bộ"
- Mỗi ý quan trọng phải có citation dạng [tên_file]

Trả lời:
"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    answer = _call_llm(messages)

    # ✅ Post-process: ensure answer is not empty
    if not answer or len(answer.strip()) < 5:
        answer = "Không đủ thông tin trong tài liệu nội bộ."

    # ✅ Extract sources (unique)
    sources = list({c.get("source", "unknown") for c in chunks})

    # ✅ Enforce citation if missing
    if sources and not any(src in answer for src in sources):
        answer += "\n\n[Nguồn: " + ", ".join(sources) + "]"

    confidence, judge_scores = _estimate_confidence(chunks, answer, policy_result, task=task)

    return {
        "answer": answer.strip(),
        "sources": sources,
        "confidence": confidence,
        "judge_scores": judge_scores,
    }

def run(state: dict) -> dict:
    """
    Worker entry point — gọi từ graph.py.
    """
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    policy_result = state.get("policy_result", {})

    state.setdefault("workers_called", [])
    state.setdefault("history", [])
    state["workers_called"].append(WORKER_NAME)

    worker_io = {
        "worker": WORKER_NAME,
        "input": {
            "task": task,
            "chunks_count": len(chunks),
            "has_policy": bool(policy_result),
        },
        "output": None,
        "error": None,
    }

    try:
        result = synthesize(task, chunks, policy_result)
        state["final_answer"] = result["answer"]
        state["sources"] = result["sources"]
        state["confidence"] = result["confidence"]
        state["judge_scores"] = result.get("judge_scores", {})

        worker_io["output"] = {
            "answer_length": len(result["answer"]),
            "sources": result["sources"],
            "confidence": result["confidence"],
            "judge_scores": result.get("judge_scores", {}),
        }
        state["history"].append(
            f"[{WORKER_NAME}] confidence={result['confidence']}, "
            f"judge={result.get('judge_scores', {})}, sources={result['sources']}"
        )

    except Exception as e:
        worker_io["error"] = {"code": "SYNTHESIS_FAILED", "reason": str(e)}
        state["final_answer"] = f"SYNTHESIS_ERROR: {e}"
        state["confidence"] = 0.0
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    state.setdefault("worker_io_logs", []).append(worker_io)
    return state


# ─────────────────────────────────────────────
# Test độc lập
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Synthesis Worker — Standalone Test")
    print("=" * 50)

    test_state = {
        "task": "SLA ticket P1 là bao lâu?",
        "retrieved_chunks": [
            {
                "text": "Ticket P1: Phản hồi ban đầu 15 phút kể từ khi ticket được tạo. Xử lý và khắc phục 4 giờ. Escalation: tự động escalate lên Senior Engineer nếu không có phản hồi trong 10 phút.",
                "source": "sla_p1_2026.txt",
                "score": 0.92,
            }
        ],
        "policy_result": {},
    }

    result = run(test_state.copy())
    print(f"\nAnswer:\n{result['final_answer']}")
    print(f"\nSources: {result['sources']}")
    print(f"Confidence: {result['confidence']}")

    print("\n--- Test 2: Exception case ---")
    test_state2 = {
        "task": "Khách hàng Flash Sale yêu cầu hoàn tiền vì lỗi nhà sản xuất.",
        "retrieved_chunks": [
            {
                "text": "Ngoại lệ: Đơn hàng Flash Sale không được hoàn tiền theo Điều 3 chính sách v4.",
                "source": "policy_refund_v4.txt",
                "score": 0.88,
            }
        ],
        "policy_result": {
            "policy_applies": False,
            "exceptions_found": [{"type": "flash_sale_exception", "rule": "Flash Sale không được hoàn tiền."}],
        },
    }
    result2 = run(test_state2.copy())
    print(f"\nAnswer:\n{result2['final_answer']}")
    print(f"Confidence: {result2['confidence']}")

    print("\n✅ synthesis_worker test done.")