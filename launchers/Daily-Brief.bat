@echo off
REM Daily Brief - double-click on Windows to run today's snapshot.
REM This script lives in launchers\; the project root is one level up.

setlocal
cd /d "%~dp0\.."

if not exist ".venv\Scripts\python.exe" (
  echo.
  echo [X] Setup not finished yet.
  echo.
  echo First time? Open PowerShell in this folder and run:
  echo   python -m venv .venv
  echo   .venv\Scripts\Activate.ps1
  echo   pip install -r requirements.txt
  echo   copy .env.example .env
  echo   REM then edit .env to add ANTHROPIC_API_KEY
  echo.
  pause
  exit /b 1
)

echo ===============================================
echo   Morning Brief - Daily Snapshot
echo ===============================================
echo.
echo Fetching today's market data...
echo.

.venv\Scripts\python.exe morning_brief.py
set EXIT_CODE=%ERRORLEVEL%

echo.
if "%EXIT_CODE%"=="0" (
  echo [OK] Done! Browser should be opening with today's snapshot.
) else (
  echo [!] Finished with warnings ^(some data sources may be down^).
)
echo.
echo Press any key to close...
pause >nul
