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
