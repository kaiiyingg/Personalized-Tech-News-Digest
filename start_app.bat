@echo off
echo Starting TechPulse with optimizations...
echo.

REM Set environment variables
set FLASK_APP=src/app.py
set FLASK_ENV=development
set PYTHONPATH=src

REM Start the application
.venv\Scripts\python.exe -m flask run --host=127.0.0.1 --port=5000

pause
