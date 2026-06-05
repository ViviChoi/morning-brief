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
