@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 -m venv .venv
    ) else (
        python -m venv .venv
    )
    if errorlevel 1 goto :error
)
.venv\Scripts\python.exe -c "import PySide6.QtMultimedia, PIL" >nul 2>nul
if errorlevel 1 (
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 goto :error
)
.venv\Scripts\python.exe app.py %*
if errorlevel 1 goto :error
exit /b 0
:error
echo GIFRipper failed to launch. Check Python, Qt and FFmpeg.
pause
exit /b 1
