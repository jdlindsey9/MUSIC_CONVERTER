@echo off
setlocal
cd /d "%~dp0"
echo Downloading the official Audiveris 5.11.0 Windows installer. Follow its installation prompts.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_audiveris.ps1"
if errorlevel 1 (
  echo Installation failed. Download the Windows installer at https://github.com/Audiveris/audiveris/releases/tag/5.11.0
  pause
  exit /b 1
)
pause
