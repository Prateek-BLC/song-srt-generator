@echo off
REM Start the Song SRT Generator. Run install.bat once first.
cd /d "%~dp0"
set GRADIO_ANALYTICS_ENABLED=False
call .venv\Scripts\activate.bat
python app.py
pause
