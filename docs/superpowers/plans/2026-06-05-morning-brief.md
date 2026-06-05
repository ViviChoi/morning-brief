# Morning Brief Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Morning Brief portable market-intelligence tool with two surfaces (Surface A: daily snapshot static HTML; Surface B: interactive Portfolio Explorer WebUI), per spec `docs/superpowers/specs/2026-06-05-morning-brief-design.md`.

**Architecture:** Python 3.11+. Shared `lib/` (pure data + scoring + Claude). Surface A entrypoint `morning_brief.py` renders self-contained HTML snapshots. Surface B entrypoint `webui.py` runs FastAPI on loopback for CSV upload + visualization. Git is the cross-platform sync layer. No server stays running outside Surface B's interactive session.

**Tech Stack:** Python 3.11, yfinance, requests, anthropic SDK, FastAPI + uvicorn, Jinja2, pandas, pytest + responses (HTTP mocking), Chart.js 4.4.6 (CDN + SRI), Pico.css 2.1.1 (CDN + SRI).

**Security: Subresource Integrity (SRI).** All external `<script>` / `<link>` tags MUST carry `integrity="sha384-..."` and `crossorigin="anonymous"`. CDN compromise is the most plausible supply-chain risk for a personal project; SRI mitigates it for free. Pinned hashes (computed once via `curl ... | openssl dgst -sha384 -binary | openssl base64 -A`):

- Pico CSS 2.1.1: `sha384-L1dWfspMTHU/ApYnFiMz2QID/PlP1xCW9visvBdbEkOLkSSWsP6ZJWhPw6apiXxU`
- Chart.js 4.4.6: `sha384-Sse/HDqcypGpyTDpvZOJNnG0TT3feGQUkF9H+mnRvic+LjR+K1NhTt8f51KIQ3v3`

If a dependency version is later bumped, the implementer MUST recompute the SRI hash and update **every** template in lockstep. Never serve a CDN script without SRI.

**Test strategy:** Pure functions tested directly. HTTP-touching code tested with `responses` library against captured fixtures in `tests/fixtures/`. Claude calls mocked via `unittest.mock.patch` with canned responses. No live API calls in CI / default `pytest` run.

**Commit cadence:** One commit per task minimum. Each commit message follows `<phase>:<scope>: <verb> <thing>`.

---

## Phase 0 — Skeleton, dependencies, fixtures

### Task 0.1: Create requirements.txt

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Create requirements.txt**

```
yfinance==0.2.66
requests==2.32.4
anthropic==0.50.0
fastapi==0.118.0
uvicorn[standard]==0.34.0
jinja2==3.1.5
pandas==2.3.1
python-multipart==0.0.20
python-dotenv==1.1.0
beautifulsoup4==4.13.5
pytest==8.4.2
responses==0.26.0
```

- [ ] **Step 2: Create and activate venv**

Run:
```bash
cd ~/Desktop/morning-brief
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 3: Verify imports**

Run:
```bash
python -c "import yfinance, requests, anthropic, fastapi, jinja2, pandas, responses; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "phase0:deps: pin runtime + test dependencies"
```

---

### Task 0.2: Create .env.example and config/watchlist.json

**Files:**
- Create: `.env.example`
- Create: `config/watchlist.json`

- [ ] **Step 1: Write .env.example**

```
ANTHROPIC_API_KEY=sk-ant-replace-me
CLAUDE_MODEL_BRIEF=claude-sonnet-4-6
CLAUDE_MODEL_PORTFOLIO=claude-haiku-4-5-20251001
TZ=Europe/Rome
```

- [ ] **Step 2: Write config/watchlist.json**

```bash
mkdir -p config
```

```json
{
  "equities": [
    {"symbol": "NVDA", "name": "NVIDIA"},
    {"symbol": "TSLA", "name": "Tesla"},
    {"symbol": "GOOG", "name": "Alphabet"},
    {"symbol": "RKLB", "name": "Rocket Lab"},
    {"symbol": "COIN", "name": "Coinbase"},
    {"symbol": "SMH", "name": "Semis ETF"}
  ],
  "crypto": [
    {"symbol": "BTC", "coingecko_id": "bitcoin"},
    {"symbol": "ETH", "coingecko_id": "ethereum"},
    {"symbol": "SOL", "coingecko_id": "solana"},
    {"symbol": "BNB", "coingecko_id": "binancecoin"},
    {"symbol": "HYPE", "coingecko_id": "hyperliquid"},
    {"symbol": "TAO", "coingecko_id": "bittensor"}
  ],
  "overview": [
    {"symbol": "SPY", "label": "S&P 500"},
    {"symbol": "QQQ", "label": "Nasdaq 100"},
    {"symbol": "VOO", "label": "Vanguard S&P 500"},
    {"symbol": "^VIX", "label": "VIX (fear gauge)"},
    {"symbol": "DX-Y.NYB", "label": "Dollar Index"},
    {"symbol": "GLD", "label": "Gold"},
    {"symbol": "USO", "label": "Crude Oil"},
    {"symbol": "BTC-USD", "label": "Bitcoin"},
    {"symbol": "ETH-USD", "label": "Ethereum"}
  ]
}
```

- [ ] **Step 3: Update .gitignore**

Append to `.gitignore`:
```
portfolios/
snapshots/*.json
!snapshots/.gitkeep
demos/*.html
!demos/.gitkeep
.venv/
*.pyc
__pycache__/
.pytest_cache/
```

Then create the gitkeep files:
```bash
mkdir -p snapshots demos portfolios
touch snapshots/.gitkeep demos/.gitkeep
```

Note: snapshots / demos start as gitignored during dev; flip this near release once formats are stable.

- [ ] **Step 4: Commit**

```bash
git add .env.example config/watchlist.json .gitignore snapshots/.gitkeep demos/.gitkeep
git commit -m "phase0:config: watchlist + env example + folder layout"
```

---

### Task 0.3: Capture HTTP fixtures

**Files:**
- Create: `tests/fixtures/alternative_me_fng.json`
- Create: `tests/fixtures/coingecko_simple_price.json`
- Create: `tests/fixtures/binance_funding.json`
- Create: `tests/fixtures/binance_lsr.json`
- Create: `tests/fixtures/farside_btc_etf.html`

- [ ] **Step 1: Create fixtures folder**

```bash
mkdir -p tests/fixtures
touch tests/__init__.py
```

- [ ] **Step 2: Write `tests/fixtures/alternative_me_fng.json`**

```json
{
  "name": "Fear and Greed Index",
  "data": [
    {
      "value": "42",
      "value_classification": "Fear",
      "timestamp": "1717545600",
      "time_until_update": "47000"
    }
  ],
  "metadata": {"error": null}
}
```

- [ ] **Step 3: Write `tests/fixtures/coingecko_simple_price.json`**

```json
{
  "bitcoin": {"usd": 68500.12, "usd_24h_change": -1.8},
  "ethereum": {"usd": 3625.44, "usd_24h_change": -0.6},
  "solana": {"usd": 152.10, "usd_24h_change": 2.1},
  "binancecoin": {"usd": 580.34, "usd_24h_change": 0.4},
  "hyperliquid": {"usd": 28.15, "usd_24h_change": 5.7},
  "bittensor": {"usd": 280.50, "usd_24h_change": -3.2}
}
```

- [ ] **Step 4: Write `tests/fixtures/binance_funding.json`**

```json
[
  {"symbol": "BTCUSDT", "markPrice": "68500.12", "lastFundingRate": "0.00008500", "nextFundingTime": 1717545600000}
]
```

- [ ] **Step 5: Write `tests/fixtures/binance_lsr.json`**

```json
[
  {"symbol": "BTCUSDT", "longShortRatio": "1.85", "longAccount": "0.6491", "shortAccount": "0.3509", "timestamp": "1717545600000"}
]
```

- [ ] **Step 6: Write `tests/fixtures/farside_btc_etf.html`**

```html
<!DOCTYPE html>
<html><body>
<table class="etf">
  <tr><th>Date</th><th>IBIT</th><th>FBTC</th><th>BITB</th><th>ARKB</th><th>BTCO</th><th>EZBC</th><th>BRRR</th><th>HODL</th><th>BTCW</th><th>GBTC</th><th>BTC</th><th>Total</th></tr>
  <tr><td>05 Jun 2026</td><td>120.5</td><td>80.3</td><td>22.1</td><td>15.0</td><td>3.0</td><td>1.5</td><td>2.0</td><td>4.0</td><td>0.0</td><td>-45.2</td><td>10.0</td><td>213.2</td></tr>
  <tr><td>04 Jun 2026</td><td>-30.0</td><td>-10.0</td><td>0.0</td><td>0.0</td><td>0.0</td><td>0.0</td><td>0.0</td><td>0.0</td><td>0.0</td><td>-50.0</td><td>0.0</td><td>-90.0</td></tr>
</table>
</body></html>
```

- [ ] **Step 7: Commit**

```bash
git add tests/
git commit -m "phase0:tests: HTTP fixtures for fetch tests"
```

---

## Phase 1 — Surface A: data + score + commentary + render

### Task 1.1: `lib/fetch.py` — alternative.me Crypto F&G

**Files:**
- Create: `lib/__init__.py`
- Create: `lib/fetch.py`
- Create: `tests/test_fetch_fng.py`

- [ ] **Step 1: Write failing test `tests/test_fetch_fng.py`**

```python
import json
from pathlib import Path
import responses
from lib.fetch import fetch_crypto_fng


FIXTURE = json.loads(Path("tests/fixtures/alternative_me_fng.json").read_text())


@responses.activate
def test_fetch_crypto_fng_returns_value_and_classification():
    responses.add(
        responses.GET,
        "https://api.alternative.me/fng/",
        json=FIXTURE,
        status=200,
    )
    result = fetch_crypto_fng()
    assert result["value"] == 42
    assert result["classification"] == "Fear"


@responses.activate
def test_fetch_crypto_fng_returns_none_on_error():
    responses.add(
        responses.GET,
        "https://api.alternative.me/fng/",
        status=500,
    )
    result = fetch_crypto_fng()
    assert result is None
```

- [ ] **Step 2: Run test, verify it fails**

```bash
pytest tests/test_fetch_fng.py -v
```

Expected: ImportError (`lib.fetch` does not exist yet).

- [ ] **Step 3: Implement `lib/fetch.py` (initial)**

```python
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
```

Also create empty `lib/__init__.py`.

- [ ] **Step 4: Run test, verify pass**

```bash
pytest tests/test_fetch_fng.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add lib/__init__.py lib/fetch.py tests/test_fetch_fng.py
git commit -m "phase1:fetch: crypto fear & greed (alternative.me)"
```

---

### Task 1.2: `lib/fetch.py` — CoinGecko simple prices

**Files:**
- Modify: `lib/fetch.py`
- Create: `tests/test_fetch_coingecko.py`

- [ ] **Step 1: Write failing test**

```python
import json
from pathlib import Path
import responses
from lib.fetch import fetch_crypto_prices

FIXTURE = json.loads(Path("tests/fixtures/coingecko_simple_price.json").read_text())


@responses.activate
def test_fetch_crypto_prices_returns_normalized_dict():
    responses.add(
        responses.GET,
        "https://api.coingecko.com/api/v3/simple/price",
        json=FIXTURE,
        status=200,
    )
    result = fetch_crypto_prices(["bitcoin", "ethereum"])
    assert result["bitcoin"]["price_usd"] == 68500.12
    assert result["bitcoin"]["change_24h_pct"] == -1.8
    assert result["ethereum"]["price_usd"] == 3625.44


@responses.activate
def test_fetch_crypto_prices_returns_empty_on_error():
    responses.add(
        responses.GET,
        "https://api.coingecko.com/api/v3/simple/price",
        status=429,
    )
    assert fetch_crypto_prices(["bitcoin"]) == {}
```

- [ ] **Step 2: Run test, verify it fails**

```bash
pytest tests/test_fetch_coingecko.py -v
```

Expected: ImportError on `fetch_crypto_prices`.

- [ ] **Step 3: Add to `lib/fetch.py`**

```python
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
```

- [ ] **Step 4: Run test, verify pass**

```bash
pytest tests/test_fetch_coingecko.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add lib/fetch.py tests/test_fetch_coingecko.py
git commit -m "phase1:fetch: crypto spot prices (coingecko)"
```

---

### Task 1.3: `lib/fetch.py` — yfinance equity quotes

**Files:**
- Modify: `lib/fetch.py`
- Create: `tests/test_fetch_equity.py`

- [ ] **Step 1: Write failing test (uses unittest.mock since yfinance has its own session)**

```python
from unittest.mock import patch, MagicMock
import pandas as pd
from lib.fetch import fetch_equity_quotes


def _fake_history():
    return pd.DataFrame(
        {"Close": [100.0, 105.0]},
        index=pd.to_datetime(["2026-06-04", "2026-06-05"]),
    )


def test_fetch_equity_quotes_returns_price_and_change():
    fake_ticker = MagicMock()
    fake_ticker.history.return_value = _fake_history()
    with patch("lib.fetch.yf.Ticker", return_value=fake_ticker):
        result = fetch_equity_quotes(["NVDA"])
    assert result["NVDA"]["price"] == 105.0
    assert round(result["NVDA"]["change_pct"], 2) == 5.0


def test_fetch_equity_quotes_skips_broken_ticker():
    fake_ticker = MagicMock()
    fake_ticker.history.side_effect = RuntimeError("boom")
    with patch("lib.fetch.yf.Ticker", return_value=fake_ticker):
        result = fetch_equity_quotes(["BROKEN"])
    assert result == {}
```

- [ ] **Step 2: Run, verify fail**

```bash
pytest tests/test_fetch_equity.py -v
```

Expected: ImportError on `fetch_equity_quotes`.

- [ ] **Step 3: Add to `lib/fetch.py`**

```python
import yfinance as yf


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
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_fetch_equity.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add lib/fetch.py tests/test_fetch_equity.py
git commit -m "phase1:fetch: equity quotes (yfinance)"
```

---

### Task 1.4: `lib/fetch.py` — Binance funding + L/S

**Files:**
- Modify: `lib/fetch.py`
- Create: `tests/test_fetch_binance.py`

- [ ] **Step 1: Write failing tests**

```python
import json
from pathlib import Path
import responses
from lib.fetch import fetch_btc_funding_rate, fetch_btc_long_short_ratio

FUNDING = json.loads(Path("tests/fixtures/binance_funding.json").read_text())
LSR = json.loads(Path("tests/fixtures/binance_lsr.json").read_text())


@responses.activate
def test_fetch_btc_funding_rate():
    responses.add(
        responses.GET,
        "https://fapi.binance.com/fapi/v1/premiumIndex",
        json=FUNDING,
        status=200,
    )
    rate = fetch_btc_funding_rate()
    assert rate is not None
    assert abs(rate - 0.000085) < 1e-9


@responses.activate
def test_fetch_btc_long_short_ratio():
    responses.add(
        responses.GET,
        "https://fapi.binance.com/futures/data/globalLongShortAccountRatio",
        json=LSR,
        status=200,
    )
    ratio = fetch_btc_long_short_ratio()
    assert ratio is not None
    assert abs(ratio - 1.85) < 1e-9
```

- [ ] **Step 2: Run, verify fail**

```bash
pytest tests/test_fetch_binance.py -v
```

Expected: ImportError.

- [ ] **Step 3: Add to `lib/fetch.py`**

```python
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
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_fetch_binance.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add lib/fetch.py tests/test_fetch_binance.py
git commit -m "phase1:fetch: BTC funding rate + long/short (binance public)"
```

---

### Task 1.5: `lib/fetch.py` — farside BTC ETF net flow (HTML scrape)

**Files:**
- Modify: `lib/fetch.py`
- Create: `tests/test_fetch_farside.py`

- [ ] **Step 1: Write failing test**

```python
from pathlib import Path
import responses
from lib.fetch import fetch_btc_etf_net_flow_musd

HTML = Path("tests/fixtures/farside_btc_etf.html").read_text()


@responses.activate
def test_fetch_btc_etf_net_flow_latest_row():
    responses.add(
        responses.GET,
        "https://farside.co.uk/bitcoin-etf-flow-all-data/",
        body=HTML,
        status=200,
        content_type="text/html",
    )
    flow = fetch_btc_etf_net_flow_musd()
    assert flow is not None
    assert abs(flow - 213.2) < 1e-6
```

- [ ] **Step 2: Run, verify fail**

```bash
pytest tests/test_fetch_farside.py -v
```

Expected: ImportError.

- [ ] **Step 3: Add to `lib/fetch.py`**

```python
from bs4 import BeautifulSoup


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
        # Skip header rows; find first row whose first cell is a date string.
        for tr in rows:
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if not cells:
                continue
            # last column is "Total"
            try:
                return float(cells[-1].replace(",", ""))
            except ValueError:
                continue
        return None
    except Exception:
        return None
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_fetch_farside.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add lib/fetch.py tests/test_fetch_farside.py
git commit -m "phase1:fetch: BTC ETF daily net flow (farside scrape)"
```

---

### Task 1.6: `lib/fetch.py` — orchestrator `run()`

**Files:**
- Modify: `lib/fetch.py`
- Create: `tests/test_fetch_run.py`

- [ ] **Step 1: Write failing test**

```python
from unittest.mock import patch
from lib.fetch import run


def _fakes():
    return {
        "fetch_equity_quotes": {"SPY": {"price": 540.0, "prev_close": 535.0, "change_pct": 0.93}},
        "fetch_crypto_prices": {"bitcoin": {"price_usd": 68500.0, "change_24h_pct": -1.0}},
        "fetch_crypto_fng": {"value": 42, "classification": "Fear"},
        "fetch_btc_funding_rate": 0.00008,
        "fetch_btc_long_short_ratio": 1.85,
        "fetch_btc_etf_net_flow_musd": 213.2,
    }


def test_run_aggregates_all_sources_and_reports_no_errors():
    f = _fakes()
    with patch("lib.fetch.fetch_equity_quotes", return_value=f["fetch_equity_quotes"]), \
         patch("lib.fetch.fetch_crypto_prices", return_value=f["fetch_crypto_prices"]), \
         patch("lib.fetch.fetch_crypto_fng", return_value=f["fetch_crypto_fng"]), \
         patch("lib.fetch.fetch_btc_funding_rate", return_value=f["fetch_btc_funding_rate"]), \
         patch("lib.fetch.fetch_btc_long_short_ratio", return_value=f["fetch_btc_long_short_ratio"]), \
         patch("lib.fetch.fetch_btc_etf_net_flow_musd", return_value=f["fetch_btc_etf_net_flow_musd"]):
        snap = run(
            equity_symbols=["SPY"],
            crypto_ids=["bitcoin"],
        )
    assert snap["equity"]["SPY"]["price"] == 540.0
    assert snap["crypto"]["bitcoin"]["price_usd"] == 68500.0
    assert snap["crypto_fng"]["value"] == 42
    assert snap["btc_signals"]["funding_rate"] == 0.00008
    assert snap["btc_signals"]["long_short_ratio"] == 1.85
    assert snap["btc_signals"]["etf_net_flow_musd"] == 213.2
    assert snap["_errors"] == []


def test_run_records_errors_on_missing_data():
    with patch("lib.fetch.fetch_equity_quotes", return_value={}), \
         patch("lib.fetch.fetch_crypto_prices", return_value={}), \
         patch("lib.fetch.fetch_crypto_fng", return_value=None), \
         patch("lib.fetch.fetch_btc_funding_rate", return_value=None), \
         patch("lib.fetch.fetch_btc_long_short_ratio", return_value=None), \
         patch("lib.fetch.fetch_btc_etf_net_flow_musd", return_value=None):
        snap = run(equity_symbols=["SPY"], crypto_ids=["bitcoin"])
    assert "crypto_fng" in snap["_errors"]
    assert "btc_signals.funding_rate" in snap["_errors"]
```

- [ ] **Step 2: Run, verify fail**

```bash
pytest tests/test_fetch_run.py -v
```

Expected: ImportError on `run`.

- [ ] **Step 3: Add to `lib/fetch.py`**

```python
def run(equity_symbols: list[str], crypto_ids: list[str]) -> dict:
    errors: list[str] = []
    equity = fetch_equity_quotes(equity_symbols)
    if not equity:
        errors.append("equity")
    crypto = fetch_crypto_prices(crypto_ids)
    if not crypto:
        errors.append("crypto")
    fng = fetch_crypto_fng()
    if fng is None:
        errors.append("crypto_fng")
    funding = fetch_btc_funding_rate()
    if funding is None:
        errors.append("btc_signals.funding_rate")
    lsr = fetch_btc_long_short_ratio()
    if lsr is None:
        errors.append("btc_signals.long_short_ratio")
    etf = fetch_btc_etf_net_flow_musd()
    if etf is None:
        errors.append("btc_signals.etf_net_flow_musd")
    return {
        "equity": equity,
        "crypto": crypto,
        "crypto_fng": fng,
        "btc_signals": {
            "funding_rate": funding,
            "long_short_ratio": lsr,
            "etf_net_flow_musd": etf,
        },
        "_errors": errors,
    }
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_fetch_run.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add lib/fetch.py tests/test_fetch_run.py
git commit -m "phase1:fetch: orchestrator run() with per-source error reporting"
```

---

### Task 1.7: `lib/score.py` — BTC bottom score 0-100

**Files:**
- Create: `lib/score.py`
- Create: `tests/test_score.py`

- [ ] **Step 1: Write failing test**

```python
from lib.score import btc_bottom_score


def test_score_all_inputs_present_returns_components_and_total():
    inputs = {
        "etf_net_flow_musd": 213.2,
        "funding_rate": 0.00008,
        "fng_value": 42,
        "long_short_ratio": 1.85,
    }
    result = btc_bottom_score(**inputs)
    assert "components" in result
    assert "total" in result
    assert 0 <= result["total"] <= 100
    assert result["rating"] in {
        "Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed",
    }
    assert result["partial"] is False


def test_score_missing_input_returns_partial_true():
    result = btc_bottom_score(
        etf_net_flow_musd=None,
        funding_rate=0.00008,
        fng_value=42,
        long_short_ratio=1.85,
    )
    assert result["partial"] is True
    assert result["components"]["etf_net_flow"] is None


def test_score_extreme_fear_under_15():
    # All bearish: huge outflows, negative funding, F&G 5, low L/S
    r = btc_bottom_score(
        etf_net_flow_musd=-500.0,
        funding_rate=-0.0005,
        fng_value=5,
        long_short_ratio=0.5,
    )
    assert r["total"] <= 15
    assert r["rating"] == "Extreme Fear"
```

- [ ] **Step 2: Run, verify fail**

```bash
pytest tests/test_score.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `lib/score.py`**

```python
"""BTC bottom score: 0-100 (0 = extreme fear, 100 = extreme greed).

Weighted from 4 daily indicators (full Day1Global model uses 13, the other 9
are paid on-chain metrics deferred to P2).
"""
from __future__ import annotations

WEIGHTS = {
    "etf_net_flow": 0.38,
    "funding_rate": 0.25,
    "fng": 0.22,
    "long_short": 0.15,
}


def _score_etf_flow(musd: float | None) -> float | None:
    """Map daily net flow (USD millions) to 0-100.
    Heuristic: -500 → 0 (extreme fear), 0 → 50, +500 → 100 (extreme greed).
    """
    if musd is None:
        return None
    score = 50.0 + (musd / 500.0) * 50.0
    return max(0.0, min(100.0, score))


def _score_funding(rate: float | None) -> float | None:
    """Map funding rate to 0-100. -0.0005 → 0, 0 → 50, +0.0005 → 100."""
    if rate is None:
        return None
    score = 50.0 + (rate / 0.0005) * 50.0
    return max(0.0, min(100.0, score))


def _score_fng(value: int | None) -> float | None:
    """F&G index is already 0-100."""
    if value is None:
        return None
    return float(max(0, min(100, value)))


def _score_long_short(ratio: float | None) -> float | None:
    """L/S ratio: 0.5 → 0, 1.0 → 50, 2.0 → 100. Logarithmic feel."""
    if ratio is None:
        return None
    import math
    score = 50.0 + math.log2(ratio) * 50.0
    return max(0.0, min(100.0, score))


def _rating(score: float) -> str:
    if score <= 15: return "Extreme Fear"
    if score <= 45: return "Fear"
    if score <= 55: return "Neutral"
    if score <= 85: return "Greed"
    return "Extreme Greed"


def btc_bottom_score(
    etf_net_flow_musd: float | None,
    funding_rate: float | None,
    fng_value: int | None,
    long_short_ratio: float | None,
) -> dict:
    components = {
        "etf_net_flow": _score_etf_flow(etf_net_flow_musd),
        "funding_rate": _score_funding(funding_rate),
        "fng": _score_fng(fng_value),
        "long_short": _score_long_short(long_short_ratio),
    }
    available = {k: v for k, v in components.items() if v is not None}
    if not available:
        return {
            "components": components,
            "total": None,
            "rating": "Unknown",
            "partial": True,
        }
    weight_sum = sum(WEIGHTS[k] for k in available)
    total = sum(v * WEIGHTS[k] for k, v in available.items()) / weight_sum
    return {
        "components": components,
        "total": round(total, 1),
        "rating": _rating(total),
        "partial": len(available) < 4,
    }
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_score.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add lib/score.py tests/test_score.py
git commit -m "phase1:score: BTC bottom score 0-100 with partial-input support"
```

---

### Task 1.8: `lib/claude_brief.py` — Claude commentary wrapper

**Files:**
- Create: `lib/claude_brief.py`
- Create: `tests/test_claude_brief.py`

- [ ] **Step 1: Write failing test**

```python
from unittest.mock import patch, MagicMock
from lib.claude_brief import compose


SNAPSHOT = {
    "equity": {"SPY": {"price": 540.0, "change_pct": 0.5}},
    "crypto": {"bitcoin": {"price_usd": 68500.0, "change_24h_pct": -1.0}},
    "crypto_fng": {"value": 42, "classification": "Fear"},
    "btc_signals": {"funding_rate": 0.00008, "long_short_ratio": 1.85, "etf_net_flow_musd": 213.2},
    "btc_score": {"total": 38, "rating": "Fear"},
    "_errors": [],
}


def _fake_response(text: str):
    msg = MagicMock()
    msg.content = [MagicMock(type="text", text=text)]
    msg.stop_reason = "end_turn"
    return msg


def test_compose_returns_all_sections():
    fake_text = (
        "HEADLINE: Markets neutral, BTC in fear zone.\n\n"
        "LIQUIDITY_TONE: Slightly tight, VIX moderate.\n\n"
        "TICKERS:\n- SPY: index drifting near highs\n\n"
        "BTC_NARRATIVE: Score 38 suggests historically a measured-risk zone, not a buy yet.\n\n"
        "TOP_10:\n1. Fed meeting next week — rates likely on hold\n"
    )
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_response(fake_text)
    with patch("lib.claude_brief.Anthropic", return_value=fake_client):
        out = compose(SNAPSHOT, api_key="dummy", model="claude-sonnet-4-6")
    assert "Markets neutral" in out["headline"]
    assert "Slightly tight" in out["liquidity_tone"]
    assert "drifting near highs" in out["tickers_text"]
    assert "Score 38" in out["btc_narrative"]
    assert "Fed meeting" in out["top_10"]


def test_compose_returns_placeholders_on_api_failure():
    fake_client = MagicMock()
    fake_client.messages.create.side_effect = RuntimeError("rate limited")
    with patch("lib.claude_brief.Anthropic", return_value=fake_client):
        out = compose(SNAPSHOT, api_key="dummy", model="claude-sonnet-4-6")
    assert out["headline"] == "AI commentary unavailable today."
    assert out["error"] is not None
```

- [ ] **Step 2: Run, verify fail**

```bash
pytest tests/test_claude_brief.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `lib/claude_brief.py`**

```python
"""Claude wrapper for the daily Surface A commentary.

Inputs: a snapshot dict (from fetch.run + score). Output: a `commentary` dict
of strings ready for templating.

The prompt asks Claude to produce a fixed set of sections, separated by
labeled markers, so parsing is robust and version-independent.
"""
from __future__ import annotations

import re
from anthropic import Anthropic


_SYSTEM = (
    "You are a calm, plain-language market briefing writer for a financial novice. "
    "Avoid jargon. When unavoidable, define it parenthetically the first time. "
    "Output ONLY the labeled sections requested. Do not add introductions or sign-offs."
)


def _user_prompt(snapshot: dict) -> str:
    return f"""Produce a daily market brief using the data below. Return EXACTLY these labeled sections:

HEADLINE: <one sentence, the day in plain language, no jargon>

LIQUIDITY_TONE: <one sentence describing today's liquidity / risk appetite>

TICKERS:
- <symbol>: <one short sentence thesis>
(one bullet per ticker in the equity and crypto blocks below)

BTC_NARRATIVE: <2-3 sentences interpreting the BTC bottom score and what it means for a long-term holder>

TOP_10:
1. <topic — one short sentence of context — actionable hint>
...
10. ...

DATA:
{snapshot}
"""


def _parse_sections(text: str) -> dict:
    def grab(label: str, until: str | None) -> str:
        if until:
            m = re.search(rf"{label}:\s*(.+?)(?={until}:)", text, re.DOTALL)
        else:
            m = re.search(rf"{label}:\s*(.+)$", text, re.DOTALL)
        return m.group(1).strip() if m else ""

    return {
        "headline": grab("HEADLINE", "LIQUIDITY_TONE"),
        "liquidity_tone": grab("LIQUIDITY_TONE", "TICKERS"),
        "tickers_text": grab("TICKERS", "BTC_NARRATIVE"),
        "btc_narrative": grab("BTC_NARRATIVE", "TOP_10"),
        "top_10": grab("TOP_10", None),
        "error": None,
    }


def compose(snapshot: dict, api_key: str, model: str) -> dict:
    try:
        client = Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=2000,
            system=_SYSTEM,
            messages=[{"role": "user", "content": _user_prompt(snapshot)}],
        )
        text = "".join(block.text for block in msg.content if getattr(block, "type", "") == "text")
        return _parse_sections(text)
    except Exception as exc:
        return {
            "headline": "AI commentary unavailable today.",
            "liquidity_tone": "",
            "tickers_text": "",
            "btc_narrative": "",
            "top_10": "",
            "error": str(exc),
        }
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_claude_brief.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add lib/claude_brief.py tests/test_claude_brief.py
git commit -m "phase1:brief: Claude wrapper composing labeled sections"
```

---

### Task 1.9: `lib/render.py` — viewer.html + self-contained demo HTML

**Files:**
- Create: `lib/render.py`
- Create: `templates/dashboard.html`
- Create: `tests/test_render.py`

- [ ] **Step 1: Write failing test**

```python
import json
from pathlib import Path
from lib.render import render_self_contained, render_live_viewer


SNAPSHOT = {
    "date": "2026-06-05",
    "equity": {"SPY": {"price": 540.0, "prev_close": 535.0, "change_pct": 0.93}},
    "crypto": {"bitcoin": {"price_usd": 68500.0, "change_24h_pct": -1.0}},
    "crypto_fng": {"value": 42, "classification": "Fear"},
    "btc_signals": {"funding_rate": 0.00008, "long_short_ratio": 1.85, "etf_net_flow_musd": 213.2},
    "btc_score": {"total": 38, "rating": "Fear", "components": {}, "partial": False},
    "commentary": {
        "headline": "Calm tape, BTC in fear zone.",
        "liquidity_tone": "Tight but not dangerous.",
        "tickers_text": "- SPY: drifting near highs",
        "btc_narrative": "Score 38 = measured-risk zone.",
        "top_10": "1. Fed meeting next week — rates on hold",
        "error": None,
    },
    "_errors": [],
}


def test_render_self_contained_inlines_data():
    html = render_self_contained(SNAPSHOT)
    assert "Calm tape" in html
    assert "SPY" in html
    assert "<script" in html  # has inlined JS
    assert "fetch(" not in html  # no external data fetches
    assert "2026-06-05" in html


def test_render_live_viewer_references_latest_json(tmp_path: Path):
    out = tmp_path / "viewer.html"
    render_live_viewer(out)
    html = out.read_text()
    assert "snapshots/latest.json" in html
    assert "<script" in html
```

- [ ] **Step 2: Run, verify fail**

```bash
pytest tests/test_render.py -v
```

Expected: ImportError.

- [ ] **Step 3: Create `templates/dashboard.html`** — minimal first cut; UX polish in Phase 3.

```bash
mkdir -p templates
```

```html
{# templates/dashboard.html - minimal first cut, UX polished in Phase 3 #}
<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<title>Morning Brief {{ date }}</title>
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/@picocss/pico@2.1.1/css/pico.min.css"
      integrity="sha384-L1dWfspMTHU/ApYnFiMz2QID/PlP1xCW9visvBdbEkOLkSSWsP6ZJWhPw6apiXxU"
      crossorigin="anonymous">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.6/dist/chart.umd.min.js"
        integrity="sha384-Sse/HDqcypGpyTDpvZOJNnG0TT3feGQUkF9H+mnRvic+LjR+K1NhTt8f51KIQ3v3"
        crossorigin="anonymous"></script>
<style>
  body { max-width: 1100px; margin: 1rem auto; padding: 0 1rem; }
  .headline { font-size: 1.8rem; line-height: 1.3; margin: 1rem 0; }
  .grid-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: .5rem; }
  .card { padding: .6rem; border: 1px solid var(--pico-muted-border-color); border-radius: 8px; }
  .up { color: #1a7f37; } .down { color: #cf222e; }
  .score-bar { height: 28px; background: linear-gradient(90deg, #cf222e 0%, #d4a72c 30%, #1a7f37 50%, #d4a72c 70%, #cf222e 100%); position: relative; border-radius: 14px; }
  .score-pointer { position: absolute; top: -6px; width: 4px; height: 40px; background: #1f2328; }
</style>
</head><body>
<header>
  <h1>Morning Brief — {{ date }}</h1>
  <p class="headline">{{ commentary.headline or "(no commentary)" }}</p>
  <p><em>{{ commentary.liquidity_tone }}</em></p>
</header>

<section>
  <h2>Overview</h2>
  <div class="grid-cards">
  {% for sym, data in equity.items() %}
    <div class="card"><strong>{{ sym }}</strong><br>
      ${{ "%.2f"|format(data.price) }}
      <span class="{{ 'up' if data.change_pct >= 0 else 'down' }}">
        {{ "%+.2f"|format(data.change_pct) }}%
      </span></div>
  {% endfor %}
  {% for cg_id, data in crypto.items() %}
    <div class="card"><strong>{{ cg_id }}</strong><br>
      ${{ "%.2f"|format(data.price_usd) }}
      <span class="{{ 'up' if data.change_24h_pct >= 0 else 'down' }}">
        {{ "%+.2f"|format(data.change_24h_pct) }}%
      </span></div>
  {% endfor %}
  </div>
</section>

<section>
  <h2>BTC Bottom Score: {{ btc_score.total or "—" }} <small>({{ btc_score.rating }})</small></h2>
  <div class="score-bar"><div class="score-pointer" style="left: {{ btc_score.total or 50 }}%"></div></div>
  <p>{{ commentary.btc_narrative }}</p>
</section>

<section>
  <h2>Holdings — what you watch today</h2>
  <pre style="white-space: pre-wrap">{{ commentary.tickers_text }}</pre>
</section>

<section>
  <h2>Top 10 things today</h2>
  <pre style="white-space: pre-wrap">{{ commentary.top_10 }}</pre>
</section>

<footer><small>Data: yfinance · CoinGecko · alternative.me · farside.co.uk · Binance. AI: Claude.</small></footer>
</body></html>
```

- [ ] **Step 4: Implement `lib/render.py`**

```python
"""HTML rendering for both surfaces.

- `render_self_contained(snapshot) -> str` returns a single HTML string with the
  snapshot data inlined as JSON. No runtime fetches.
- `render_live_viewer(path)` writes a viewer file that fetches
  `snapshots/latest.json` at open time.
"""
from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


_TEMPLATES = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(_TEMPLATES),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_self_contained(snapshot: dict) -> str:
    return _env.get_template("dashboard.html").render(**snapshot)


_VIEWER = """<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><title>Morning Brief (live)</title>
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/@picocss/pico@2.1.1/css/pico.min.css"
      integrity="sha384-L1dWfspMTHU/ApYnFiMz2QID/PlP1xCW9visvBdbEkOLkSSWsP6ZJWhPw6apiXxU"
      crossorigin="anonymous">
</head><body>
<main class="container">
  <h1>Loading latest snapshot...</h1>
  <div id="content"></div>
</main>
<script>
fetch('snapshots/latest.json').then(r => r.json()).then(s => {
  document.title = 'Morning Brief — ' + s.date;
  document.querySelector('h1').textContent = s.commentary?.headline || s.date;
  const c = document.getElementById('content');
  c.innerHTML = '<p>' + (s.commentary?.liquidity_tone || '') + '</p>'
    + '<h2>BTC Score: ' + (s.btc_score?.total ?? '-') + ' (' + (s.btc_score?.rating ?? '-') + ')</h2>'
    + '<pre>' + JSON.stringify(s.equity, null, 2) + '</pre>';
}).catch(e => {
  document.querySelector('h1').textContent = 'No snapshot found. Run morning_brief.py first.';
});
</script>
</body></html>
"""


def render_live_viewer(path: Path) -> None:
    Path(path).write_text(_VIEWER)
```

- [ ] **Step 5: Run, verify pass**

```bash
pytest tests/test_render.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add lib/render.py templates/dashboard.html tests/test_render.py
git commit -m "phase1:render: minimal dashboard template + viewer (UX polish later)"
```

---

### Task 1.10: `morning_brief.py` — Surface A orchestrator

**Files:**
- Create: `morning_brief.py`
- Create: `tests/test_morning_brief.py`

- [ ] **Step 1: Write failing test**

```python
import json
import os
from pathlib import Path
from unittest.mock import patch
import sys


def test_orchestrator_writes_snapshot_and_demo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "snapshots").mkdir()
    (tmp_path / "demos").mkdir()
    (tmp_path / "config" / "watchlist.json").write_text(json.dumps({
        "equities": [{"symbol": "SPY", "name": "S&P"}],
        "crypto": [{"symbol": "BTC", "coingecko_id": "bitcoin"}],
        "overview": [{"symbol": "SPY", "label": "S&P"}],
    }))
    # Copy templates so jinja loader finds them
    repo_root = Path(__file__).resolve().parent.parent
    src_tpl = repo_root / "templates"
    if src_tpl.exists():
        import shutil
        shutil.copytree(src_tpl, tmp_path / "templates")
    # Force lib import path
    sys.path.insert(0, str(repo_root))
    from lib.fetch import run as fetch_run  # noqa
    fake_snapshot = {
        "equity": {"SPY": {"price": 540.0, "prev_close": 535.0, "change_pct": 0.93}},
        "crypto": {"bitcoin": {"price_usd": 68500.0, "change_24h_pct": -1.0}},
        "crypto_fng": {"value": 42, "classification": "Fear"},
        "btc_signals": {"funding_rate": 0.00008, "long_short_ratio": 1.85, "etf_net_flow_musd": 213.2},
        "_errors": [],
    }
    fake_commentary = {
        "headline": "ok", "liquidity_tone": "ok", "tickers_text": "ok",
        "btc_narrative": "ok", "top_10": "ok", "error": None,
    }
    with patch("lib.fetch.run", return_value=fake_snapshot), \
         patch("lib.claude_brief.compose", return_value=fake_commentary):
        import morning_brief
        rc = morning_brief.main(["--no-open"])
    assert rc == 0
    snapshots = list((tmp_path / "snapshots").glob("*.json"))
    demos = list((tmp_path / "demos").glob("*.html"))
    assert len(snapshots) >= 1
    assert len(demos) >= 1
    snap = json.loads((tmp_path / "snapshots" / "latest.json").read_text())
    assert snap["btc_score"]["total"] is not None
```

- [ ] **Step 2: Run, verify fail**

```bash
pytest tests/test_morning_brief.py -v
```

Expected: ImportError on `morning_brief`.

- [ ] **Step 3: Implement `morning_brief.py`**

```python
"""Surface A entrypoint. One invocation = one snapshot.

CLI:
    python morning_brief.py [--no-open] [--commit] [--push]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

from dotenv import load_dotenv

from lib import fetch as fetch_mod
from lib import score as score_mod
from lib import claude_brief
from lib import render as render_mod


def _load_watchlist(root: Path) -> dict:
    return json.loads((root / "config" / "watchlist.json").read_text())


def _today_iso() -> str:
    return dt.date.today().isoformat()


def _write_snapshot(root: Path, snapshot: dict) -> Path:
    snaps = root / "snapshots"
    snaps.mkdir(exist_ok=True)
    today = root / "snapshots" / f"{snapshot['date']}.json"
    today.write_text(json.dumps(snapshot, indent=2, default=str))
    (snaps / "latest.json").write_text(today.read_text())  # copy, NOT symlink
    return today


def _write_demo(root: Path, snapshot: dict) -> Path:
    demos = root / "demos"
    demos.mkdir(exist_ok=True)
    html = render_mod.render_self_contained(snapshot)
    out = demos / f"{snapshot['date']}.html"
    out.write_text(html)
    (demos / "latest.html").write_text(html)
    return out


def _git(root: Path, *args: str) -> int:
    return subprocess.call(["git", "-C", str(root), *args])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--push", action="store_true")
    args = parser.parse_args(argv)

    root = Path.cwd()
    load_dotenv(root / ".env")
    watchlist = _load_watchlist(root)

    equity_syms = [w["symbol"] for w in watchlist["overview"]] + [e["symbol"] for e in watchlist["equities"]]
    crypto_ids = [c["coingecko_id"] for c in watchlist["crypto"]]

    data = fetch_mod.run(equity_symbols=list(dict.fromkeys(equity_syms)), crypto_ids=crypto_ids)
    score = score_mod.btc_bottom_score(
        etf_net_flow_musd=data["btc_signals"]["etf_net_flow_musd"],
        funding_rate=data["btc_signals"]["funding_rate"],
        fng_value=(data["crypto_fng"] or {}).get("value"),
        long_short_ratio=data["btc_signals"]["long_short_ratio"],
    )
    data["btc_score"] = score
    data["date"] = _today_iso()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    model = os.environ.get("CLAUDE_MODEL_BRIEF", "claude-sonnet-4-6")
    if api_key and api_key != "sk-ant-replace-me":
        data["commentary"] = claude_brief.compose(data, api_key=api_key, model=model)
    else:
        data["commentary"] = {
            "headline": "(set ANTHROPIC_API_KEY in .env to enable AI commentary)",
            "liquidity_tone": "", "tickers_text": "", "btc_narrative": "", "top_10": "",
            "error": "no_api_key",
        }

    snap_path = _write_snapshot(root, data)
    demo_path = _write_demo(root, data)

    if args.commit:
        _git(root, "add", "snapshots", "demos")
        _git(root, "commit", "-m", f"snapshot {data['date']}")
        if args.push:
            _git(root, "push")

    if not args.no_open:
        webbrowser.open((root / "viewer.html").as_uri())

    return 0 if not data["_errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_morning_brief.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Live smoke test (Mac, requires .env)**

```bash
cp .env.example .env
# manually edit .env to add ANTHROPIC_API_KEY
python morning_brief.py --no-open
```

Expected: writes `snapshots/2026-06-05.json` and `demos/2026-06-05.html`. Exit code 0.

- [ ] **Step 6: Commit**

```bash
git add morning_brief.py tests/test_morning_brief.py
git commit -m "phase1:cli: surface A orchestrator with --no-open / --commit / --push"
```

---

## Phase 2 — Surface B: importers + portfolio + WebUI

### Task 2.1: `lib/importers/generic.py` — column-name autodetect CSV

**Files:**
- Create: `lib/importers/__init__.py`
- Create: `lib/importers/generic.py`
- Create: `tests/fixtures/portfolio_generic.csv`
- Create: `tests/test_importer_generic.py`

- [ ] **Step 1: Write fixture `tests/fixtures/portfolio_generic.csv`**

```
Symbol,Quantity,Cost Basis
NVDA,50,400.50
TSLA,20,250.00
BTC,0.5,40000
```

- [ ] **Step 2: Write failing test**

```python
from pathlib import Path
from lib.importers.generic import parse_generic_csv


def test_parse_generic_csv_handles_common_column_names():
    raw = Path("tests/fixtures/portfolio_generic.csv").read_bytes()
    out = parse_generic_csv(raw)
    assert len(out) == 3
    nvda = next(p for p in out if p["symbol"] == "NVDA")
    assert nvda["qty"] == 50
    assert nvda["cost"] == 400.50


def test_parse_generic_csv_raises_on_missing_columns():
    raw = b"foo,bar\n1,2\n"
    try:
        parse_generic_csv(raw)
    except ValueError as e:
        assert "column" in str(e).lower()
        return
    assert False, "expected ValueError"
```

- [ ] **Step 3: Run, verify fail**

```bash
pytest tests/test_importer_generic.py -v
```

Expected: ImportError.

- [ ] **Step 4: Implement `lib/importers/generic.py`**

```bash
mkdir -p lib/importers
touch lib/importers/__init__.py
```

```python
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
```

- [ ] **Step 5: Run, verify pass**

```bash
pytest tests/test_importer_generic.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add lib/importers/__init__.py lib/importers/generic.py tests/fixtures/portfolio_generic.csv tests/test_importer_generic.py
git commit -m "phase2:importer: generic CSV with column autodetect"
```

---

### Task 2.2: `lib/importers/ibkr.py` — IBKR Activity Statement

**Files:**
- Create: `lib/importers/ibkr.py`
- Create: `tests/fixtures/portfolio_ibkr.csv`
- Create: `tests/test_importer_ibkr.py`

- [ ] **Step 1: Write fixture (IBKR "Positions" rows from Activity Statement)**

`tests/fixtures/portfolio_ibkr.csv`:
```
Statement,Header,Field Name,Field Value
Statement,Data,BrokerName,Interactive Brokers
Positions,Header,Asset Category,Symbol,Quantity,Cost Basis,Currency
Positions,Data,Stocks,NVDA,50,20025.00,USD
Positions,Data,Stocks,TSLA,20,5000.00,USD
Positions,Total,,,,25025.00,USD
```

- [ ] **Step 2: Write failing test**

```python
from pathlib import Path
from lib.importers.ibkr import parse_ibkr_csv


def test_parse_ibkr_picks_positions_rows_only():
    raw = Path("tests/fixtures/portfolio_ibkr.csv").read_bytes()
    out = parse_ibkr_csv(raw)
    syms = {p["symbol"] for p in out}
    assert syms == {"NVDA", "TSLA"}
    nvda = next(p for p in out if p["symbol"] == "NVDA")
    assert nvda["qty"] == 50
    assert abs(nvda["cost"] - 400.5) < 1e-3  # 20025 / 50
```

- [ ] **Step 3: Run, verify fail**

```bash
pytest tests/test_importer_ibkr.py -v
```

Expected: ImportError.

- [ ] **Step 4: Implement `lib/importers/ibkr.py`**

```python
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
```

- [ ] **Step 5: Run, verify pass**

```bash
pytest tests/test_importer_ibkr.py -v
```

Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add lib/importers/ibkr.py tests/fixtures/portfolio_ibkr.csv tests/test_importer_ibkr.py
git commit -m "phase2:importer: IBKR activity statement positions"
```

---

### Task 2.3: `lib/importers/binance.py` — Binance Trade History

**Files:**
- Create: `lib/importers/binance.py`
- Create: `tests/fixtures/portfolio_binance.csv`
- Create: `tests/test_importer_binance.py`

- [ ] **Step 1: Write fixture**

`tests/fixtures/portfolio_binance.csv`:
```
Date(UTC),Pair,Side,Price,Executed,Amount,Fee
2026-01-15,BTC/USDT,BUY,42000,0.1,4200,0.0001 BTC
2026-02-20,ETH/USDT,BUY,2800,2,5600,0.002 ETH
2026-03-10,BTC/USDT,SELL,68000,0.02,1360,0.001 USDT
```

- [ ] **Step 2: Write failing test**

```python
from pathlib import Path
from lib.importers.binance import parse_binance_csv


def test_parse_binance_aggregates_buys_minus_sells():
    raw = Path("tests/fixtures/portfolio_binance.csv").read_bytes()
    out = parse_binance_csv(raw)
    syms = {p["symbol"]: p for p in out}
    assert "BTC" in syms
    assert "ETH" in syms
    btc = syms["BTC"]
    # Bought 0.1 BTC @ 42000, sold 0.02 BTC. Net 0.08 BTC. Avg cost stays at 42000 for buys.
    assert abs(btc["qty"] - 0.08) < 1e-6
    assert abs(btc["cost"] - 42000) < 1e-3
```

- [ ] **Step 3: Run, verify fail**

```bash
pytest tests/test_importer_binance.py -v
```

Expected: ImportError.

- [ ] **Step 4: Implement `lib/importers/binance.py`**

```python
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
```

- [ ] **Step 5: Run, verify pass**

```bash
pytest tests/test_importer_binance.py -v
```

Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add lib/importers/binance.py tests/fixtures/portfolio_binance.csv tests/test_importer_binance.py
git commit -m "phase2:importer: binance trade history (buys − sells, weighted avg cost)"
```

---

### Task 2.4: `lib/importers/coinbase.py` — Coinbase Pro Account export

**Files:**
- Create: `lib/importers/coinbase.py`
- Create: `tests/fixtures/portfolio_coinbase.csv`
- Create: `tests/test_importer_coinbase.py`

- [ ] **Step 1: Write fixture**

`tests/fixtures/portfolio_coinbase.csv`:
```
Timestamp,Transaction Type,Asset,Quantity Transacted,Spot Price at Transaction,Subtotal,Notes
2026-01-15T10:00:00Z,Buy,BTC,0.1,42000,4200,Bought BTC
2026-02-20T11:00:00Z,Buy,ETH,2,2800,5600,Bought ETH
2026-03-10T12:00:00Z,Sell,BTC,0.02,68000,1360,Sold BTC
```

- [ ] **Step 2: Write failing test**

```python
from pathlib import Path
from lib.importers.coinbase import parse_coinbase_csv


def test_parse_coinbase_aggregates_per_asset():
    raw = Path("tests/fixtures/portfolio_coinbase.csv").read_bytes()
    out = parse_coinbase_csv(raw)
    syms = {p["symbol"]: p for p in out}
    assert syms["BTC"]["qty"] == 0.08
    assert abs(syms["BTC"]["cost"] - 42000) < 1e-3
    assert syms["ETH"]["qty"] == 2
```

- [ ] **Step 3: Run, verify fail**

```bash
pytest tests/test_importer_coinbase.py -v
```

Expected: ImportError.

- [ ] **Step 4: Implement `lib/importers/coinbase.py`**

```python
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
```

- [ ] **Step 5: Run, verify pass**

```bash
pytest tests/test_importer_coinbase.py -v
```

Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add lib/importers/coinbase.py tests/fixtures/portfolio_coinbase.csv tests/test_importer_coinbase.py
git commit -m "phase2:importer: coinbase account history (buys − sells)"
```

---

### Task 2.5: `lib/importers` — dispatch + sniff

**Files:**
- Modify: `lib/importers/__init__.py`
- Create: `tests/test_importer_dispatch.py`

- [ ] **Step 1: Write failing test**

```python
from pathlib import Path
from lib.importers import detect_and_parse


def test_detect_ibkr_by_first_line():
    raw = Path("tests/fixtures/portfolio_ibkr.csv").read_bytes()
    broker, positions = detect_and_parse(raw)
    assert broker == "ibkr"
    assert len(positions) >= 1


def test_detect_binance_by_headers():
    raw = Path("tests/fixtures/portfolio_binance.csv").read_bytes()
    broker, positions = detect_and_parse(raw)
    assert broker == "binance"


def test_detect_coinbase_by_headers():
    raw = Path("tests/fixtures/portfolio_coinbase.csv").read_bytes()
    broker, positions = detect_and_parse(raw)
    assert broker == "coinbase"


def test_detect_generic_fallback():
    raw = Path("tests/fixtures/portfolio_generic.csv").read_bytes()
    broker, positions = detect_and_parse(raw)
    assert broker == "generic"
```

- [ ] **Step 2: Run, verify fail**

```bash
pytest tests/test_importer_dispatch.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `lib/importers/__init__.py`**

```python
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
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_importer_dispatch.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add lib/importers/__init__.py tests/test_importer_dispatch.py
git commit -m "phase2:importer: auto-detect dispatch (ibkr/binance/coinbase/generic)"
```

---

### Task 2.6: `lib/portfolio.py` — positions valuation + allocation

**Files:**
- Create: `lib/portfolio.py`
- Create: `tests/test_portfolio.py`

- [ ] **Step 1: Write failing test**

```python
from lib.portfolio import value_positions, allocation_breakdown


RAW = [
    {"symbol": "NVDA", "qty": 50, "cost": 400.0},
    {"symbol": "BTC", "qty": 0.5, "cost": 40000.0},
]

PRICES = {
    "NVDA": 500.0,
    "BTC": 60000.0,
}


def test_value_positions_computes_pnl():
    out = value_positions(RAW, PRICES)
    nvda = next(p for p in out if p["symbol"] == "NVDA")
    assert nvda["current_value"] == 25000.0
    assert nvda["pnl_abs"] == 5000.0
    assert nvda["pnl_pct"] == 25.0


def test_allocation_breakdown_sums_to_one():
    valued = value_positions(RAW, PRICES)
    alloc = allocation_breakdown(valued)
    assert abs(sum(a["weight"] for a in alloc) - 1.0) < 1e-6
    # NVDA = 25000, BTC = 30000, total 55000 → NVDA ~45%, BTC ~55%
    nvda = next(a for a in alloc if a["symbol"] == "NVDA")
    assert abs(nvda["weight"] - 25000 / 55000) < 1e-6


def test_value_positions_skips_unpriced_symbols():
    out = value_positions(RAW, {"NVDA": 500.0})
    syms = {p["symbol"] for p in out}
    assert "NVDA" in syms
    assert "BTC" not in syms
```

- [ ] **Step 2: Run, verify fail**

```bash
pytest tests/test_portfolio.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `lib/portfolio.py`**

```python
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
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_portfolio.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add lib/portfolio.py tests/test_portfolio.py
git commit -m "phase2:portfolio: valuation + allocation breakdown (pure functions)"
```

---

### Task 2.7: `lib/claude_portfolio.py` — plain-language explanation

**Files:**
- Create: `lib/claude_portfolio.py`
- Create: `tests/test_claude_portfolio.py`

- [ ] **Step 1: Write failing test**

```python
from unittest.mock import patch, MagicMock
from lib.claude_portfolio import explain_portfolio


VALUED = [
    {"symbol": "NVDA", "qty": 50, "cost": 400.0, "current_price": 500.0,
     "current_value": 25000.0, "pnl_abs": 5000.0, "pnl_pct": 25.0},
    {"symbol": "BTC", "qty": 0.5, "cost": 40000.0, "current_price": 60000.0,
     "current_value": 30000.0, "pnl_abs": 10000.0, "pnl_pct": 50.0},
]


def _fake_response(text: str):
    msg = MagicMock()
    msg.content = [MagicMock(type="text", text=text)]
    return msg


def test_explain_returns_three_blocks():
    text = (
        "WHAT_YOU_HOLD: You hold a tech-heavy portfolio dominated by NVDA and BTC.\n\n"
        "WORKING:\n- NVDA: up 25%, riding the AI capex wave\n- BTC: up 50%, cycle tailwind\n\n"
        "NOT_WORKING:\n- (none today)\n\n"
        "WATCH: Concentration risk — two positions = 100% of your book.\n"
    )
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_response(text)
    with patch("lib.claude_portfolio.Anthropic", return_value=fake_client):
        out = explain_portfolio(VALUED, api_key="dummy", model="claude-haiku-4-5-20251001")
    assert "tech-heavy" in out["what_you_hold"]
    assert "NVDA: up 25%" in out["working"]
    assert "Concentration" in out["watch"]


def test_explain_returns_placeholder_on_error():
    fake_client = MagicMock()
    fake_client.messages.create.side_effect = RuntimeError("boom")
    with patch("lib.claude_portfolio.Anthropic", return_value=fake_client):
        out = explain_portfolio(VALUED, api_key="dummy", model="claude-haiku-4-5-20251001")
    assert out["error"] is not None
```

- [ ] **Step 2: Run, verify fail**

```bash
pytest tests/test_claude_portfolio.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `lib/claude_portfolio.py`**

```python
"""Plain-language portfolio explanation for a financial novice.

Output sections:
- what_you_hold (1 sentence)
- working / not_working (bullet lists)
- watch (1-2 sentences)
"""
from __future__ import annotations

import re
from anthropic import Anthropic


_SYSTEM = (
    "You are a calm financial explainer for someone who does NOT read finance well. "
    "Use plain language. If you must use a technical term, define it in parentheses on first use. "
    "Output ONLY the labeled sections requested. No introductions, no sign-offs."
)


def _user_prompt(positions: list[dict]) -> str:
    return f"""Given the portfolio below, produce EXACTLY these labeled sections.

WHAT_YOU_HOLD: <one sentence summary of the portfolio's character>

WORKING:
- <symbol>: <what is going well, one short clause>
(only positions with positive pnl_pct)

NOT_WORKING:
- <symbol>: <what is going wrong, one short clause>
(only positions with negative pnl_pct; write "(none today)" if empty)

WATCH: <1-2 sentences. Flag concentration risk, sector exposure, or any obvious imbalance. No jargon.>

POSITIONS: {positions}
"""


def _parse(text: str) -> dict:
    def grab(label: str, until: str | None) -> str:
        if until:
            m = re.search(rf"{label}:\s*(.+?)(?={until}:)", text, re.DOTALL)
        else:
            m = re.search(rf"{label}:\s*(.+)$", text, re.DOTALL)
        return m.group(1).strip() if m else ""

    return {
        "what_you_hold": grab("WHAT_YOU_HOLD", "WORKING"),
        "working": grab("WORKING", "NOT_WORKING"),
        "not_working": grab("NOT_WORKING", "WATCH"),
        "watch": grab("WATCH", None),
        "error": None,
    }


def explain_portfolio(positions: list[dict], api_key: str, model: str) -> dict:
    try:
        client = Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=1000,
            system=_SYSTEM,
            messages=[{"role": "user", "content": _user_prompt(positions)}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        return _parse(text)
    except Exception as exc:
        return {
            "what_you_hold": "Portfolio explanation unavailable right now.",
            "working": "", "not_working": "", "watch": "",
            "error": str(exc),
        }
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_claude_portfolio.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add lib/claude_portfolio.py tests/test_claude_portfolio.py
git commit -m "phase2:brief: portfolio Claude wrapper (plain-language, jargon-defined)"
```

---

### Task 2.8: `webui/app.py` — FastAPI scaffold + `POST /upload`

**Files:**
- Create: `webui/__init__.py`
- Create: `webui/app.py`
- Create: `webui/templates/index.html`
- Create: `tests/test_webui_upload.py`

- [ ] **Step 1: Write failing test**

```python
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from webui.app import app


def test_upload_generic_csv_returns_valued_positions():
    raw = Path("tests/fixtures/portfolio_generic.csv").read_bytes()
    client = TestClient(app)
    fake_prices_equity = {"NVDA": {"price": 500.0, "change_pct": 1.0, "prev_close": 495.0},
                          "TSLA": {"price": 280.0, "change_pct": -0.5, "prev_close": 281.5}}
    fake_prices_crypto = {"bitcoin": {"price_usd": 60000.0, "change_24h_pct": 0.1}}
    with patch("webui.app.fetch.fetch_equity_quotes", return_value=fake_prices_equity), \
         patch("webui.app.fetch.fetch_crypto_prices", return_value=fake_prices_crypto), \
         patch("webui.app.claude_portfolio.explain_portfolio", return_value={
             "what_you_hold": "ok", "working": "", "not_working": "", "watch": "", "error": None,
         }):
        r = client.post("/upload", files={"file": ("portfolio.csv", raw, "text/csv")})
    assert r.status_code == 200
    data = r.json()
    assert data["broker"] == "generic"
    assert any(p["symbol"] == "NVDA" for p in data["positions"])
    nvda = next(p for p in data["positions"] if p["symbol"] == "NVDA")
    assert nvda["current_price"] == 500.0


def test_upload_unparseable_returns_400():
    client = TestClient(app)
    r = client.post("/upload", files={"file": ("x.csv", b"junk\n", "text/csv")})
    assert r.status_code == 400
```

- [ ] **Step 2: Run, verify fail**

```bash
pytest tests/test_webui_upload.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `webui/app.py`**

```bash
mkdir -p webui/templates webui/static
touch webui/__init__.py
```

```python
"""FastAPI app for Surface B Portfolio Explorer.

Single endpoint POST /upload accepts a CSV, returns JSON with broker, positions,
allocation, AI explanation. Frontend (templates/index.html) is a thin
JS-driven view.
"""
from __future__ import annotations

import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

from lib import importers
from lib import fetch
from lib import portfolio as portfolio_mod
from lib import claude_portfolio


app = FastAPI(title="Morning Brief — Portfolio Explorer")

_HERE = Path(__file__).resolve().parent
_env = Environment(loader=FileSystemLoader(_HERE / "templates"), autoescape=select_autoescape(["html"]))

app.mount("/static", StaticFiles(directory=str(_HERE / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _env.get_template("index.html").render()


@app.post("/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    raw = await file.read()
    try:
        broker, raw_positions = importers.detect_and_parse(raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not raw_positions:
        raise HTTPException(status_code=400, detail="no positions parsed")

    equity_syms = [p["symbol"] for p in raw_positions if not _looks_crypto(p["symbol"])]
    crypto_ids = [_to_coingecko_id(p["symbol"]) for p in raw_positions if _looks_crypto(p["symbol"])]
    equity_quotes = fetch.fetch_equity_quotes(equity_syms) if equity_syms else {}
    crypto_quotes = fetch.fetch_crypto_prices([c for c in crypto_ids if c]) if crypto_ids else {}

    prices: dict[str, float] = {sym: q["price"] for sym, q in equity_quotes.items()}
    for p in raw_positions:
        if _looks_crypto(p["symbol"]):
            cg = _to_coingecko_id(p["symbol"])
            if cg and cg in crypto_quotes:
                prices[p["symbol"]] = crypto_quotes[cg]["price_usd"]

    valued = portfolio_mod.value_positions(raw_positions, prices)
    allocation = portfolio_mod.allocation_breakdown(valued)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    model = os.environ.get("CLAUDE_MODEL_PORTFOLIO", "claude-haiku-4-5-20251001")
    if api_key and api_key != "sk-ant-replace-me":
        commentary = claude_portfolio.explain_portfolio(valued, api_key=api_key, model=model)
    else:
        commentary = {"what_you_hold": "(set ANTHROPIC_API_KEY in .env to enable AI explanation)",
                      "working": "", "not_working": "", "watch": "", "error": "no_api_key"}

    return {
        "broker": broker,
        "positions": valued,
        "allocation": allocation,
        "commentary": commentary,
    }


_CRYPTO_MAP = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "BNB": "binancecoin",
    "HYPE": "hyperliquid", "TAO": "bittensor", "ADA": "cardano", "XRP": "ripple",
    "DOGE": "dogecoin", "AVAX": "avalanche-2", "LINK": "chainlink",
}


def _looks_crypto(sym: str) -> bool:
    return sym.upper() in _CRYPTO_MAP


def _to_coingecko_id(sym: str) -> str | None:
    return _CRYPTO_MAP.get(sym.upper())
```

- [ ] **Step 4: Write minimal `webui/templates/index.html`** — visual polish in Phase 3.

```html
<!DOCTYPE html><html><head>
<meta charset="utf-8"><title>Portfolio Explorer</title>
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/@picocss/pico@2.1.1/css/pico.min.css"
      integrity="sha384-L1dWfspMTHU/ApYnFiMz2QID/PlP1xCW9visvBdbEkOLkSSWsP6ZJWhPw6apiXxU"
      crossorigin="anonymous">
</head><body><main class="container">
<h1>Portfolio Explorer</h1>
<p>Drag-drop a CSV (IBKR / Binance / Coinbase / generic) below.</p>
<form id="f" enctype="multipart/form-data">
  <input type="file" id="csv" accept=".csv">
  <button type="button" onclick="upload()">Analyze</button>
</form>
<div id="out"></div>
<script>
async function upload(){
  const fd = new FormData();
  const f = document.getElementById('csv').files[0];
  if(!f) return;
  fd.append('file', f);
  const r = await fetch('/upload', {method:'POST', body: fd});
  if(!r.ok){
    document.getElementById('out').textContent = 'Upload failed: ' + r.status;
    return;
  }
  const d = await r.json();
  document.getElementById('out').innerHTML =
    '<h2>' + d.commentary.what_you_hold + '</h2>'
    + '<pre>' + JSON.stringify(d.positions, null, 2) + '</pre>';
}
</script>
</main></body></html>
```

- [ ] **Step 5: Run, verify pass**

```bash
pytest tests/test_webui_upload.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add webui/ tests/test_webui_upload.py
git commit -m "phase2:webui: FastAPI scaffold + POST /upload (minimal UI)"
```

---

### Task 2.9: `webui.py` — Surface B launcher

**Files:**
- Create: `webui.py`

- [ ] **Step 1: Implement (no test — boot-only script tested manually)**

```python
"""Surface B launcher. Starts uvicorn + opens browser."""
from __future__ import annotations

import os
import threading
import time
import webbrowser

import uvicorn
from dotenv import load_dotenv

from webui.app import app


def _open_browser():
    time.sleep(1.0)
    webbrowser.open("http://127.0.0.1:8765/")


def main() -> None:
    load_dotenv()
    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke test**

```bash
python webui.py &
SERVER_PID=$!
sleep 2
curl -s http://127.0.0.1:8765/ | head -5
kill $SERVER_PID
```

Expected: HTML containing "Portfolio Explorer".

- [ ] **Step 3: Commit**

```bash
git add webui.py
git commit -m "phase2:webui: launcher binds 127.0.0.1:8765 + opens browser"
```

---

## Phase 3 — UX visual rules (§11.5 of spec)

### Task 3.1: Polish `templates/dashboard.html` — thermometer + colored cards

**Files:**
- Modify: `templates/dashboard.html`

- [ ] **Step 1: Replace `templates/dashboard.html` with polished version**

```html
<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<title>Morning Brief — {{ date }}</title>
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/@picocss/pico@2.1.1/css/pico.min.css"
      integrity="sha384-L1dWfspMTHU/ApYnFiMz2QID/PlP1xCW9visvBdbEkOLkSSWsP6ZJWhPw6apiXxU"
      crossorigin="anonymous">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.6/dist/chart.umd.min.js"
        integrity="sha384-Sse/HDqcypGpyTDpvZOJNnG0TT3feGQUkF9H+mnRvic+LjR+K1NhTt8f51KIQ3v3"
        crossorigin="anonymous"></script>
<style>
  body { max-width: 1100px; margin: 1rem auto; padding: 0 1rem; }
  .hero { background: var(--pico-card-background-color); border-radius: 12px; padding: 1.2rem; margin: 1rem 0; }
  .hero h1 { font-size: 2.0rem; line-height: 1.2; margin: 0 0 .5rem; }
  .hero .tone { color: var(--pico-muted-color); }
  .grid-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: .6rem; }
  .card { padding: .8rem; border: 1px solid var(--pico-muted-border-color); border-radius: 10px; background: var(--pico-card-background-color); }
  .card .sym { font-weight: 700; font-size: 1.05rem; }
  .card .price { font-size: 1.2rem; margin: .2rem 0; }
  .card .chg { font-weight: 600; }
  .card .label { color: var(--pico-muted-color); font-size: .8rem; }
  .up { color: #1a7f37; } .down { color: #cf222e; } .neutral { color: #57606a; }
  .gauge-wrap { margin: 1rem 0; }
  .gauge { height: 36px; background: linear-gradient(90deg, #cf222e 0%, #d4a72c 20%, #1a7f37 50%, #d4a72c 80%, #cf222e 100%); position: relative; border-radius: 18px; box-shadow: inset 0 0 6px rgba(0,0,0,.2); }
  .gauge-marker { position: absolute; top: -8px; width: 6px; height: 52px; background: #1f2328; border-radius: 3px; }
  .gauge-labels { display: flex; justify-content: space-between; font-size: .75rem; color: var(--pico-muted-color); margin-top: .3rem; }
  .gauge-rating { text-align: center; font-size: 1.1rem; font-weight: 700; margin-top: .8rem; }
  details.glossary { margin-top: 2rem; }
  details.glossary summary { cursor: pointer; font-weight: 600; }
  details.glossary dl { display: grid; grid-template-columns: 130px 1fr; gap: .4rem .8rem; margin-top: .8rem; }
  details.glossary dt { font-weight: 600; }
  [data-tooltip] { border-bottom: 1px dotted var(--pico-muted-color); cursor: help; }
  .briefblock { white-space: pre-wrap; line-height: 1.55; }
</style>
</head><body>

<header class="hero">
  <h1>{{ commentary.headline or date }}</h1>
  <p class="tone"><em>{{ commentary.liquidity_tone }}</em></p>
</header>

<section>
  <h2>Overview</h2>
  <div class="grid-cards">
  {% for sym, data in equity.items() %}
    <div class="card">
      <div class="sym">{{ sym }}</div>
      <div class="price">${{ "%.2f"|format(data.price) }}</div>
      <div class="chg {{ 'up' if data.change_pct >= 0 else 'down' }}">
        {{ "%+.2f"|format(data.change_pct) }}%
      </div>
      <div class="label">vs prev close ${{ "%.2f"|format(data.prev_close) }}</div>
    </div>
  {% endfor %}
  {% for cg_id, data in crypto.items() %}
    <div class="card">
      <div class="sym">{{ cg_id }}</div>
      <div class="price">${{ "%.2f"|format(data.price_usd) }}</div>
      <div class="chg {{ 'up' if data.change_24h_pct >= 0 else 'down' }}">
        {{ "%+.2f"|format(data.change_24h_pct) }}%
      </div>
      <div class="label">24h change</div>
    </div>
  {% endfor %}
  {% if crypto_fng %}
    <div class="card">
      <div class="sym" data-tooltip="Crypto Fear & Greed: 0 = max fear, 100 = max greed">F&amp;G</div>
      <div class="price">{{ crypto_fng.value }}</div>
      <div class="chg neutral">{{ crypto_fng.classification }}</div>
      <div class="label">crypto sentiment</div>
    </div>
  {% endif %}
  </div>
</section>

<section class="gauge-wrap">
  <h2>BTC Bottom Score
    <small data-tooltip="0 = historical buy zone (extreme fear). 100 = historical sell zone (extreme greed). Built from 4 free indicators: ETF flows, funding rate, fear & greed, and futures long/short ratio.">{{ btc_score.total or "—" }}</small>
  </h2>
  <div class="gauge">
    {% if btc_score.total is not none %}
      <div class="gauge-marker" style="left: calc({{ btc_score.total }}% - 3px);"></div>
    {% endif %}
  </div>
  <div class="gauge-labels"><span>0 buy</span><span>50 neutral</span><span>100 sell</span></div>
  <div class="gauge-rating {{ 'up' if (btc_score.total or 50) < 30 else ('down' if (btc_score.total or 50) > 70 else 'neutral') }}">{{ btc_score.rating }}</div>
  <p>{{ commentary.btc_narrative }}</p>
</section>

<section>
  <h2>Holdings — what to watch today</h2>
  <div class="briefblock">{{ commentary.tickers_text }}</div>
</section>

<section>
  <h2>Top 10 things today</h2>
  <div class="briefblock">{{ commentary.top_10 }}</div>
</section>

<details class="glossary">
  <summary>Glossary — what these terms actually mean</summary>
  <dl>
    <dt>VIX</dt><dd>Wall Street's fear gauge. Above 25 = market expects unusually large daily swings.</dd>
    <dt>DXY</dt><dd>U.S. Dollar Index. Higher = dollar strong → headwind for stocks and BTC.</dd>
    <dt>Funding rate</dt><dd>What perpetual-futures longs pay shorts (or vice versa). Positive = traders bullish & paying to hold longs.</dd>
    <dt>Long/Short ratio</dt><dd>Share of retail futures accounts net long vs net short. &gt;1 = more longs than shorts.</dd>
    <dt>ETF net flow</dt><dd>Money entering (positive) or leaving (negative) U.S. spot BTC ETFs today, in USD millions.</dd>
    <dt>F&amp;G</dt><dd>Composite "how scared / how greedy is the crowd" index. 0 = panic, 100 = euphoria.</dd>
  </dl>
</details>

<footer><small>Data: yfinance · CoinGecko · alternative.me · farside.co.uk · Binance public. AI: Claude.</small></footer>
</body></html>
```

- [ ] **Step 2: Run render tests**

```bash
pytest tests/test_render.py -v
```

Expected: 2 passed (already-existing assertions still hold).

- [ ] **Step 3: Visual smoke test on Mac**

```bash
python morning_brief.py --no-open
open demos/$(date +%Y-%m-%d).html
```

Expected: dashboard with hero headline, colored ticker cards, thermometer gauge, glossary expander.

- [ ] **Step 4: Commit**

```bash
git add templates/dashboard.html
git commit -m "phase3:ux: thermometer gauge + colored cards + tooltips + glossary"
```

---

### Task 3.2: Polish `webui/templates/index.html` — donut + diverging bars + sparklines + drawer

**Files:**
- Modify: `webui/templates/index.html`

- [ ] **Step 1: Replace `webui/templates/index.html`**

```html
<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<title>Portfolio Explorer</title>
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/@picocss/pico@2.1.1/css/pico.min.css"
      integrity="sha384-L1dWfspMTHU/ApYnFiMz2QID/PlP1xCW9visvBdbEkOLkSSWsP6ZJWhPw6apiXxU"
      crossorigin="anonymous">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.6/dist/chart.umd.min.js"
        integrity="sha384-Sse/HDqcypGpyTDpvZOJNnG0TT3feGQUkF9H+mnRvic+LjR+K1NhTt8f51KIQ3v3"
        crossorigin="anonymous"></script>
<style>
  body { max-width: 1200px; margin: 1rem auto; padding: 0 1rem; }
  .drop { border: 2px dashed var(--pico-muted-border-color); border-radius: 12px; padding: 2rem; text-align: center; cursor: pointer; }
  .drop.dragover { background: var(--pico-card-background-color); border-color: var(--pico-primary); }
  .panels { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1.2rem; }
  @media (max-width: 800px) { .panels { grid-template-columns: 1fr; } }
  .panel { padding: 1rem; border: 1px solid var(--pico-muted-border-color); border-radius: 10px; background: var(--pico-card-background-color); }
  .pl-table { width: 100%; border-collapse: collapse; margin-top: .6rem; }
  .pl-table td, .pl-table th { padding: .4rem; border-bottom: 1px solid var(--pico-muted-border-color); font-size: .9rem; }
  .pl-bar { height: 18px; position: relative; background: #f6f8fa; border-radius: 4px; overflow: hidden; }
  .pl-bar-fill { position: absolute; top: 0; height: 100%; }
  .up { color: #1a7f37; } .down { color: #cf222e; }
  .bg-up { background: #1a7f37; } .bg-down { background: #cf222e; }
  .ai-panel { margin-top: 1rem; padding: 1.2rem; background: var(--pico-card-background-color); border-radius: 10px; }
  .ai-panel h3 { margin: .5rem 0 .2rem; font-size: 1rem; }
  .glossary { margin-top: 2rem; }
</style>
</head><body><main>

<header>
  <h1>Portfolio Explorer</h1>
  <p>Drag-drop a broker CSV. Supported: <strong>IBKR Activity Statement</strong>, <strong>Binance Trade History</strong>, <strong>Coinbase Account</strong>. Falls back to a generic CSV if column names match.</p>
</header>

<div id="drop" class="drop">
  <input type="file" id="csv" accept=".csv" style="display: none;">
  <p>📂 Drop your CSV here, or click to pick</p>
  <p id="status" style="color: var(--pico-muted-color);"></p>
</div>

<div id="results" style="display: none;">
  <div class="panels">
    <div class="panel">
      <h2>Allocation</h2>
      <canvas id="donut" height="280"></canvas>
    </div>
    <div class="panel">
      <h2>P&amp;L by position</h2>
      <table class="pl-table">
        <thead><tr><th>Symbol</th><th>Qty</th><th>Price</th><th>P&amp;L %</th><th></th></tr></thead>
        <tbody id="pl-body"></tbody>
      </table>
    </div>
  </div>

  <div class="ai-panel">
    <h2>In plain language</h2>
    <h3>What you hold</h3>
    <p id="ai-what"></p>
    <h3>What's working</h3>
    <div id="ai-working" style="white-space: pre-wrap;"></div>
    <h3>What's not working</h3>
    <div id="ai-notworking" style="white-space: pre-wrap;"></div>
    <h3>What to watch</h3>
    <p id="ai-watch"></p>
  </div>

  <details class="glossary">
    <summary>Glossary</summary>
    <dl>
      <dt>Allocation</dt><dd>How your money is split across positions, in percent of total current value.</dd>
      <dt>P&amp;L %</dt><dd>Profit or loss compared to your average purchase price. Green = gain, red = loss.</dd>
      <dt>Concentration risk</dt><dd>One holding being too large a share of your portfolio. If it drops, your whole portfolio drops with it.</dd>
    </dl>
  </details>
</div>

<script>
const drop = document.getElementById('drop');
const csv = document.getElementById('csv');
drop.addEventListener('click', () => csv.click());
['dragover','dragenter'].forEach(e => drop.addEventListener(e, ev => {ev.preventDefault(); drop.classList.add('dragover');}));
['dragleave','drop'].forEach(e => drop.addEventListener(e, () => drop.classList.remove('dragover')));
drop.addEventListener('drop', async ev => {
  ev.preventDefault();
  if(ev.dataTransfer.files[0]) await upload(ev.dataTransfer.files[0]);
});
csv.addEventListener('change', async () => { if(csv.files[0]) await upload(csv.files[0]); });

let donutChart;

async function upload(file){
  document.getElementById('status').textContent = 'Analyzing ' + file.name + ' ...';
  const fd = new FormData();
  fd.append('file', file);
  const r = await fetch('/upload', {method: 'POST', body: fd});
  if(!r.ok){
    document.getElementById('status').textContent = 'Failed: ' + (await r.text());
    return;
  }
  const d = await r.json();
  document.getElementById('status').textContent = 'Detected: ' + d.broker;
  render(d);
}

function render(d){
  document.getElementById('results').style.display = 'block';
  renderDonut(d.allocation);
  renderPLTable(d.positions);
  document.getElementById('ai-what').textContent = d.commentary.what_you_hold;
  document.getElementById('ai-working').textContent = d.commentary.working;
  document.getElementById('ai-notworking').textContent = d.commentary.not_working;
  document.getElementById('ai-watch').textContent = d.commentary.watch;
}

function renderDonut(alloc){
  if(donutChart) donutChart.destroy();
  donutChart = new Chart(document.getElementById('donut'), {
    type: 'doughnut',
    data: {
      labels: alloc.map(a => a.symbol),
      datasets: [{
        data: alloc.map(a => (a.weight * 100).toFixed(2)),
      }],
    },
    options: {plugins: {legend: {position: 'right'}}}
  });
}

function renderPLTable(positions){
  const sorted = [...positions].sort((a,b) => Math.abs(b.pnl_abs) - Math.abs(a.pnl_abs));
  const maxAbs = Math.max(...sorted.map(p => Math.abs(p.pnl_pct)), 1);
  document.getElementById('pl-body').innerHTML = sorted.map(p => {
    const cls = p.pnl_pct >= 0 ? 'up' : 'down';
    const bgcls = p.pnl_pct >= 0 ? 'bg-up' : 'bg-down';
    const widthPct = Math.min(100, Math.abs(p.pnl_pct) / maxAbs * 100);
    return `<tr>
      <td><strong>${p.symbol}</strong></td>
      <td>${p.qty.toFixed(4)}</td>
      <td>$${p.current_price.toFixed(2)}</td>
      <td class="${cls}">${p.pnl_pct.toFixed(1)}%</td>
      <td><div class="pl-bar"><div class="pl-bar-fill ${bgcls}" style="width: ${widthPct}%"></div></div></td>
    </tr>`;
  }).join('');
}
</script>
</main></body></html>
```

- [ ] **Step 2: Run webui tests**

```bash
pytest tests/test_webui_upload.py -v
```

Expected: 2 passed.

- [ ] **Step 3: Live smoke test**

```bash
python webui.py &
SERVER_PID=$!
sleep 2
open http://127.0.0.1:8765/
# manually drop a tests/fixtures/portfolio_generic.csv
kill $SERVER_PID
```

Expected: page loads, drop zone visible, dropping the CSV renders donut + table + AI panel.

- [ ] **Step 4: Commit**

```bash
git add webui/templates/index.html
git commit -m "phase3:ux: donut + diverging P&L bars + AI panel + glossary"
```

---

## Phase 4 — Polish, README, launchd

### Task 4.1: Write README.md

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`**

```markdown
# Morning Brief

A portable, single-folder market-intelligence tool. Two surfaces:

- **Daily Brief** — automated daily snapshot of US equities + crypto + AI-written commentary, rendered as a self-contained HTML file you can share with anyone (no install, no warnings).
- **Portfolio Explorer** — local web UI: drop a broker CSV (IBKR / Binance / Coinbase / generic), get a visualized portfolio dashboard with plain-language explanation.

Both are built for non-traders: charts dominate, every term is defined, color is consistent (green = up, red = down).

![demo](demo.gif)

## 60-second quickstart

```bash
git clone <this-repo>
cd morning-brief
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your ANTHROPIC_API_KEY
python morning_brief.py        # → opens viewer.html with today's snapshot
python webui.py                 # → opens http://127.0.0.1:8765 for portfolio CSV upload
```

## Daily Brief

`python morning_brief.py [--no-open] [--commit] [--push]`

- Fetches 9 overview tickers + crypto F&G + BTC ETF flow + funding rate + long/short ratio
- Computes a 0–100 **BTC bottom score** from 4 free daily indicators (full Day1Global 13-indicator model deferred — paid on-chain metrics live in P2)
- Calls Claude to produce a plain-language headline, liquidity tone, per-ticker thesis, BTC narrative, and "today's top 10"
- Writes `snapshots/YYYY-MM-DD.json` (raw data + AI text) and `demos/YYYY-MM-DD.html` (self-contained, no external data fetches, shareable)
- `--commit --push` flags suitable for a Mac mini launchd job

## Portfolio Explorer

`python webui.py` → opens `http://127.0.0.1:8765/` in your browser. Drop a CSV:

| Broker | Format expected |
|---|---|
| Interactive Brokers | Activity Statement CSV |
| Binance | Trade History CSV |
| Coinbase / Coinbase Pro | Account export CSV |
| Generic | Any CSV with columns named `symbol`, `quantity`, `cost` (any reasonable variant) |

You see: allocation donut, P&L by position, plain-language explanation panel.

The server binds to `127.0.0.1` only. Uploaded portfolios stay in `portfolios/` and are git-ignored.

## Cross-platform

| Platform | Run |
|---|---|
| macOS | `python3 morning_brief.py` or `python3 webui.py` |
| Windows 11 | same (Python 3 from python.org or store) |
| iPhone | Working Copy → `git pull` → tap `viewer.html` → Safari renders the latest snapshot |

## Mac mini daily schedule

Install a LaunchAgent that runs the Daily Brief at 08:00 Europe/Rome:

```bash
./scripts/install_launchd.sh
```

(See `scripts/install_launchd.sh` for details.)

## Data sources

| Source | Used for | Cost |
|---|---|---|
| yfinance | equity prices, VIX, DXY, gold, oil | free |
| CoinGecko | crypto spot prices | free |
| alternative.me | Crypto Fear & Greed Index | free |
| farside.co.uk | BTC spot ETF net flows | free |
| Binance public futures | funding rate, long/short ratio | free |
| Anthropic Claude | written commentary | API key, ~$0.05/day |

## Project layout

```
morning_brief.py    Daily Brief entrypoint (Surface A)
webui.py            Portfolio Explorer entrypoint (Surface B)
lib/                shared backend: fetch, score, claude_brief, claude_portfolio, portfolio, importers/
templates/          Daily Brief Jinja template
webui/              FastAPI app + Portfolio Explorer template
snapshots/          generated daily JSON
demos/              generated daily self-contained HTML (shareable)
portfolios/         uploaded CSVs (git-ignored)
config/watchlist.json   editable list of equity + crypto tickers
docs/superpowers/   design spec + implementation plan
```

## Roadmap (P2)

- Glassnode paid on-chain indicators → full 13-indicator BTC bottom score
- Fund Finance Lens — sector ETF flows + concentration tracking (UniCredit application bridge)
- Custom watchlist CSV/JSON upload in WebUI
- PDF / DOCX document parsing — upload an earnings report, Claude extracts plain-language key findings
- GitHub Pages public deploy serving `demos/`
- Evening run at 22:00 IT (US close summary)
- Mobile-tuned layout
- Telegram / Mac notification on extreme readings
- Portfolio Explorer PDF export
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "phase4:docs: README with quickstart + project layout + roadmap"
```

---

### Task 4.2: Write Mac mini launchd installer

**Files:**
- Create: `scripts/install_launchd.sh`
- Create: `scripts/com.jiawen.morning-brief.plist`

- [ ] **Step 1: Write `scripts/com.jiawen.morning-brief.plist`**

```bash
mkdir -p scripts
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.jiawen.morning-brief</string>
  <key>ProgramArguments</key>
  <array>
    <string>__VENV_PYTHON__</string>
    <string>__REPO_ROOT__/morning_brief.py</string>
    <string>--no-open</string>
    <string>--commit</string>
    <string>--push</string>
  </array>
  <key>WorkingDirectory</key>
  <string>__REPO_ROOT__</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key><integer>8</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>__REPO_ROOT__/.launchd.out.log</string>
  <key>StandardErrorPath</key>
  <string>__REPO_ROOT__/.launchd.err.log</string>
  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
```

- [ ] **Step 2: Write `scripts/install_launchd.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PYTHON="$REPO_ROOT/.venv/bin/python"
TARGET="$HOME/Library/LaunchAgents/com.jiawen.morning-brief.plist"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "Error: venv python not found at $VENV_PYTHON"
  echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

mkdir -p "$(dirname "$TARGET")"
sed -e "s|__VENV_PYTHON__|$VENV_PYTHON|g" \
    -e "s|__REPO_ROOT__|$REPO_ROOT|g" \
    "$REPO_ROOT/scripts/com.jiawen.morning-brief.plist" > "$TARGET"

launchctl unload "$TARGET" 2>/dev/null || true
launchctl load "$TARGET"

echo "Installed LaunchAgent at $TARGET"
echo "Will fire daily at 08:00 local time."
echo "Logs: $REPO_ROOT/.launchd.{out,err}.log"
echo ""
echo "To run once now (verify):"
echo "  launchctl start com.jiawen.morning-brief"
echo ""
echo "To remove:"
echo "  launchctl unload $TARGET && rm $TARGET"
```

- [ ] **Step 3: chmod and commit**

```bash
chmod +x scripts/install_launchd.sh
git add scripts/
git commit -m "phase4:cron: Mac mini launchd installer (08:00 daily, commit+push)"
```

---

### Task 4.3: Record demo GIF / MP4

**Files:**
- Create: `demo.gif` (or `demo.mp4`)
- Modify: `README.md` (if MP4 instead of GIF)

- [ ] **Step 1: Record screen with macOS native tool**

Run:
```bash
# Press Cmd+Shift+5 → select "Record Selected Portion" → record ~20 seconds:
#   1. Open terminal, run `python morning_brief.py`
#   2. Show the dashboard loading in browser
#   3. Switch to terminal, run `python webui.py`
#   4. Drag tests/fixtures/portfolio_generic.csv into the drop zone
#   5. Show the donut + table populating
# Save the .mov to ~/Desktop/morning-brief-demo.mov
```

- [ ] **Step 2: Convert .mov → demo.gif**

Run:
```bash
# Requires ffmpeg. Install via: brew install ffmpeg
ffmpeg -i ~/Desktop/morning-brief-demo.mov -vf "fps=10,scale=720:-1:flags=lanczos" -loop 0 demo.gif
ls -lh demo.gif
```

Expected: a `demo.gif` under 5 MB. If larger, lower fps to 8 or scale to 600.

- [ ] **Step 3: Commit**

```bash
git add demo.gif
git commit -m "phase4:docs: demo GIF showing both surfaces"
```

---

### Task 4.4: End-to-end live smoke + final verification

**Files:** (none changed; verification only)

- [ ] **Step 1: Run full test suite**

```bash
pytest -q
```

Expected: all tests pass; report shows ~25+ tests.

- [ ] **Step 2: Surface A live run (Mac, requires real ANTHROPIC_API_KEY in .env)**

```bash
python morning_brief.py
```

Expected: browser opens to `viewer.html`. Snapshot JSON in `snapshots/`. Demo HTML in `demos/`. Check: thermometer renders, colored ticker cards visible, glossary expander present.

- [ ] **Step 3: Surface A demo share test**

```bash
open demos/$(date +%Y-%m-%d).html
```

Open this file from a separate browser (or share with someone) — confirm it renders without ANY network calls and contains no `ANTHROPIC_API_KEY` substring.

```bash
grep -c "sk-ant" demos/*.html
```

Expected: 0.

- [ ] **Step 4: Surface B live run with fixture**

```bash
python webui.py
# in browser: drop tests/fixtures/portfolio_generic.csv
# verify: donut shows NVDA/TSLA/BTC, table shows P&L %, AI panel populates
```

- [ ] **Step 5: Surface B live run with personal data**

Drop your real broker CSV (IBKR / Binance / Coinbase) into the WebUI. Confirm:
- Auto-detection picks the right broker
- Real positions render correctly
- `portfolios/<filename>-parsed.json` exists and is ignored by `git status`

- [ ] **Step 6: Win VM sanity check**

In the Parallels Win 11 VM with Python 3 installed:

```powershell
cd C:\Users\macmini\Desktop\morning-brief   # or wherever shared folder maps to
python morning_brief.py --no-open
python webui.py
```

Expected: both surfaces work; no symlink errors (latest.json is a copy).

- [ ] **Step 7: Final tag**

```bash
git tag p1-v1.0.0 -m "Morning Brief P1 shipped"
git log --oneline | head -20
```

- [ ] **Step 8: Done — push to remote (after user adds origin)**

```bash
# user adds the remote first
# git remote add origin git@github.com:<user>/morning-brief.git
git push -u origin main --tags
```

---

## Self-Review

**Spec coverage check:**

| Spec section | Task(s) |
|---|---|
| §1 One-liner / two surfaces | 1.10 + 2.9 |
| §2 Goals 1-6 | All phases |
| §3 Non-goals | (negative; nothing to implement) |
| §4 Why not a desktop app | (documented in README §1) |
| §5 Architecture | Phase 0 + every task creates an entry in the layout |
| §5.1 Data flow | 1.6 + 1.10 |
| §5.2 Cross-platform sync | 4.2 launchd + Win VM test in 4.4 step 6 |
| §5.3 Surface B run model | 2.8 + 2.9 |
| §5.4 Demo distribution | 1.9 (self-contained HTML) + 4.4 step 3 |
| §6 P1 modules — overview | 1.1 + 1.2 + 1.3 + 1.6 |
| §6 P1 modules — holdings | 1.3 (equity) + 1.2 (crypto) |
| §6 P1 modules — AI brief | 1.8 |
| §6 P1 modules — BTC score | 1.4 + 1.5 + 1.7 |
| §6.1 Weights table | 1.7 |
| §7 Module boundaries | One file per task; verified by file structure |
| §8 Error handling | 1.6 partial run + 1.7 partial score + 1.8 / 2.7 placeholder on Claude failure |
| §9 Testing | TDD throughout |
| §10 launchd schedule | 4.2 |
| §11 Repository plan | Phase 0 + handoff at end of 4.4 |
| §11.5 Visual / UX rules | Phase 3 (3.1 + 3.2) |
| §12 P2 backlog | Documented in README (4.1) |
| §13 Open items | Will be raised in subagent-driven execution |
| §14 Acceptance criteria | 4.4 covers all bullets |

No gaps. No placeholders left in plan body.

**Type consistency:** function names verified — `fetch.run`, `score.btc_bottom_score`, `claude_brief.compose`, `claude_portfolio.explain_portfolio`, `render.render_self_contained`, `render.render_live_viewer`, `importers.detect_and_parse`, `portfolio.value_positions`, `portfolio.allocation_breakdown` — all match across tasks.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-05-morning-brief.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
