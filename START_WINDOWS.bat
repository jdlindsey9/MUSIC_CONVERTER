@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto missing
if not exist ".venv\Scripts\python.exe" py -3.11 -m venv .venv
if errorlevel 1 goto failed
if not exist ".venv\Scripts\python.exe" goto missing
.venv\Scripts\python.exe -m pip install -r requirements-windows.lock.txt
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip check
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m streamlit run app.py --server.address localhost --server.headless false --browser.gatherUsageStats false --server.fileWatcherType none
if errorlevel 1 goto failed
exit /b 0
:missing
echo Install 64-bit Python 3.11 from python.org with the py launcher, then retry.
pause
exit /b 1
:failed
echo Setup or startup failed. Review the error above. If upgrading Python, remove .venv and retry.
pause
exit /b 1
