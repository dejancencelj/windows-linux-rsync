@echo off
echo Upgrading build tools...
python -m pip install --upgrade pip setuptools wheel

echo Installing requirements...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install requirements.
    pause
    exit /b %errorlevel%
)

echo Starting Windows-Linux Sync App...
python main.py
