import json
from pathlib import Path
import responses
from lib.fetch import fetch_btc_funding_rate, fetch_btc_long_short_ratio

FUNDING = json.loads(Path("tests/fixtures/binance_funding.json").read_text())
LSR = json.loads(Path("tests/fixtures/binance_lsr.json").read_text())


@responses.activate
def test_fetch_btc_funding_rate():
    responses.add(
        responses.GET,
        "https://fapi.binance.com/fapi/v1/premiumIndex",
        json=FUNDING,
        status=200,
    )
    rate = fetch_btc_funding_rate()
    assert rate is not None
    assert abs(rate - 0.000085) < 1e-9


@responses.activate
def test_fetch_btc_long_short_ratio():
    responses.add(
        responses.GET,
        "https://fapi.binance.com/futures/data/globalLongShortAccountRatio",
        json=LSR,
        status=200,
    )
    ratio = fetch_btc_long_short_ratio()
    assert ratio is not None
    assert abs(ratio - 1.85) < 1e-9
