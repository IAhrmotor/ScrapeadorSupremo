@echo off
REM Launcher for Cochesnet Scraper Application (Windows)
REM Double-click this file to run the application

echo ========================================
echo   Cochesnet Scraper Application
echo   Year-based Scraping (2007-2025)
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
python scraping\sites\cochesnet\app\main.py

REM Keep window open if error occurs
if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start
    echo Press any key to close...
    pause > nul
)
