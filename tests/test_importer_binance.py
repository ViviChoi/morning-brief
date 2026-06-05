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
