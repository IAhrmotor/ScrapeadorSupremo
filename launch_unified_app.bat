@echo off
REM Launcher for Unified Scraper Application (Windows)
REM Double-click this file to run the application

echo ========================================
echo   Unified Scraper Application
echo   Autocasion + Cochesnet Manager
echo ========================================
echo.

REM Get script directory
cd /d "%~dp0"

REM Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Run application
echo Starting application...
python scraping\unified_app\main.py

REM Keep window open if error occurs
if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start
    echo Press any key to close...
    pause > nul
)
