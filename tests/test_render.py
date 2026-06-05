import json
from pathlib import Path
from lib.render import render_self_contained, render_live_viewer


SNAPSHOT = {
    "date": "2026-06-05",
    "equity": {"SPY": {"price": 540.0, "prev_close": 535.0, "change_pct": 0.93}},
    "crypto": {"bitcoin": {"price_usd": 68500.0, "change_24h_pct": -1.0}},
    "crypto_fng": {"value": 42, "classification": "Fear"},
    "btc_signals": {"funding_rate": 0.00008, "long_short_ratio": 1.85, "etf_net_flow_musd": 213.2},
    "btc_score": {"total": 38, "rating": "Fear", "components": {}, "partial": False},
    "commentary": {
        "headline": "Calm tape, BTC in fear zone.",
        "liquidity_tone": "Tight but not dangerous.",
        "tickers_text": "- SPY: drifting near highs",
        "btc_narrative": "Score 38 = measured-risk zone.",
        "top_10": "1. Fed meeting next week — rates on hold",
        "error": None,
    },
    "_errors": [],
}


def test_render_self_contained_inlines_data():
    html = render_self_contained(SNAPSHOT)
    assert "Calm tape" in html
    assert "SPY" in html
    assert "<script" in html  # has inlined JS
    assert "fetch(" not in html  # no external data fetches
    assert "2026-06-05" in html


def test_render_live_viewer_references_latest_json(tmp_path: Path):
    out = tmp_path / "viewer.html"
    render_live_viewer(out)
    html = out.read_text()
    assert "snapshots/latest.json" in html
    assert "<script" in html
