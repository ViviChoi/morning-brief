#!/usr/bin/env bash
# Daily Brief — double-click on Mac to run today's snapshot.
# This script lives in launchers/; the project root is one level up.

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if [ ! -x ".venv/bin/python" ]; then
  echo ""
  echo "❌ Setup not finished yet."
  echo ""
  echo "First time? Open Terminal in this folder and run:"
  echo "  python3 -m venv .venv"
  echo "  source .venv/bin/activate"
  echo "  pip install -r requirements.txt"
  echo "  cp .env.example .env"
  echo "  # then edit .env to add ANTHROPIC_API_KEY"
  echo ""
  echo "Press any key to close..."
  read -n 1
  exit 1
fi

echo "═══════════════════════════════════════════════"
echo "  Morning Brief — Daily Snapshot"
echo "═══════════════════════════════════════════════"
echo ""
echo "Fetching today's market data..."
echo ""

.venv/bin/python morning_brief.py
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ Done! Browser should be opening with today's snapshot."
else
  echo "⚠️  Finished with warnings (some data sources may be down)."
fi
echo ""
echo "This window will close in 5 seconds, or press any key to close now..."
read -n 1 -t 5 || true
