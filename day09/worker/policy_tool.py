"""Basic policy gate for Day 09 MCP demo.

This is intentionally simple: it blocks requests that look like PII or payroll data.
"""

from __future__ import annotations

from typing import Dict


BLOCKLIST_KEYWORDS = [
    "salary",
    "payroll",
    "ssn",
    "social security",
    "credit card",
    "bank account",
    "address",
    "phone number",
]


def policy_check(query: str) -> Dict[str, str | bool]:
    if not query or not query.strip():
        return {
            "allowed": False,
            "reason": "empty_query",
        }

    lowered = query.lower()
    for keyword in BLOCKLIST_KEYWORDS:
        if keyword in lowered:
            return {
                "allowed": False,
                "reason": f"blocked_keyword:{keyword}",
            }

    return {
        "allowed": True,
        "reason": "ok",
    }
