@echo off
REM Song SRT Generator — one-time installer for Windows.
REM NOTE: written defensively but UNTESTED until Windows hardware is available (see DECISIONS.md).
setlocal
cd /d "%~dp0"

echo === Song SRT Generator installer (Windows) ===

REM 1. Find Python 3.10 or 3.11
set PY=
py -3.11 --version >nul 2>&1 && set PY=py -3.11
if not defined PY py -3.10 --version >nul 2>&1 && set PY=py -3.10
if not defined PY (
  echo.
  echo Python 3.10 or 3.11 is required and wasn't found.
  echo Install it from https://www.python.org/downloads/ ^(choose 3.11, tick "Add to PATH"^), then run this again.
  pause
  exit /b 1
)
echo OK  Python found

REM 2. ffmpeg
where ffmpeg >nul 2>&1
if errorlevel 1 (
  echo Installing ffmpeg with winget...
  winget install --accept-source-agreements --accept-package-agreements Gyan.FFmpeg
  if errorlevel 1 (
    echo.
    echo Couldn't install ffmpeg automatically. Without admin rights:
    echo   1. Download the "essentials" zip from https://www.gyan.dev/ffmpeg/builds/
    echo   2. Unzip it to a folder like C:\Users\%USERNAME%\ffmpeg
    echo   3. Add that folder's bin subfolder to your PATH:
    echo      Settings ^> System ^> About ^> Advanced system settings ^> Environment Variables
    echo      ^> select Path under User variables ^> Edit ^> New ^> paste the bin folder path
    echo   4. Open a NEW terminal and run this installer again.
    pause
    exit /b 1
  )
  echo NOTE: if the next step can't find ffmpeg, close this window and run the installer again
  echo       in a fresh terminal so PATH updates take effect.
)

REM 3. Virtual environment + dependencies (CPU torch wheel explicitly, per setup guide)
if not exist .venv (
  %PY% -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
echo Installing dependencies (CPU engine for Windows)...
pip install torch --index-url https://download.pytorch.org/whl/cpu -q
pip install stable-ts faster-whisper fastapi "uvicorn[standard]" python-multipart "audio-separator[cpu]" -q

REM Tell the app to use the cross-platform engine
python -c "import re,pathlib; p=pathlib.Path('config.py'); p.write_text(re.sub(r'^SEPARATOR_ENGINE = .*', 'SEPARATOR_ENGINE = \"cpu\"', p.read_text(), flags=re.M))"

REM 4. Download models and verify end to end
echo.
echo Downloading models and verifying (first time only, needs internet)...
set GRADIO_ANALYTICS_ENABLED=False
python warmup.py
if errorlevel 1 (
  echo.
  echo Setup did not finish. Read the message above, fix it, and run this installer again.
  pause
  exit /b 1
)

echo.
echo === Install complete. Start the app anytime with start.bat ===
pause
