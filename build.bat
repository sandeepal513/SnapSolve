@echo off
setlocal
cd /d "%~dp0"
echo === Building SnapSolve.exe ===
where python >nul 2>nul || (echo Python not found. Install Python 3.10-3.12 from python.org first. & pause & exit /b 1)
python -m venv .venv || (pause & exit /b 1)
call .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt || (echo Install failed. & pause & exit /b 1)
python tools\make_icon.py
python -m PyInstaller --noconfirm --clean --noconsole --onefile --icon assets\icon.ico --add-data "assets;assets" --name SnapSolve --paths . --collect-all rapidocr_onnxruntime --collect-data wordninja --collect-submodules winrt --hidden-import winrt.windows.media.ocr --hidden-import winrt.windows.graphics.imaging --hidden-import winrt.windows.storage.streams --hidden-import winrt.windows.globalization --hidden-import winrt.windows.foundation --hidden-import winrt.windows.foundation.collections app\main.py || (echo Build failed. & pause & exit /b 1)
echo.
echo Done:  %cd%\dist\SnapSolve.exe
pause
