@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python run.py --input-pdf "%~1"
pause
