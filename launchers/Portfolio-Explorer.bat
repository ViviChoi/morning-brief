@echo off
REM Portfolio Explorer - double-click on Windows to start the local WebUI.

setlocal
cd /d "%~dp0\.."

if not exist ".venv\Scripts\python.exe" (
  echo.
  echo [X] Setup not finished yet. See Daily-Brief.bat for first-time setup.
  echo.
  pause
  exit /b 1
)

echo ===============================================
echo   Portfolio Explorer - Local WebUI
echo ===============================================
echo.
echo Starting server at http://127.0.0.1:8765/
echo Browser will open automatically in 1 second.
echo.
echo To stop: press Ctrl+C below, then close this window.
echo ===============================================
echo.

.venv\Scripts\python.exe webui.py
