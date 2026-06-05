"""Plain-language portfolio explanation for a financial novice.

Output sections:
- what_you_hold (1 sentence)
- working / not_working (bullet lists)
- watch (1-2 sentences)
"""
from __future__ import annotations

import re
from anthropic import Anthropic


_SYSTEM = (
    "You are a calm financial explainer for someone who does NOT read finance well. "
    "Use plain language. If you must use a technical term, define it in parentheses on first use. "
    "Output ONLY the labeled sections requested. No introductions, no sign-offs."
)


def _user_prompt(positions: list[dict]) -> str:
    return f"""Given the portfolio below, produce EXACTLY these labeled sections.

WHAT_YOU_HOLD: <one sentence summary of the portfolio's character>

WORKING:
- <symbol>: <what is going well, one short clause>
(only positions with positive pnl_pct)

NOT_WORKING:
- <symbol>: <what is going wrong, one short clause>
(only positions with negative pnl_pct; write "(none today)" if empty)

WATCH: <1-2 sentences. Flag concentration risk, sector exposure, or any obvious imbalance. No jargon.>

POSITIONS: {positions}
"""


def _parse(text: str) -> dict:
    def grab(label: str, until: str | None) -> str:
        if until:
            m = re.search(rf"{label}:\s*(.+?)(?={until}:)", text, re.DOTALL)
        else:
            m = re.search(rf"{label}:\s*(.+)$", text, re.DOTALL)
        return m.group(1).strip() if m else ""

    return {
        "what_you_hold": grab("WHAT_YOU_HOLD", "WORKING"),
        "working": grab("WORKING", "NOT_WORKING"),
        "not_working": grab("NOT_WORKING", "WATCH"),
        "watch": grab("WATCH", None),
        "error": None,
    }


def explain_portfolio(positions: list[dict], api_key: str, model: str) -> dict:
    try:
        client = Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=1000,
            system=_SYSTEM,
            messages=[{"role": "user", "content": _user_prompt(positions)}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        return _parse(text)
    except Exception as exc:
        return {
            "what_you_hold": "Portfolio explanation unavailable right now.",
            "working": "", "not_working": "", "watch": "",
            "error": str(exc),
        }
