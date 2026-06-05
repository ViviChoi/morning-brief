#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PYTHON="$REPO_ROOT/.venv/bin/python"
TARGET="$HOME/Library/LaunchAgents/com.jiawen.morning-brief.plist"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "Error: venv python not found at $VENV_PYTHON"
  echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

mkdir -p "$(dirname "$TARGET")"
sed -e "s|__VENV_PYTHON__|$VENV_PYTHON|g" \
    -e "s|__REPO_ROOT__|$REPO_ROOT|g" \
    "$REPO_ROOT/scripts/com.jiawen.morning-brief.plist" > "$TARGET"

launchctl unload "$TARGET" 2>/dev/null || true
launchctl load "$TARGET"

echo "Installed LaunchAgent at $TARGET"
echo "Will fire daily at 08:00 local time."
echo "Logs: $REPO_ROOT/.launchd.{out,err}.log"
echo ""
echo "To run once now (verify):"
echo "  launchctl start com.jiawen.morning-brief"
echo ""
echo "To remove:"
echo "  launchctl unload $TARGET && rm $TARGET"
