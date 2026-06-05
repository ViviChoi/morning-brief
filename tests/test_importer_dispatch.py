from pathlib import Path
from lib.importers import detect_and_parse


def test_detect_ibkr_by_first_line():
    raw = Path("tests/fixtures/portfolio_ibkr.csv").read_bytes()
    broker, positions = detect_and_parse(raw)
    assert broker == "ibkr"
    assert len(positions) >= 1


def test_detect_binance_by_headers():
    raw = Path("tests/fixtures/portfolio_binance.csv").read_bytes()
    broker, positions = detect_and_parse(raw)
    assert broker == "binance"


def test_detect_coinbase_by_headers():
    raw = Path("tests/fixtures/portfolio_coinbase.csv").read_bytes()
    broker, positions = detect_and_parse(raw)
    assert broker == "coinbase"


def test_detect_generic_fallback():
    raw = Path("tests/fixtures/portfolio_generic.csv").read_bytes()
    broker, positions = detect_and_parse(raw)
    assert broker == "generic"
