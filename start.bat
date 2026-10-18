@echo off
setlocal EnableExtensions
title Bitly - URL shortener
cd /d "%~dp0"

echo.
echo  ==========================================
echo    Bitly - URL shortener
echo  ==========================================
echo.

rem ---------- 1. Find Python 3.10+ ----------
rem "python" may be a fake Microsoft Store alias, so every candidate is
rem actually executed and its version is checked.
set "PY="
for %%P in ("py -3" "python" "python3") do (
    if not defined PY (
        %%~P -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1 && set "PY=%%~P"
    )
)
if not defined PY goto :no_python
echo [1/3] Python found: %PY%

rem ---------- 2. Virtual environment ----------
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys" >nul 2>&1 || (
        echo       Existing .venv is broken, recreating...
        rmdir /s /q ".venv"
    )
)
if not exist ".venv\Scripts\python.exe" (
    echo [2/3] Creating virtual environment .venv ...
    %PY% -m venv .venv
    if errorlevel 1 goto :venv_failed
) else (
    echo [2/3] Virtual environment: .venv
)

rem ---------- 3. Dependencies ----------
echo [3/3] Installing dependencies, first run may take a minute...
".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :pip_failed

rem ---------- Run ----------
echo.
if not defined OPEN_BROWSER set "OPEN_BROWSER=1"
".venv\Scripts\python.exe" run.py
echo.
echo Server stopped.
pause
exit /b 0

:no_python
echo [ERROR] Python 3.10 or newer was not found.
echo.
echo   1. Download it from https://www.python.org/downloads/
echo   2. During installation check "Add python.exe to PATH"
echo   3. Run start.bat again
echo.
pause
exit /b 1

:venv_failed
echo [ERROR] Failed to create the virtual environment.
pause
exit /b 1

:pip_failed
echo [ERROR] Failed to install dependencies. Check your internet connection.
pause
exit /b 1
