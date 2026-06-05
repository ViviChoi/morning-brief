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
