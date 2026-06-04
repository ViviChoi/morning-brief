# Morning Brief — Design Spec

**Date**: 2026-06-05
**Status**: Approved for implementation (P1) — revised once during brainstorming to add Surface B
**Owner**: Jiawen / Polimi EE

---

## 1. One-liner

**Morning Brief** is a portable, single-folder market-intelligence tool that runs anywhere Python 3 + a browser exist. It has two surfaces:

- **Surface A — Daily Brief**: a fully automated daily snapshot rendered as a self-contained HTML file. Shareable as a link, opens with zero install, no server, no warnings.
- **Surface B — Portfolio Explorer**: a local interactive WebUI where the owner uploads a broker CSV (holdings or trade history), and the app visualizes the real portfolio against today's market data plus an AI-written plain-language explanation.

Both surfaces share the same backend modules. Surface A is read-only and distribution-friendly. Surface B is interactive and personal.

The visual language across both surfaces is built for a **financial novice** (the owner's own words: "I don't really read finance code"): charts dominate over tables, every number has a plain-language tooltip, color-coding is consistent (red = bearish / loss, green = bullish / gain, amber = caution).

---

## 2. Goals (P1)

1. **Surface A — Daily Brief**: Owner can view today's market snapshot on Mac, Win VM, and iPhone with **zero infrastructure** (no server process, no Tailscale dependency, no Docker, no cron daemon that has to stay healthy).
2. **Surface A — Shareable**: Anyone the owner shares a link with can open a **single HTML file** and see the same dashboard, with **zero install** and no browser security warnings.
3. **Surface B — Portfolio Explorer**: Owner can launch `python webui.py` on either Mac or Win VM, drag-drop a broker CSV (IBKR / Binance / Coinbase / generic), and within seconds see a visualized portfolio dashboard with allocation chart, P&L bars, sparklines, and a Claude-written plain-language explanation. No login. Loopback-only.
4. **Visual-first UX**: Both surfaces are built for someone who admits they "don't read finance well" — charts dominate, every number has a plain-language tooltip / caption, color semantics are global and consistent.
5. **Codebase**: small, readable, and obviously runnable — the README's quickstart fits in 60 seconds of reading.
6. **Infra compat**: works with the owner's existing infrastructure (Mac mini home server, Parallels Win 11 VM, iOS Working Copy, Anthropic API key already provisioned).

## 3. Non-goals (explicit, list in README)

- Real-time / streaming data. One snapshot per day is enough.
- Paid on-chain indicators (Glassnode LTH-MVRV / NUPL / SOPR). Deferred to P2.
- A native desktop binary (.app / .exe). Out of scope — see "Why not a desktop app" below.
- Public unauthenticated API. The repo is private during P1; if it goes public in P2, only static HTML snapshots are exposed.
- Multi-user accounts, login, persistence beyond git history.
- Fund Finance Lens tab. Placeholder section reserved in README; implementation deferred to P1.5.

## 4. Why not a desktop app

Considered Tauri / Electron / PyInstaller. Rejected because:
- Code-signing reality: unsigned .app and .exe trigger Gatekeeper / SmartScreen warnings. Recipients in regulated environments (e.g. a bank IT-managed laptop) will likely not run it at all.
- Maintenance: changing the watchlist or adding an indicator requires a rebuild + redistribute cycle.
- Distribution value: the demo signal we need is "look at my dashboard," not "install my binary." A static HTML file delivers the same visual signal with strictly less friction.

The "feels like a desktop app to the recipient" property is delivered by the static-HTML demo path, not by actually being one.

## 5. Architecture overview

```
~/Desktop/morning-brief/                  ← git repo, private GitHub initially
├── morning_brief.py                      ← Surface A entrypoint; one invocation = one snapshot
├── webui.py                              ← Surface B entrypoint; starts FastAPI + opens browser
├── lib/
│   ├── fetch.py                          ← market data adapters (yfinance, alt.me F&G, CoinGecko, farside, Binance public)
│   ├── score.py                          ← BTC 0-100 bottom-score (4 free indicators, weighted)
│   ├── claude_brief.py                   ← Claude API caller for daily commentary
│   ├── claude_portfolio.py               ← Claude API caller for portfolio plain-language explanation
│   ├── importers/                        ← broker CSV parsers, one file per broker
│   │   ├── ibkr.py
│   │   ├── binance.py
│   │   ├── coinbase.py
│   │   └── generic.py                    ← fallback: column-name autodetect (symbol/qty/cost)
│   ├── portfolio.py                      ← normalize positions, compute P&L, allocation, sector mapping
│   └── render.py                         ← snapshot → self-contained HTML; also fragments for Surface B
├── webui/
│   ├── app.py                            ← FastAPI routes: POST /upload, GET /portfolio, GET /snapshot
│   ├── static/                           ← JS, CSS, Chart.js, Plotly bundle
│   └── templates/                        ← Jinja2: index.html with upload zone + dashboard panels
├── snapshots/
│   ├── 2026-06-05.json                   ← daily snapshot (raw data + AI text), git-tracked
│   └── latest.json                       ← plain copy of today's file (NOT symlink — Win VM compatibility)
├── portfolios/                           ← uploaded CSVs land here; git-IGNORED (personal data)
├── demos/
│   └── 2026-06-05.html                   ← self-contained HTML; CSS/JS/data inlined; shareable link target
├── viewer.html                           ← live viewer; reads snapshots/latest.json from same folder
├── config/
│   └── watchlist.json                    ← editable: equity tickers + crypto tickers
├── .env.example                          ← documents ANTHROPIC_API_KEY only
├── .gitignore                            ← excludes .env, .venv, __pycache__, portfolios/
├── README.md                             ← top: demo GIF; below: 60-second quickstart, then module map
├── demo.gif                              ← 20-30s screen recording of the dashboard, looped
└── docs/superpowers/specs/2026-06-05-morning-brief-design.md  ← this file
```

### 5.1 Data flow (one run)

```
morning_brief.py  [--no-open] [--commit] [--push]
   ├─→ lib.fetch.run()              → dict of market data
   ├─→ lib.score.btc_bottom_score() → 0-100 + components breakdown
   ├─→ lib.claude_brief.compose()   → AI commentary (overview / holdings / news / btc narrative)
   ├─→ writes snapshots/2026-06-05.json   (commit candidate)
   ├─→ writes snapshots/latest.json       (copy, NOT symlink — Win VM / Parallels Shared Folder compatibility)
   ├─→ writes demos/2026-06-05.html       (self-contained, shareable)
   ├─→ if --commit: git add snapshots demos && git commit -m "snapshot YYYY-MM-DD"
   ├─→ if --push:   git push
   └─→ unless --no-open: opens viewer.html in default browser
```

CLI flags:
- `--no-open` — used by launchd / cron, suppresses browser launch
- `--commit` — stages and commits the snapshot + demo
- `--push` — pushes to remote (requires `--commit`)
- Default (no flags) — interactive: writes files and opens browser only

### 5.2 Cross-platform sync

Git itself is the sync layer.

| Platform | Run pattern |
|---|---|
| Mac mini (host, always on) | `launchd` LaunchAgent fires `python3 morning_brief.py` at 08:00 Europe/Rome daily, then `git add snapshots demos && git commit -m "snapshot YYYY-MM-DD" && git push` |
| Mac mini (interactive) | `./morning-brief` (shell wrapper) |
| Win 11 VM | `python morning_brief.py` from PowerShell or VS Code; same `.env` shared via Parallels Shared Folder |
| iPhone | Working Copy app → `git pull` → tap `viewer.html` → Safari renders (file:// is allowed on iOS for HTML) |
| Any other machine | `git clone` → `pip install -r requirements.txt` → `cp .env.example .env` → fill in key → run |

### 5.3 Surface B run model (Portfolio Explorer WebUI)

`python3 webui.py` starts a local FastAPI server bound to `127.0.0.1:8765` and opens the default browser. Listens on loopback only — never exposed externally. No login (single user, local machine).

User flow:
1. Browser opens to `http://127.0.0.1:8765/` showing an upload zone with broker-format hints.
2. User drags a CSV (IBKR Activity Statement, Binance Trade History, Coinbase Pro Account export, or any CSV with `symbol`, `qty`, `cost` columns) into the zone.
3. Backend parses via `lib/importers/`, normalizes to a uniform `Position` schema, persists to `portfolios/<filename>-parsed.json` (this folder is git-ignored).
4. Backend fetches today's prices for those tickers via `lib/fetch.py`, computes P&L and allocation via `lib/portfolio.py`.
5. UI renders four panels: donut allocation, per-ticker P&L bars, positions table with sparklines, and a plain-language AI explanation block (from `lib/claude_portfolio.py`).
6. User can swap CSVs, the dashboard re-renders without page reload (fetch returns JSON; charts redraw via Chart.js update).

Stopping the server: `Ctrl+C` in the terminal, or close the browser tab and the LaunchAgent (if used) reaps the process.

Surface B is intentionally **not** shared via the demo path — uploaded portfolios contain personal financial data. Surface A remains the only shareable surface.

### 5.4 Demo distribution (the "easy for others to try" path, Surface A only)

When the owner shares a link:
1. **GitHub repo URL** (private first, can be made public in P2). Recipient sees README → demo GIF (renders inline) → quickstart.
2. **Direct link to `demos/YYYY-MM-DD.html`** raw URL. Anyone clicking it gets a self-contained dashboard rendered in their browser — no Python, no install, no warnings, no API keys leaked (the AI output is pre-baked text in the HTML; raw API keys never touch this file).
3. **GitHub Pages (P2 toggle)**: flipping the repo to public + enabling Pages serves `demos/latest.html` at `<user>.github.io/morning-brief/`.

This is the property the owner asked for ("方便别人确认尝试程序"): friction-free viewing.

---

## 6. Modules (P1, 4 modules)

| # | Module | Data source | Cost | Claude role |
|---|---|---|---|---|
| 1 | **Overview** | yfinance: SPY/QQQ/VOO/VIX/DXY/GLD/USO/BTC-USD/ETH-USD · alternative.me Crypto Fear & Greed | free | one-sentence "liquidity tone" |
| 2 | **Holdings** | yfinance for equities (default: NVDA, TSLA, GOOG, RKLB, COIN, SMH) · CoinGecko for crypto including non-yfinance tickers (default: BTC, ETH, SOL, BNB, HYPE/Hyperliquid, TAO/Bittensor). Watchlist is owner-configurable via `config/watchlist.json` | free | one-sentence thesis per ticker |
| 3 | **AI morning brief** | Reuters Markets RSS + CoinDesk RSS + CNBC Markets RSS · upstream data from modules 1 + 2 | free | "Top 10 things to know today" + 1 actionable hint each |
| 4 | **BTC bottom score (0-100)** | farside.co.uk BTC ETF net flow (HTML scrape, daily) · Binance public futures `fundingRate` · alternative.me Crypto F&G · Binance `globalLongShortAccountRatio` | free | invokes `~/.claude/skills/btc-bottom-model` skill prompt with the data; outputs narrative + buy/wait/sell flag |

### 6.1 BTC bottom score weighting (P1)

Only the 4 daily-pulse indicators from the Day1Global skill are scored (sum = 32 pts in their schema; we rescale to 0-100):

| Indicator | Weight | Source |
|---|---|---|
| ETF daily net flow | 38% | farside.co.uk daily table |
| Funding rate (BTC perp avg) | 25% | Binance `/fapi/v1/premiumIndex` |
| Fear & Greed Index | 22% | alternative.me |
| Long/Short ratio | 15% | Binance `/futures/data/globalLongShortAccountRatio` |

Total → 0-100; ratings copied from Day1Global:
- 0-15 Extreme Fear (buy)
- 16-45 Fear
- 46-55 Neutral
- 56-85 Greed
- 86-100 Extreme Greed (sell)

README explicitly notes weekly on-chain indicators (LTH-MVRV / NUPL / SOPR / 200WMA / RSI / volume change — 68 pts in the original) are P2 deferred because they require Glassnode paid tier.

---

## 7. Module boundaries (one-purpose units)

Each `lib/*.py` file does one thing, has one exported entry point, and can be unit-tested by feeding it a fixture:

- `lib/fetch.py` — pure I/O. Input: nothing or a list of tickers. Output: dict of raw market data. No Claude calls. No scoring.
- `lib/score.py` — pure function. Input: the dict from `fetch.py`. Output: BTC bottom score components and total. No I/O.
- `lib/claude_brief.py` — Claude wrapper for the daily brief. Input: dict from `fetch.py` + `score.py`. Output: a `commentary` dict of strings.
- `lib/claude_portfolio.py` — Claude wrapper for portfolio explanation. Input: normalized `Position[]` + market snapshot. Output: a `portfolio_commentary` dict (concentration risk, sector exposure, plain-language summary).
- `lib/importers/<broker>.py` — pure parsers. Input: CSV bytes / file path. Output: list of `RawTrade` dicts. Per-broker module. Each handles only one CSV format. `generic.py` is the column-name fallback.
- `lib/portfolio.py` — pure functions. Input: list of `RawTrade`. Output: list of `Position` (symbol, qty, avg_cost, current_value, pnl_abs, pnl_pct), plus allocation breakdown and sector mapping. No I/O.
- `lib/render.py` — template engine. Input: a snapshot dict. Output: HTML strings (live `viewer.html` and self-contained `demos/YYYY-MM-DD.html`). No I/O beyond writing files.
- `webui/app.py` — FastAPI app. Glue only: receives upload, calls `importers + portfolio + fetch + claude_portfolio`, returns JSON. No business logic.
- `morning_brief.py` — Surface A orchestrator. Calls fetch + score + claude_brief + render in sequence. Handles errors, writes JSON, commits, opens browser.
- `webui.py` — Surface B orchestrator. Starts `uvicorn webui.app:app --host 127.0.0.1 --port 8765` and opens browser. Nothing else.

This means: someone reading any single file understands what it does without reading the others. Changing the BTC scoring formula doesn't touch fetch, render, or the WebUI.

---

## 8. Error handling

Each external data source can fail independently (rate limit, network, site change). The design assumption is that **a partial snapshot is better than no snapshot** — if Binance funding rate fails, the BTC score should still compute with 3 of 4 components and mark the missing one as `null` with a note.

- `lib/fetch.py` catches per-source exceptions, logs them, returns the partial dict plus a `_errors: [...]` list.
- `lib/score.py` gracefully degrades: if any of the 4 BTC indicators is `null`, it computes a normalized score over the available ones and flags `partial: true`.
- `lib/claude_brief.py` retries Anthropic 429/500 with exponential backoff (3 attempts). If still failing, writes a placeholder `"AI commentary unavailable for today — see raw data above"` instead of crashing.
- `morning_brief.py` always writes a snapshot, even if degraded. Exit code is 0 on full success, 1 if any module logged errors. Cron / launchd can read exit code to alert later.

No mocked data on failure — if a value is missing, the dashboard shows it as missing, not fake.

---

## 9. Testing

- Each `lib/*.py` file has a `tests/test_<name>.py` with at least 2 cases: happy path with a captured-real-response fixture, and a degraded path where one input is `None`.
- `morning_brief.py` has one integration test that runs against pre-recorded fixtures (no real API calls in CI), asserts that a snapshot JSON is produced with the expected schema.
- No coverage target chased for its own sake; the goal is "every public function has at least one test that exercises it."

---

## 10. Schedule (Mac mini launchd)

`~/Library/LaunchAgents/com.jiawen.morning-brief.plist` runs `python3 ~/Desktop/morning-brief/morning_brief.py --commit --push --no-open` daily at 08:00 Europe/Rome.

Any other machine can run the script manually at any time — the same snapshot for a given calendar day is idempotent (re-running overwrites today's snapshot, last commit wins).

A second LaunchAgent (P2) optionally re-runs at 22:00 IT to capture the US close. P1 ships with the single morning run only.

---

## 11. Repository plan

- Local: `~/Desktop/morning-brief/` (this folder).
- Remote: a private GitHub repo on the owner's TBD account (the owner will log in and create it during implementation). After creation: `git remote add origin <url>` and push.
- Initial commits during the brainstorming phase (this spec + folder skeleton) live in a local-only history until the remote is set up.

---

## 11.5 Visual / UX requirements (apply to both surfaces)

The owner is a financial novice (own words: "I don't really read finance code"). Both Surface A and Surface B must privilege visual understanding over numeric density.

**Universal rules:**

- **Charts > tables**, always. Tables exist as a secondary "details" view, never primary.
- **Color semantics are global and consistent**: green = bullish / gain / safe, red = bearish / loss / risk, amber = caution / mixed, blue/gray = neutral / informational. No other meanings.
- **Every number that is not raw price has a plain-language tooltip on hover** (Surface A) or persistent caption underneath (Surface B). Example tooltip for "VIX 27.3": *"Wall Street's fear gauge. Above 25 = market expects unusually large daily swings."*
- **"Today in one sentence" headline** at the very top of both surfaces — a single Claude-generated sentence summarizing the day, font-size huge, no jargon.
- **Glossary expander** at the bottom of every page, collapsed by default, listing every term used.

**Surface A specific:**

- BTC bottom score rendered as a horizontal **thermometer gauge** with a rainbow gradient (deep red 0 → green 50 → deep red 100, since both extremes are dangerous), the current score marked with an arrow. Below the gauge: the rating label (e.g. "Extreme Fear — historically a strong buy zone").
- Overview tickers rendered as a grid of colored cards, not a table. Each card: ticker symbol (big), price, daily % change with arrow and color, sparkline of last 30 days.
- AI brief items rendered as a stacked list of "what / why it matters" pairs, not a numbered bullet wall.

**Surface B specific:**

- Portfolio allocation as a **donut chart** (Chart.js doughnut) with hover-to-isolate behavior — hovering a wedge dims the others and shows that holding's full detail in a side panel.
- Per-ticker P&L as **horizontal diverging bars** (negative left in red, positive right in green), sorted by absolute P&L magnitude descending.
- Positions table as a "detail drawer" that slides out from the right when the user clicks a wedge or a bar.
- Each row in the positions table includes a small **30-day sparkline** (Chart.js mini line chart) so the owner can see the price trajectory next to the number, without having to click into a separate chart.
- AI portfolio explanation rendered as a panel with three sub-blocks: *"What you hold"* (one-sentence summary), *"What's working / not working"* (two short lists), *"What to watch"* (1-2 sentences). No jargon allowed in this panel — if a term is unavoidable, it is followed by a parenthetical definition.

## 12. P2 backlog (named, not committed)

- **Fund Finance Lens** module — ETF flows for sector concentration tracking (XLK / SMH / XLE / KRE), positioned as the bridge to UniCredit application narrative. Placeholder section in README.
- **On-chain indicators** — Glassnode paid tier integration (LTH-MVRV / NUPL / SOPR / 200WMA / RSI / volume). Lifts BTC bottom score to the full 13-indicator Day1Global weighting.
- **Custom watchlist CSV/JSON upload** in WebUI (deferred from P1 design discussion).
- **PDF / DOCX document parsing** — upload an earnings report / 10-K, Claude extracts plain-language key findings + valuation cues (deferred from P1 design discussion).
- **GitHub Pages public deploy** — flip repo public, enable Pages serving `demos/`.
- **Evening run** — 22:00 IT for US close summary.
- **Mobile-tuned layout** — viewer.html responsive for iPhone Safari.
- **Telegram / Mac notification on extreme readings** — push when BTC score < 20 or > 80, when VIX > 30, when a watchlist ticker moves > 5%.
- **Portfolio Explorer PDF export** — generate a self-contained PDF of the user's portfolio dashboard for offline sharing (one-off, no live data).

---

## 13. Open items for implementation phase

These are not design questions, but they are choices the implementer (i.e. the next conversation) should confirm with the owner before writing code:

1. Final watchlist tickers (default proposed above; owner may want to add / remove).
2. Anthropic model choice (`claude-haiku-4-5-20251001` for cost, vs `claude-sonnet-4-6` for commentary quality). Default proposal: Haiku for per-ticker thesis, Sonnet for the morning brief synthesis.
3. README tone — Chinese first, English first, or bilingual blocks? Owner is bilingual; recipient pool is mixed (Italian HR, English-speaking team, Chinese personal).
4. Demo GIF tooling — `Cmd+Shift+5` → `ffmpeg`, or use `gifski` for higher quality. Decide at GIF-recording step.

---

## 14. Acceptance criteria for P1 "done"

P1 is considered shipped when **all** of the following hold:

**Surface A — Daily Brief:**
- Running `python3 morning_brief.py` on a fresh clone (after `pip install -r requirements.txt` and `.env` setup) produces a snapshot JSON, a self-contained HTML demo, and opens the live viewer — in under 60 seconds.
- The owner can open `viewer.html` on Mac, Win VM, and iPhone Safari, and see today's data correctly rendered with all visual rules from §11.5 applied (thermometer gauge, colored ticker cards, plain-language tooltips, etc.).
- Sharing the raw URL of a `demos/YYYY-MM-DD.html` file to a third-party browser (incognito, no clone) renders the dashboard with no missing assets, no broken charts, no exposed API keys.
- The Mac mini launchd job has been verified to fire once and produce a committed snapshot.

**Surface B — Portfolio Explorer:**
- Running `python3 webui.py` starts the FastAPI server, opens the browser to the upload page, and the page renders in under 3 seconds.
- Dragging a sample IBKR Activity Statement CSV, a sample Binance Trade History CSV, and a sample Coinbase Account CSV each produces a correctly-rendered dashboard (positions, allocation donut, P&L bars, sparklines, AI explanation).
- A generic CSV with `symbol`, `qty`, `cost` columns (any header casing) is accepted by the fallback importer.
- Uploaded portfolios are stored in `portfolios/` and that folder is correctly git-ignored (verified by `git status` after an upload).
- The plain-language AI explanation panel contains zero financial jargon that isn't immediately defined in-line.

**General:**
- README's quickstart can be followed in under 60 seconds by someone who already has Python 3 + git.
- A 20-30 second demo GIF / MP4 is embedded in the README and plays inline on GitHub. Demo shows BOTH surfaces.
- All visual rules from §11.5 are applied across both surfaces and verified by manual inspection.
