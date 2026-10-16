@echo off
rem Double-click to start SnapSolve (no console window, no admin rights).
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" -m app.main
) else (
    start "" pythonw -m app.main
)
