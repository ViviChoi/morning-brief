"""BTC bottom score: 0-100 (0 = extreme fear, 100 = extreme greed).

Weighted from 4 daily indicators (full Day1Global model uses 13, the other 9
are paid on-chain metrics deferred to P2).
"""
from __future__ import annotations

WEIGHTS = {
    "etf_net_flow": 0.38,
    "funding_rate": 0.25,
    "fng": 0.22,
    "long_short": 0.15,
}


def _score_etf_flow(musd: float | None) -> float | None:
    """Map daily net flow (USD millions) to 0-100.
    Heuristic: -500 → 0 (extreme fear), 0 → 50, +500 → 100 (extreme greed).
    """
    if musd is None:
        return None
    score = 50.0 + (musd / 500.0) * 50.0
    return max(0.0, min(100.0, score))


def _score_funding(rate: float | None) -> float | None:
    """Map funding rate to 0-100. -0.0005 → 0, 0 → 50, +0.0005 → 100."""
    if rate is None:
        return None
    score = 50.0 + (rate / 0.0005) * 50.0
    return max(0.0, min(100.0, score))


def _score_fng(value: int | None) -> float | None:
    """F&G index is already 0-100."""
    if value is None:
        return None
    return float(max(0, min(100, value)))


def _score_long_short(ratio: float | None) -> float | None:
    """L/S ratio: 0.5 → 0, 1.0 → 50, 2.0 → 100. Logarithmic feel."""
    if ratio is None:
        return None
    import math
    score = 50.0 + math.log2(ratio) * 50.0
    return max(0.0, min(100.0, score))


def _rating(score: float) -> str:
    if score <= 15: return "Extreme Fear"
    if score <= 45: return "Fear"
    if score <= 55: return "Neutral"
    if score <= 85: return "Greed"
    return "Extreme Greed"


def btc_bottom_score(
    etf_net_flow_musd: float | None,
    funding_rate: float | None,
    fng_value: int | None,
    long_short_ratio: float | None,
) -> dict:
    components = {
        "etf_net_flow": _score_etf_flow(etf_net_flow_musd),
        "funding_rate": _score_funding(funding_rate),
        "fng": _score_fng(fng_value),
        "long_short": _score_long_short(long_short_ratio),
    }
    available = {k: v for k, v in components.items() if v is not None}
    if not available:
        return {
            "components": components,
            "total": None,
            "rating": "Unknown",
            "partial": True,
        }
    weight_sum = sum(WEIGHTS[k] for k in available)
    total = sum(v * WEIGHTS[k] for k, v in available.items()) / weight_sum
    return {
        "components": components,
        "total": round(total, 1),
        "rating": _rating(total),
        "partial": len(available) < 4,
    }
