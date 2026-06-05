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
