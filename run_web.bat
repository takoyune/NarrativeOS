@echo off
chcp 65001 >nul
title NarrativeOS EPUB Toolkit

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   NarrativeOS — EPUB Toolkit Server     ║
echo  ╚══════════════════════════════════════════╝
echo.
echo  Starting server at http://localhost:8765
echo  Press Ctrl+C to stop.
echo.

:: Change to the directory where this .bat lives
cd /d "%~dp0"

:: Use the virtual environment if it exists
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8765 --reload
) else (
    python -m uvicorn server:app --host 127.0.0.1 --port 8765 --reload
)

pause
