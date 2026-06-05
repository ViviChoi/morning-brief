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
