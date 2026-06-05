from unittest.mock import patch, MagicMock
from lib.claude_portfolio import explain_portfolio


VALUED = [
    {"symbol": "NVDA", "qty": 50, "cost": 400.0, "current_price": 500.0,
     "current_value": 25000.0, "pnl_abs": 5000.0, "pnl_pct": 25.0},
    {"symbol": "BTC", "qty": 0.5, "cost": 40000.0, "current_price": 60000.0,
     "current_value": 30000.0, "pnl_abs": 10000.0, "pnl_pct": 50.0},
]


def _fake_response(text: str):
    msg = MagicMock()
    msg.content = [MagicMock(type="text", text=text)]
    return msg


def test_explain_returns_three_blocks():
    text = (
        "WHAT_YOU_HOLD: You hold a tech-heavy portfolio dominated by NVDA and BTC.\n\n"
        "WORKING:\n- NVDA: up 25%, riding the AI capex wave\n- BTC: up 50%, cycle tailwind\n\n"
        "NOT_WORKING:\n- (none today)\n\n"
        "WATCH: Concentration risk — two positions = 100% of your book.\n"
    )
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_response(text)
    with patch("lib.claude_portfolio.Anthropic", return_value=fake_client):
        out = explain_portfolio(VALUED, api_key="dummy", model="claude-haiku-4-5-20251001")
    assert "tech-heavy" in out["what_you_hold"]
    assert "NVDA: up 25%" in out["working"]
    assert "Concentration" in out["watch"]


def test_explain_returns_placeholder_on_error():
    fake_client = MagicMock()
    fake_client.messages.create.side_effect = RuntimeError("boom")
    with patch("lib.claude_portfolio.Anthropic", return_value=fake_client):
        out = explain_portfolio(VALUED, api_key="dummy", model="claude-haiku-4-5-20251001")
    assert out["error"] is not None
