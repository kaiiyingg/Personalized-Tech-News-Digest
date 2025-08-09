@echo off
REM Deployment script for Render (Windows)

echo Preparing deployment to Render...

REM Add all changes
git add .

REM Commit changes
git commit -m "Optimize for Render free tier: fix PyTorch compatibility, add lazy loading, reduce memory usage"

REM Push to remote repository
git push origin main

echo Changes pushed to repository. Render should start auto-deploying.
echo Check your Render dashboard for deployment status.
pause
