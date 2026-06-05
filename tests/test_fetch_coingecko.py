import json
from pathlib import Path
import responses
from lib.fetch import fetch_crypto_prices

FIXTURE = json.loads(Path("tests/fixtures/coingecko_simple_price.json").read_text())


@responses.activate
def test_fetch_crypto_prices_returns_normalized_dict():
    responses.add(
        responses.GET,
        "https://api.coingecko.com/api/v3/simple/price",
        json=FIXTURE,
        status=200,
    )
    result = fetch_crypto_prices(["bitcoin", "ethereum"])
    assert result["bitcoin"]["price_usd"] == 68500.12
    assert result["bitcoin"]["change_24h_pct"] == -1.8
    assert result["ethereum"]["price_usd"] == 3625.44


@responses.activate
def test_fetch_crypto_prices_returns_empty_on_error():
    responses.add(
        responses.GET,
        "https://api.coingecko.com/api/v3/simple/price",
        status=429,
    )
    assert fetch_crypto_prices(["bitcoin"]) == {}
