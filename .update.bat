@echo off
echo Updating repository...
git pull

echo Installing Python requirements...
pip install -r requirements.txt

echo Update complete!
pause