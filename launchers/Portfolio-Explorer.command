#!/usr/bin/env bash
# Portfolio Explorer — double-click on Mac to start the local WebUI.

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if [ ! -x ".venv/bin/python" ]; then
  echo ""
  echo "❌ Setup not finished yet. See Daily-Brief.command for first-time setup."
  echo ""
  echo "Press any key to close..."
  read -n 1
  exit 1
fi

echo "═══════════════════════════════════════════════"
echo "  Portfolio Explorer — Local WebUI"
echo "═══════════════════════════════════════════════"
echo ""
echo "Starting server at http://127.0.0.1:8765/"
echo "Browser will open automatically in 1 second."
echo ""
echo "To stop: press Ctrl+C below, then close this window."
echo "═══════════════════════════════════════════════"
echo ""

.venv/bin/python webui.py
