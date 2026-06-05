"""IBKR Activity Statement CSV importer.

IBKR statements are multi-section CSVs where each row begins with the section
name (e.g. 'Positions'). We extract rows from the 'Positions' section only.
"""
from __future__ import annotations

import csv
import io


def parse_ibkr_csv(raw: bytes) -> list[dict]:
    text = raw.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    out: list[dict] = []
    header: list[str] | None = None
    for row in rows:
        if not row or row[0] != "Positions":
            continue
        if row[1] == "Header":
            header = row[2:]
            continue
        if row[1] != "Data" or header is None:
            continue
        record = dict(zip(header, row[2:]))
        try:
            symbol = record.get("Symbol", "").strip().upper()
            qty = float(record["Quantity"])
            total_cost = float(record["Cost Basis"])
            if not symbol or qty == 0:
                continue
            out.append({
                "symbol": symbol,
                "qty": qty,
                "cost": total_cost / qty,
            })
        except (KeyError, ValueError):
            continue
    return out
