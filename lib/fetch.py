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
