@echo off
echo Starting TechPulse with user-driven content updates...
echo.

REM Set environment variables
set FLASK_APP=src/app.py
set FLASK_ENV=development
set PYTHONPATH=src

echo =========================================
echo TechPulse - User-Driven Content Updates
echo =========================================
echo.
echo Features:
echo  - Click "Refresh" in navigation to update content
echo  - Real-time article classification with AI
echo  - Optimized for free-tier hosting
echo.
echo Access your app at: http://localhost:5000
echo.

REM Start the application
.venv\Scripts\python.exe -m flask run --host=127.0.0.1 --port=5000

pause
