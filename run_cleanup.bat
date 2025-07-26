@echo off
REM TechPulse Daily Cleanup Service
REM This batch file runs the daily article cleanup scheduler
REM Place this file in Windows Task Scheduler to run automatically

echo ========================================
echo TechPulse Daily Article Cleanup
echo ========================================
echo Starting cleanup scheduler...
echo.

cd /d "c:\Users\user-pc\Downloads\Personal Projects\Personalized-Tech-News-Digest"

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Run the cleanup scheduler
echo Running article cleanup...
python src\scheduler.py

echo.
echo Cleanup completed!
pause
