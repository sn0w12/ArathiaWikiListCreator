@echo off
echo Installing required packages...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install requirements
    pause
    exit /b 1
) else (
    echo Requirements installed successfully
    pause
)