"""Portfolio valuation + allocation. Pure functions.

`value_positions(raw_positions, prices)` enriches each position with current
value and P&L. `allocation_breakdown(valued)` returns weight per symbol.
"""
from __future__ import annotations


def value_positions(positions: list[dict], prices: dict[str, float]) -> list[dict]:
    out: list[dict] = []
    for p in positions:
        sym = p["symbol"]
        if sym not in prices:
            continue
        price = prices[sym]
        current_value = price * p["qty"]
        cost_value = p["cost"] * p["qty"]
        pnl_abs = current_value - cost_value
        pnl_pct = ((price / p["cost"]) - 1.0) * 100.0 if p["cost"] else 0.0
        out.append({
            **p,
            "current_price": price,
            "current_value": current_value,
            "cost_value": cost_value,
            "pnl_abs": pnl_abs,
            "pnl_pct": pnl_pct,
        })
    return out


def allocation_breakdown(valued_positions: list[dict]) -> list[dict]:
    total = sum(p["current_value"] for p in valued_positions)
    if total <= 0:
        return []
    return [
        {"symbol": p["symbol"], "weight": p["current_value"] / total, "value": p["current_value"]}
        for p in valued_positions
    ]
