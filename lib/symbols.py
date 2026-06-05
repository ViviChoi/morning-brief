"""Symbol → CoinGecko ID lookup for common crypto tickers.

Used by the WebUI to route uploaded-CSV symbols to the right price source
(equity tickers go to yfinance; crypto tickers go to CoinGecko).

This is a static fallback. The owner's watchlist (config/watchlist.json) may
contain more authoritative mappings — callers can layer them on top.
"""
from __future__ import annotations

CRYPTO_TO_COINGECKO: dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "HYPE": "hyperliquid",
    "TAO": "bittensor",
    "ADA": "cardano",
    "XRP": "ripple",
    "DOGE": "dogecoin",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
}


def is_crypto(symbol: str) -> bool:
    """Return True if `symbol` is a known crypto ticker."""
    return symbol.upper() in CRYPTO_TO_COINGECKO


def to_coingecko_id(symbol: str) -> str | None:
    """Return the CoinGecko ID for a crypto ticker, or None if not known."""
    return CRYPTO_TO_COINGECKO.get(symbol.upper())
