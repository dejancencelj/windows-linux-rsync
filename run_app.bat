@echo off
setlocal
cd /d "%~dp0"
if errorlevel 1 goto failed

set "PYTHON=python"
python -c "import sys; sys.exit(sys.version_info.major != 3)" >nul 2>&1
if not errorlevel 1 goto python_ready
set "PYTHON=py -3"
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 goto python_ready
echo Python 3 was not found. Install Python and enable its PATH option.
goto failed

:python_ready
%PYTHON% -c "import watchdog, paramiko, pystray, PIL" >nul 2>&1
if not errorlevel 1 goto start_app
echo Installing requirements...
%PYTHON% -m pip install -r requirements.txt
if errorlevel 1 goto failed

:start_app
echo Starting Windows-Linux Sync App...
%PYTHON% main.py
if errorlevel 1 goto failed
exit /b 0

:failed
echo.
echo The app could not start. Review the error above and sync.log in:
echo %~dp0
pause
exit /b 1
