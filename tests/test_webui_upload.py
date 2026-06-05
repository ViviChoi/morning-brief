from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from webui.app import app


def test_upload_generic_csv_returns_valued_positions():
    raw = Path("tests/fixtures/portfolio_generic.csv").read_bytes()
    client = TestClient(app)
    fake_prices_equity = {"NVDA": {"price": 500.0, "change_pct": 1.0, "prev_close": 495.0},
                          "TSLA": {"price": 280.0, "change_pct": -0.5, "prev_close": 281.5}}
    fake_prices_crypto = {"bitcoin": {"price_usd": 60000.0, "change_24h_pct": 0.1}}
    with patch("webui.app.fetch.fetch_equity_quotes", return_value=fake_prices_equity), \
         patch("webui.app.fetch.fetch_crypto_prices", return_value=fake_prices_crypto), \
         patch("webui.app.claude_portfolio.explain_portfolio", return_value={
             "what_you_hold": "ok", "working": "", "not_working": "", "watch": "", "error": None,
         }):
        r = client.post("/upload", files={"file": ("portfolio.csv", raw, "text/csv")})
    assert r.status_code == 200
    data = r.json()
    assert data["broker"] == "generic"
    assert any(p["symbol"] == "NVDA" for p in data["positions"])
    nvda = next(p for p in data["positions"] if p["symbol"] == "NVDA")
    assert nvda["current_price"] == 500.0


def test_upload_unparseable_returns_400():
    client = TestClient(app)
    r = client.post("/upload", files={"file": ("x.csv", b"junk\n", "text/csv")})
    assert r.status_code == 400
