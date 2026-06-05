from unittest.mock import patch, MagicMock
from lib.claude_brief import compose


SNAPSHOT = {
    "equity": {"SPY": {"price": 540.0, "change_pct": 0.5}},
    "crypto": {"bitcoin": {"price_usd": 68500.0, "change_24h_pct": -1.0}},
    "crypto_fng": {"value": 42, "classification": "Fear"},
    "btc_signals": {"funding_rate": 0.00008, "long_short_ratio": 1.85, "etf_net_flow_musd": 213.2},
    "btc_score": {"total": 38, "rating": "Fear"},
    "_errors": [],
}


def _fake_response(text: str):
    msg = MagicMock()
    msg.content = [MagicMock(type="text", text=text)]
    msg.stop_reason = "end_turn"
    return msg


def test_compose_returns_all_sections():
    fake_text = (
        "HEADLINE: Markets neutral, BTC in fear zone.\n\n"
        "LIQUIDITY_TONE: Slightly tight, VIX moderate.\n\n"
        "TICKERS:\n- SPY: index drifting near highs\n\n"
        "BTC_NARRATIVE: Score 38 suggests historically a measured-risk zone, not a buy yet.\n\n"
        "TOP_10:\n1. Fed meeting next week — rates likely on hold\n"
    )
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_response(fake_text)
    with patch("lib.claude_brief.Anthropic", return_value=fake_client):
        out = compose(SNAPSHOT, api_key="dummy", model="claude-sonnet-4-6")
    assert "Markets neutral" in out["headline"]
    assert "Slightly tight" in out["liquidity_tone"]
    assert "drifting near highs" in out["tickers_text"]
    assert "Score 38" in out["btc_narrative"]
    assert "Fed meeting" in out["top_10"]


def test_compose_returns_placeholders_on_api_failure():
    fake_client = MagicMock()
    fake_client.messages.create.side_effect = RuntimeError("rate limited")
    with patch("lib.claude_brief.Anthropic", return_value=fake_client):
        out = compose(SNAPSHOT, api_key="dummy", model="claude-sonnet-4-6")
    assert out["headline"] == "AI commentary unavailable today."
    assert out["error"] is not None
