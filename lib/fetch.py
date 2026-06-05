"""Market data fetchers. Each function is independent; all return None on error.

Callers compose: a partial dict with `None` values is preferable to crashing.
"""
from __future__ import annotations

import requests
import yfinance as yf
from bs4 import BeautifulSoup

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


def fetch_btc_funding_rate() -> float | None:
    try:
        r = requests.get(
            "https://fapi.binance.com/fapi/v1/premiumIndex",
            params={"symbol": "BTCUSDT"},
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            data = data[0]
        return float(data["lastFundingRate"])
    except Exception:
        return None


def fetch_btc_long_short_ratio() -> float | None:
    try:
        r = requests.get(
            "https://fapi.binance.com/futures/data/globalLongShortAccountRatio",
            params={"symbol": "BTCUSDT", "period": "1d", "limit": 1},
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        return float(data[0]["longShortRatio"])
    except Exception:
        return None


def fetch_btc_etf_net_flow_musd() -> float | None:
    """Return today's (latest row) total BTC ETF net flow in millions of USD.

    Farside lists newest day at the top of the data rows. We pick the first data row.
    """
    try:
        r = requests.get(
            "https://farside.co.uk/bitcoin-etf-flow-all-data/",
            headers={"User-Agent": "Mozilla/5.0 morning-brief/1.0"},
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table")
        if table is None:
            return None
        rows = table.find_all("tr")
        for tr in rows:
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if not cells:
                continue
            try:
                return float(cells[-1].replace(",", ""))
            except ValueError:
                continue
        return None
    except Exception:
        return None
