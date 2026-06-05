"""HTML rendering for both surfaces.

- `render_self_contained(snapshot) -> str` returns a single HTML string with the
  snapshot data inlined as JSON. No runtime fetches.
- `render_live_viewer(path)` writes a viewer file that fetches
  `snapshots/latest.json` at open time.
"""
from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


_TEMPLATES = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(_TEMPLATES),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_self_contained(snapshot: dict) -> str:
    return _env.get_template("dashboard.html").render(**snapshot)


_VIEWER = """<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><title>Morning Brief (live)</title>
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/@picocss/pico@2.1.1/css/pico.min.css"
      integrity="sha384-L1dWfspMTHU/ApYnFiMz2QID/PlP1xCW9visvBdbEkOLkSSWsP6ZJWhPw6apiXxU"
      crossorigin="anonymous">
</head><body>
<main class="container">
  <h1>Loading latest snapshot...</h1>
  <div id="content"></div>
</main>
<script>
fetch('snapshots/latest.json').then(r => r.json()).then(s => {
  document.title = 'Morning Brief — ' + s.date;
  document.querySelector('h1').textContent = s.commentary?.headline || s.date;
  const c = document.getElementById('content');
  c.innerHTML = '<p>' + (s.commentary?.liquidity_tone || '') + '</p>'
    + '<h2>BTC Score: ' + (s.btc_score?.total ?? '-') + ' (' + (s.btc_score?.rating ?? '-') + ')</h2>'
    + '<pre>' + JSON.stringify(s.equity, null, 2) + '</pre>';
}).catch(e => {
  document.querySelector('h1').textContent = 'No snapshot found. Run morning_brief.py first.';
});
</script>
</body></html>
"""


def render_live_viewer(path: Path) -> None:
    Path(path).write_text(_VIEWER)
