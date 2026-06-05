import json
from pathlib import Path
import responses
from lib.fetch import fetch_crypto_fng


FIXTURE = json.loads(Path("tests/fixtures/alternative_me_fng.json").read_text())


@responses.activate
def test_fetch_crypto_fng_returns_value_and_classification():
    responses.add(
        responses.GET,
        "https://api.alternative.me/fng/",
        json=FIXTURE,
        status=200,
    )
    result = fetch_crypto_fng()
    assert result["value"] == 42
    assert result["classification"] == "Fear"


@responses.activate
def test_fetch_crypto_fng_returns_none_on_error():
    responses.add(
        responses.GET,
        "https://api.alternative.me/fng/",
        status=500,
    )
    result = fetch_crypto_fng()
    assert result is None
