"""Market data fetchers. Each function is independent; all return None on error.

Callers compose: a partial dict with `None` values is preferable to crashing.
"""
from __future__ import annotations

import requests
import yfinance as yf

_TIMEOUT = 10


def fetch_crypto_fng() -> dict | None:
    try:
        r = requests.get("https://api.alternative.me/fng/", timeout=_TIMEOUT)
        r.raise_for_status()
        item = r.json()["data"][0]
        return {
            "value": int(item["value"]),
            "classification": item["value_classification"],
        }
    except Exception:
        return None


def fetch_crypto_prices(coingecko_ids: list[str]) -> dict:
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": ",".join(coingecko_ids),
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            },
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        raw = r.json()
        return {
            cg_id: {
                "price_usd": data["usd"],
                "change_24h_pct": data.get("usd_24h_change", 0.0),
            }
            for cg_id, data in raw.items()
        }
    except Exception:
        return {}


def fetch_equity_quotes(symbols: list[str]) -> dict:
    out: dict[str, dict] = {}
    for sym in symbols:
        try:
            hist = yf.Ticker(sym).history(period="5d", interval="1d")
            if hist.empty or len(hist) < 2:
                continue
            close_today = float(hist["Close"].iloc[-1])
            close_prev = float(hist["Close"].iloc[-2])
            change_pct = (close_today - close_prev) / close_prev * 100.0
            out[sym] = {
                "price": close_today,
                "prev_close": close_prev,
                "change_pct": change_pct,
            }
        except Exception:
            continue
    return out
