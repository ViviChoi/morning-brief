"""Surface A entrypoint. One invocation = one snapshot.

CLI:
    python morning_brief.py [--no-open] [--commit] [--push]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

from dotenv import load_dotenv

from lib import fetch as fetch_mod
from lib import score as score_mod
from lib import claude_brief
from lib import render as render_mod


def _load_watchlist(root: Path) -> dict:
    return json.loads((root / "config" / "watchlist.json").read_text())


def _today_iso() -> str:
    return dt.date.today().isoformat()


def _write_snapshot(root: Path, snapshot: dict) -> Path:
    snaps = root / "snapshots"
    snaps.mkdir(exist_ok=True)
    today = root / "snapshots" / f"{snapshot['date']}.json"
    today.write_text(json.dumps(snapshot, indent=2, default=str))
    (snaps / "latest.json").write_text(today.read_text())  # copy, NOT symlink
    return today


def _write_demo(root: Path, snapshot: dict) -> Path:
    demos = root / "demos"
    demos.mkdir(exist_ok=True)
    html = render_mod.render_self_contained(snapshot)
    out = demos / f"{snapshot['date']}.html"
    out.write_text(html)
    (demos / "latest.html").write_text(html)
    return out


def _git(root: Path, *args: str) -> int:
    return subprocess.call(["git", "-C", str(root), *args])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--push", action="store_true")
    args = parser.parse_args(argv)

    root = Path.cwd()
    load_dotenv(root / ".env")
    watchlist = _load_watchlist(root)

    equity_syms = [w["symbol"] for w in watchlist["overview"]] + [e["symbol"] for e in watchlist["equities"]]
    crypto_ids = [c["coingecko_id"] for c in watchlist["crypto"]]

    data = fetch_mod.run(equity_symbols=list(dict.fromkeys(equity_syms)), crypto_ids=crypto_ids)
    score = score_mod.btc_bottom_score(
        etf_net_flow_musd=data["btc_signals"]["etf_net_flow_musd"],
        funding_rate=data["btc_signals"]["funding_rate"],
        fng_value=(data["crypto_fng"] or {}).get("value"),
        long_short_ratio=data["btc_signals"]["long_short_ratio"],
    )
    data["btc_score"] = score
    data["date"] = _today_iso()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    model = os.environ.get("CLAUDE_MODEL_BRIEF", "claude-sonnet-4-6")
    if api_key and api_key != "sk-ant-replace-me":
        data["commentary"] = claude_brief.compose(data, api_key=api_key, model=model)
    else:
        data["commentary"] = {
            "headline": "(set ANTHROPIC_API_KEY in .env to enable AI commentary)",
            "liquidity_tone": "", "tickers_text": "", "btc_narrative": "", "top_10": "",
            "error": "no_api_key",
        }

    snap_path = _write_snapshot(root, data)
    demo_path = _write_demo(root, data)

    if args.commit:
        _git(root, "add", "snapshots", "demos")
        _git(root, "commit", "-m", f"snapshot {data['date']}")
        if args.push:
            _git(root, "push")

    if not args.no_open:
        webbrowser.open((root / "viewer.html").as_uri())

    return 0 if not data["_errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
