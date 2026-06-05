"""Market data fetchers. Each function is independent; all return None on error.

Callers compose: a partial dict with `None` values is preferable to crashing.
"""
from __future__ import annotations

import requests

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
