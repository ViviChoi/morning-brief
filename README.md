# Morning Brief

**🌐 Live: [vivichoi.github.io/morning-brief/](https://vivichoi.github.io/morning-brief/)** — today's snapshot, auto-updated every morning by GitHub Actions. No setup, no install, just open the URL.

A portable, single-folder market-intelligence tool. Two surfaces:

- **Daily Brief** — automated daily snapshot of US equities + crypto + AI-written commentary, rendered as a self-contained HTML file. Auto-deployed to GitHub Pages.
- **Portfolio Explorer** — local web UI: drop a broker CSV (IBKR / Binance / Coinbase / generic), get a visualized portfolio dashboard with plain-language explanation. Runs on `127.0.0.1` only because uploading broker statements to a public server is a privacy bad idea.

Both are built for non-traders: charts dominate, every term is defined, color is consistent (green = up, red = down).

![demo](demo.gif)

## 60-second quickstart

```bash
git clone <this-repo>
cd morning-brief
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your ANTHROPIC_API_KEY
python morning_brief.py        # → opens viewer.html with today's snapshot
python webui.py                 # → opens http://127.0.0.1:8765 for portfolio CSV upload
```

## Daily Brief

`python morning_brief.py [--no-open] [--commit] [--push]`

- Fetches 9 overview tickers + crypto F&G + BTC ETF flow + funding rate + long/short ratio
- Computes a 0–100 **BTC bottom score** from 4 free daily indicators (full Day1Global 13-indicator model deferred — paid on-chain metrics live in P2)
- Calls Claude to produce a plain-language headline, liquidity tone, per-ticker thesis, BTC narrative, and "today's top 10"
- Writes `snapshots/YYYY-MM-DD.json` (raw data + AI text) and `demos/YYYY-MM-DD.html` (self-contained, no external data fetches, shareable)
- `--commit --push` flags suitable for a Mac mini launchd job

## Portfolio Explorer

`python webui.py` → opens `http://127.0.0.1:8765/` in your browser. Drop a CSV:

| Broker | Format expected |
|---|---|
| Interactive Brokers | Activity Statement CSV |
| Binance | Trade History CSV |
| Coinbase / Coinbase Pro | Account export CSV |
| Generic | Any CSV with columns named `symbol`, `quantity`, `cost` (any reasonable variant) |

You see: allocation donut, P&L by position, plain-language explanation panel.

The server binds to `127.0.0.1` only. Uploaded portfolios stay in `portfolios/` and are git-ignored.

## Cross-platform

| Platform | Run |
|---|---|
| macOS | `python3 morning_brief.py` or `python3 webui.py` — or double-click `launchers/*.command` |
| Windows 11 | same (Python 3 from python.org or store) — or double-click `launchers/*.bat` |
| iPhone | open [the live URL](https://vivichoi.github.io/morning-brief/) in Safari (no app needed) |

## Deployment

**Primary path — GitHub Actions + GitHub Pages (already live)**

The repo includes `.github/workflows/daily-snapshot.yml` that:
- Fires every day at 06:00 UTC (≈ 08:00 Europe/Rome)
- Runs `morning_brief.py` in a fresh Ubuntu runner
- Publishes the resulting HTML snapshot to [vivichoi.github.io/morning-brief/](https://vivichoi.github.io/morning-brief/) via the official Pages pipeline

No Mac mini, no home server, no Tailscale required. The cron lives on GitHub's infrastructure.

To enable the AI commentary on the deployed dashboard, set the secret once:
```bash
gh secret set ANTHROPIC_API_KEY -R <your-fork>/morning-brief
```
Without the secret, the snapshot still publishes but the commentary fields show a placeholder.

**Alternative — self-host on a Mac mini (optional)**

If you'd rather run the snapshot locally and skip GitHub Actions entirely, there's a LaunchAgent installer:

```bash
./scripts/install_launchd.sh
```

This is the original deployment path and is preserved for offline / self-host scenarios. It's mutually exclusive with the GitHub Actions path — pick one.

## Data sources

| Source | Used for | Cost |
|---|---|---|
| yfinance | equity prices, VIX, DXY, gold, oil | free |
| CoinGecko | crypto spot prices | free |
| alternative.me | Crypto Fear & Greed Index | free |
| farside.co.uk | BTC spot ETF net flows | free |
| Binance public futures | funding rate, long/short ratio | free |
| Anthropic Claude | written commentary | API key, ~$0.05/day |

## Security notes

- **Subresource Integrity (SRI)** on all CDN assets (Pico CSS, Chart.js). CDN compromise can't inject scripts.
- **XSS-safe DOM rendering** for the WebUI — uploaded CSV data and Claude output are rendered via `textContent` / DOM APIs, never `innerHTML`.
- **Loopback-only** Portfolio Explorer: FastAPI binds to `127.0.0.1:8765`, no external network exposure.
- **Personal-use risk acceptance:** the venv currently carries 3 low-severity advisories (pytest local-tmp DoS, Starlette Host-header URL reconstruction) that are not exploitable in single-user loopback deployment but should be patched if this is ever exposed to other users or networks. See backlog item below.

## Project layout

```
morning_brief.py    Daily Brief entrypoint (Surface A)
webui.py            Portfolio Explorer entrypoint (Surface B)
lib/                shared backend: fetch, score, claude_brief, claude_portfolio, portfolio, importers/, symbols
templates/          Daily Brief Jinja template
webui/              FastAPI app + Portfolio Explorer template
launchers/          double-click launchers — .command (Mac) + .bat (Win)
scripts/            self-host LaunchAgent installer (optional, alternative to GitHub Actions)
.github/workflows/  GitHub Actions daily cron + Pages deploy (primary deploy path)
docs/               GitHub Pages assets (about.html etc.)
tests/              pytest suite (40 tests, all mocked, no live API calls)
snapshots/          generated daily JSON (git-ignored)
demos/              generated daily self-contained HTML (git-ignored)
portfolios/         uploaded CSVs (git-ignored)
config/watchlist.json   editable list of equity + crypto tickers
```

## Roadmap (P2)

- Glassnode paid on-chain indicators → full 13-indicator BTC bottom score
- Fund Finance Lens — sector ETF flows + concentration tracking
- Custom watchlist CSV/JSON upload in WebUI
- PDF / DOCX document parsing — upload an earnings report, Claude extracts plain-language key findings
- ~~GitHub Pages public deploy serving `demos/`~~ ✅ shipped (see *Deployment* above)
- Evening run at 22:00 IT (US close summary)
- Mobile-tuned layout
- Telegram / Mac notification on extreme readings
- Portfolio Explorer PDF export
- Patch 3 remaining advisories (Starlette Host-header URL reconstruction + pytest tmp predictability) — required before any non-loopback deployment
