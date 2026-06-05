"""Surface B launcher. Starts uvicorn + opens browser."""
from __future__ import annotations

import os
import threading
import time
import webbrowser

import uvicorn
from dotenv import load_dotenv

from webui.app import app


def _open_browser():
    time.sleep(1.0)
    webbrowser.open("http://127.0.0.1:8765/")


def main() -> None:
    load_dotenv()
    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
