@echo off
REM Create desktop shortcuts for scraper applications
REM Run this script ONCE to create shortcuts on your desktop

echo ========================================
echo   Creating Desktop Shortcuts
echo ========================================
echo.

REM Get current directory (project root)
set PROJECT_DIR=%~dp0
set PROJECT_DIR=%PROJECT_DIR:~0,-1%

REM Get desktop path
set DESKTOP=%USERPROFILE%\Desktop

echo Project directory: %PROJECT_DIR%
echo Desktop directory: %DESKTOP%
echo.

REM Create VBScript to generate shortcuts (Windows doesn't have native shortcut command)
echo Creating shortcut generator script...

REM 1. Unified App Shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%DESKTOP%\Unified Scraper.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%PROJECT_DIR%\launch_unified_app.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%PROJECT_DIR%" >> CreateShortcut.vbs
echo oLink.Description = "Unified Scraper - Autocasion + Cochesnet" >> CreateShortcut.vbs
echo oLink.IconLocation = "C:\Windows\System32\SHELL32.dll,165" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

cscript //nologo CreateShortcut.vbs
echo [OK] Created: Unified Scraper.lnk

REM 2. Cochesnet App Shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%DESKTOP%\Cochesnet Scraper.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%PROJECT_DIR%\launch_cochesnet_app.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%PROJECT_DIR%" >> CreateShortcut.vbs
echo oLink.Description = "Cochesnet Scraper - Year Selection" >> CreateShortcut.vbs
echo oLink.IconLocation = "C:\Windows\System32\SHELL32.dll,43" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

cscript //nologo CreateShortcut.vbs
echo [OK] Created: Cochesnet Scraper.lnk

REM 3. Autocasion App Shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%DESKTOP%\Autocasion Scraper.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%PROJECT_DIR%\launch_autocasion_app.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%PROJECT_DIR%" >> CreateShortcut.vbs
echo oLink.Description = "Autocasion Scraper - Brand Selection" >> CreateShortcut.vbs
echo oLink.IconLocation = "C:\Windows\System32\SHELL32.dll,44" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

cscript //nologo CreateShortcut.vbs
echo [OK] Created: Autocasion Scraper.lnk

REM Cleanup
del CreateShortcut.vbs

echo.
echo ========================================
echo   Shortcuts Created Successfully!
echo ========================================
echo.
echo You can now find these shortcuts on your desktop:
echo   - Unified Scraper.lnk
echo   - Cochesnet Scraper.lnk
echo   - Autocasion Scraper.lnk
echo.
echo Double-click any shortcut to launch the application.
echo.
pause
