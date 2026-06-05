"""Broker auto-detection + dispatch.

Returns (broker_name, positions_list). Each importer module is independent.
"""
from __future__ import annotations

from . import generic, ibkr, binance, coinbase


def _peek_text(raw: bytes, n: int = 4096) -> str:
    return raw[:n].decode("utf-8-sig", errors="ignore")


def detect_and_parse(raw: bytes) -> tuple[str, list[dict]]:
    head = _peek_text(raw)
    first_line = head.splitlines()[0] if head else ""
    if first_line.startswith("Statement,Header") or ",Header," in head[:1000]:
        try:
            return "ibkr", ibkr.parse_ibkr_csv(raw)
        except Exception:
            pass
    if "Pair" in head[:500] and "Executed" in head[:500]:
        try:
            return "binance", binance.parse_binance_csv(raw)
        except Exception:
            pass
    if "Transaction Type" in head[:500] and "Quantity Transacted" in head[:500]:
        try:
            return "coinbase", coinbase.parse_coinbase_csv(raw)
        except Exception:
            pass
    return "generic", generic.parse_generic_csv(raw)
