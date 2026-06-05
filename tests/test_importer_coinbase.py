from pathlib import Path
from lib.importers.coinbase import parse_coinbase_csv


def test_parse_coinbase_aggregates_per_asset():
    raw = Path("tests/fixtures/portfolio_coinbase.csv").read_bytes()
    out = parse_coinbase_csv(raw)
    syms = {p["symbol"]: p for p in out}
    assert syms["BTC"]["qty"] == 0.08
    assert abs(syms["BTC"]["cost"] - 42000) < 1e-3
    assert syms["ETH"]["qty"] == 2
