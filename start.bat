@echo off
REM Запуск на Windows: двойной клик по start.bat
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv (
    python -m venv .venv
)
.venv\Scripts\python -m pip install -q -r requirements.txt
.venv\Scripts\python run.py
pause
