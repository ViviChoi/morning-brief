"""Generic CSV importer with column-name autodetect.

Accepts any CSV containing one column matching each of: symbol, quantity, cost.
"""
from __future__ import annotations

import csv
import io


_SYMBOL_KEYS = {"symbol", "ticker", "asset", "instrument"}
_QTY_KEYS = {"qty", "quantity", "shares", "units", "amount"}
_COST_KEYS = {"cost", "avg_cost", "cost_basis", "average_price", "purchase_price", "price"}


def _find_column(headers: list[str], candidates: set[str]) -> str | None:
    norm = {h.lower().replace(" ", "_"): h for h in headers}
    for cand in candidates:
        if cand in norm:
            return norm[cand]
    return None


def parse_generic_csv(raw: bytes) -> list[dict]:
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []
    sym_col = _find_column(headers, _SYMBOL_KEYS)
    qty_col = _find_column(headers, _QTY_KEYS)
    cost_col = _find_column(headers, _COST_KEYS)
    if not (sym_col and qty_col and cost_col):
        raise ValueError(
            f"CSV missing required columns. Found {headers!r}. "
            f"Need one of {_SYMBOL_KEYS} + {_QTY_KEYS} + {_COST_KEYS}."
        )
    out: list[dict] = []
    for row in reader:
        try:
            out.append({
                "symbol": row[sym_col].strip().upper(),
                "qty": float(row[qty_col]),
                "cost": float(row[cost_col]),
            })
        except (ValueError, KeyError):
            continue
    return out
