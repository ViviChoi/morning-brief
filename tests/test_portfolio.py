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
    nvda = next(a for a in alloc if a["symbol"] == "NVDA")
    assert abs(nvda["weight"] - 25000 / 55000) < 1e-6


def test_value_positions_skips_unpriced_symbols():
    out = value_positions(RAW, {"NVDA": 500.0})
    syms = {p["symbol"] for p in out}
    assert "NVDA" in syms
    assert "BTC" not in syms
