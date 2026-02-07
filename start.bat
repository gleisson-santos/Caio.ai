@echo off
REM Launcher simples para Windows

IF EXIST .venv (
    CALL .venv\Scripts\activate.bat
)

python cli.py
pause
