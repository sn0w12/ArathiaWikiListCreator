REM filepath: /C:/Users/lucas/Documents/GitHub/ArathiaWikiListCreator/.run.bat
@echo off

REM Check if there are any changes to pull
git remote update
git status -uno | findstr "behind" > nul

REM If changes exist, run update
if not errorlevel 1 (
    echo Updates available, running update...
    call .update.bat
)

REM Run main program
python src/main.py
pause