"""Coinbase / Coinbase Pro Account CSV importer.

Same buy/sell aggregation strategy as binance.py — weighted avg of buy fills.
"""
from __future__ import annotations

import csv
import io


def parse_coinbase_csv(raw: bytes) -> list[dict]:
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    by_asset: dict[str, dict] = {}
    for row in reader:
        try:
            tx_type = row["Transaction Type"].upper()
            asset = row["Asset"].upper()
            qty = float(row["Quantity Transacted"])
            price = float(row["Spot Price at Transaction"])
        except (KeyError, ValueError):
            continue
        agg = by_asset.setdefault(asset, {"qty": 0.0, "buy_qty": 0.0, "buy_cost_sum": 0.0})
        if tx_type == "BUY":
            agg["qty"] += qty
            agg["buy_qty"] += qty
            agg["buy_cost_sum"] += qty * price
        elif tx_type == "SELL":
            agg["qty"] -= qty
    out: list[dict] = []
    for asset, a in by_asset.items():
        if a["qty"] <= 0 or a["buy_qty"] <= 0:
            continue
        out.append({"symbol": asset, "qty": a["qty"], "cost": a["buy_cost_sum"] / a["buy_qty"]})
    return out
