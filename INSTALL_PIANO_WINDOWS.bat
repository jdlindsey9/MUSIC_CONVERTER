@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run START_WINDOWS.bat once to install the application first, then close it.
  pause
  exit /b 1
)
echo Install piano isolation and Transkun V2. CUDA is recommended for your NVIDIA RTX 4070 Super.
choice /c GC /n /m "Press G for NVIDIA GPU or C for CPU: "
if errorlevel 2 goto cpu
.venv\Scripts\python.exe -m pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
if errorlevel 1 goto failed
goto separator
:cpu
.venv\Scripts\python.exe -m pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 goto failed
:separator
.venv\Scripts\python.exe -m pip install -r requirements-piano.txt
if errorlevel 1 goto failed
.venv\Scripts\python.exe scripts\install_transkun.py
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip check
if errorlevel 1 goto failed
echo Installed. Run START_WINDOWS.bat. The first isolation downloads model weights.
pause
exit /b 0
:failed
echo Installation failed. Review the error above.
pause
exit /b 1
