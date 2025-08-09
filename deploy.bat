@echo off
REM Deployment script for Render (Windows)

echo Preparing deployment to Render...

REM Add all changes
git add .

REM Get current date for commit message
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "datestamp=%YYYY%-%MM%-%DD%"

REM Commit changes with timestamp
git commit -m "App improvements and fixes - %datestamp%"

REM Push to remote repository
git push origin main

echo Changes pushed to repository. Render should start auto-deploying.
echo Check your Render dashboard for deployment status.
pause
