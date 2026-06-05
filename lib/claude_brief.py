"""Claude wrapper for the daily Surface A commentary.

Inputs: a snapshot dict (from fetch.run + score). Output: a `commentary` dict
of strings ready for templating.

The prompt asks Claude to produce a fixed set of sections, separated by
labeled markers, so parsing is robust and version-independent.
"""
from __future__ import annotations

import re
from anthropic import Anthropic


_SYSTEM = (
    "You are a calm, plain-language market briefing writer for a financial novice. "
    "Avoid jargon. When unavoidable, define it parenthetically the first time. "
    "Output ONLY the labeled sections requested. Do not add introductions or sign-offs."
)


def _user_prompt(snapshot: dict) -> str:
    return f"""Produce a daily market brief using the data below. Return EXACTLY these labeled sections:

HEADLINE: <one sentence, the day in plain language, no jargon>

LIQUIDITY_TONE: <one sentence describing today's liquidity / risk appetite>

TICKERS:
- <symbol>: <one short sentence thesis>
(one bullet per ticker in the equity and crypto blocks below)

BTC_NARRATIVE: <2-3 sentences interpreting the BTC bottom score and what it means for a long-term holder>

TOP_10:
1. <topic — one short sentence of context — actionable hint>
...
10. ...

DATA:
{snapshot}
"""


def _parse_sections(text: str) -> dict:
    def grab(label: str, until: str | None) -> str:
        if until:
            m = re.search(rf"{label}:\s*(.+?)(?={until}:)", text, re.DOTALL)
        else:
            m = re.search(rf"{label}:\s*(.+)$", text, re.DOTALL)
        return m.group(1).strip() if m else ""

    return {
        "headline": grab("HEADLINE", "LIQUIDITY_TONE"),
        "liquidity_tone": grab("LIQUIDITY_TONE", "TICKERS"),
        "tickers_text": grab("TICKERS", "BTC_NARRATIVE"),
        "btc_narrative": grab("BTC_NARRATIVE", "TOP_10"),
        "top_10": grab("TOP_10", None),
        "error": None,
    }


def compose(snapshot: dict, api_key: str, model: str) -> dict:
    try:
        client = Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=2000,
            system=_SYSTEM,
            messages=[{"role": "user", "content": _user_prompt(snapshot)}],
        )
        text = "".join(block.text for block in msg.content if getattr(block, "type", "") == "text")
        return _parse_sections(text)
    except Exception as exc:
        return {
            "headline": "AI commentary unavailable today.",
            "liquidity_tone": "",
            "tickers_text": "",
            "btc_narrative": "",
            "top_10": "",
            "error": str(exc),
        }
