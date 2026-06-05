import json
import os
from pathlib import Path
from unittest.mock import patch
import sys


def test_orchestrator_writes_snapshot_and_demo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "snapshots").mkdir()
    (tmp_path / "demos").mkdir()
    (tmp_path / "config" / "watchlist.json").write_text(json.dumps({
        "equities": [{"symbol": "SPY", "name": "S&P"}],
        "crypto": [{"symbol": "BTC", "coingecko_id": "bitcoin"}],
        "overview": [{"symbol": "SPY", "label": "S&P"}],
    }))
    # Copy templates so jinja loader finds them
    repo_root = Path(__file__).resolve().parent.parent
    src_tpl = repo_root / "templates"
    if src_tpl.exists():
        import shutil
        shutil.copytree(src_tpl, tmp_path / "templates")
    # Force lib import path
    sys.path.insert(0, str(repo_root))
    from lib.fetch import run as fetch_run  # noqa
    fake_snapshot = {
        "equity": {"SPY": {"price": 540.0, "prev_close": 535.0, "change_pct": 0.93}},
        "crypto": {"bitcoin": {"price_usd": 68500.0, "change_24h_pct": -1.0}},
        "crypto_fng": {"value": 42, "classification": "Fear"},
        "btc_signals": {"funding_rate": 0.00008, "long_short_ratio": 1.85, "etf_net_flow_musd": 213.2},
        "_errors": [],
    }
    fake_commentary = {
        "headline": "ok", "liquidity_tone": "ok", "tickers_text": "ok",
        "btc_narrative": "ok", "top_10": "ok", "error": None,
    }
    with patch("lib.fetch.run", return_value=fake_snapshot), \
         patch("lib.claude_brief.compose", return_value=fake_commentary):
        import morning_brief
        rc = morning_brief.main(["--no-open"])
    assert rc == 0
    snapshots = list((tmp_path / "snapshots").glob("*.json"))
    demos = list((tmp_path / "demos").glob("*.html"))
    assert len(snapshots) >= 1
    assert len(demos) >= 1
    snap = json.loads((tmp_path / "snapshots" / "latest.json").read_text())
    assert snap["btc_score"]["total"] is not None
