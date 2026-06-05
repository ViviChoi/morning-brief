from lib.symbols import is_crypto, to_coingecko_id, CRYPTO_TO_COINGECKO


def test_is_crypto_known_tickers():
    for sym in ["BTC", "ETH", "SOL", "BNB"]:
        assert is_crypto(sym)
        assert is_crypto(sym.lower())


def test_is_crypto_rejects_equities():
    for sym in ["NVDA", "TSLA", "SPY", "VIX"]:
        assert not is_crypto(sym)


def test_to_coingecko_id_returns_known_id():
    assert to_coingecko_id("BTC") == "bitcoin"
    assert to_coingecko_id("eth") == "ethereum"
    assert to_coingecko_id("AVAX") == "avalanche-2"


def test_to_coingecko_id_returns_none_for_unknown():
    assert to_coingecko_id("UNKNOWN") is None
    assert to_coingecko_id("") is None


def test_map_contains_owners_default_watchlist():
    """The owner's default watchlist crypto symbols must all be mappable."""
    defaults = ["BTC", "ETH", "SOL", "BNB", "HYPE", "TAO"]
    for sym in defaults:
        assert sym in CRYPTO_TO_COINGECKO, f"{sym} missing from CRYPTO_TO_COINGECKO"
