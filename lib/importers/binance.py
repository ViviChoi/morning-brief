"""Binance Trade History CSV importer.

Aggregates buys minus sells per base asset; cost basis is the weighted avg of
buy fills only (sells reduce qty but do not recompute avg cost — standard FIFO
approximation suitable for a dashboard, not for tax filing).
"""
from __future__ import annotations

import csv
import io


def parse_binance_csv(raw: bytes) -> list[dict]:
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    by_base: dict[str, dict] = {}
    for row in reader:
        try:
            pair = row["Pair"].upper().replace("/", "")
            side = row["Side"].upper()
            price = float(row["Price"])
            qty = float(row["Executed"])
        except (KeyError, ValueError):
            continue
        base = _split_base(pair)
        if base is None:
            continue
        agg = by_base.setdefault(base, {"qty": 0.0, "buy_qty": 0.0, "buy_cost_sum": 0.0})
        if side == "BUY":
            agg["qty"] += qty
            agg["buy_qty"] += qty
            agg["buy_cost_sum"] += qty * price
        elif side == "SELL":
            agg["qty"] -= qty
    out: list[dict] = []
    for base, a in by_base.items():
        if a["qty"] <= 0 or a["buy_qty"] <= 0:
            continue
        out.append({
            "symbol": base,
            "qty": a["qty"],
            "cost": a["buy_cost_sum"] / a["buy_qty"],
        })
    return out


_QUOTES = ("USDT", "BUSD", "USDC", "FDUSD", "BTC", "ETH", "BNB")


def _split_base(pair: str) -> str | None:
    for q in _QUOTES:
        if pair.endswith(q) and len(pair) > len(q):
            return pair[: -len(q)]
    return None
