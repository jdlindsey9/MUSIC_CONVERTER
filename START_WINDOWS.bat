@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Please install Python 3.10 from python.org first.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" py -3.10 -m venv .venv
if not exist ".venv\Scripts\python.exe" (
 echo Python 3.10 is required for best compatibility. Install Python 3.10 and retry.
 pause
 exit /b 1
)
call .venv\Scripts\python.exe -m pip install --upgrade pip
call .venv\Scripts\python.exe -m pip install -r requirements.txt
call .venv\Scripts\python.exe -m streamlit run app.py
pause
