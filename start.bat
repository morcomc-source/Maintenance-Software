@echo off
echo ================================================
echo     Maintenance Software - Starting...
echo ================================================

cd /d "%~dp0"

echo.
echo Starting Flask app...
echo Running: python run.py
echo.

python run.py

pause