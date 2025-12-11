@echo off
title Scraper Coordinado - Multi-Scraper con Proteccion DNS
cd /d "%~dp0"
echo ============================================
echo   Scraper Coordinado
echo   Multi-Scraper con Proteccion DNS
echo ============================================
echo.
echo Iniciando aplicacion de escritorio...
echo.
python -m scraping.coordinated.app.gui
pause
