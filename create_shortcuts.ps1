# PowerShell script to create desktop shortcuts
# Run: powershell -ExecutionPolicy Bypass -File create_shortcuts.ps1

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Desktop = [Environment]::GetFolderPath('Desktop')
$WshShell = New-Object -ComObject WScript.Shell

Write-Host "========================================"
Write-Host "  Creating Desktop Shortcuts"
Write-Host "========================================"
Write-Host ""
Write-Host "Project: $ProjectDir"
Write-Host "Desktop: $Desktop"
Write-Host ""

# 1. Unified Scraper
Write-Host "Creating: Unified Scraper.lnk ..."
$Shortcut = $WshShell.CreateShortcut("$Desktop\Unified Scraper.lnk")
$Shortcut.TargetPath = "$ProjectDir\launch_unified_app.bat"
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.Description = "Unified Scraper - Autocasion + Cochesnet"
$Shortcut.IconLocation = "C:\Windows\System32\SHELL32.dll,165"
$Shortcut.Save()
Write-Host "[OK] Unified Scraper.lnk" -ForegroundColor Green

# 2. Cochesnet Scraper
Write-Host "Creating: Cochesnet Scraper.lnk ..."
$Shortcut = $WshShell.CreateShortcut("$Desktop\Cochesnet Scraper.lnk")
$Shortcut.TargetPath = "$ProjectDir\launch_cochesnet_app.bat"
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.Description = "Cochesnet Scraper - Year Selection"
$Shortcut.IconLocation = "C:\Windows\System32\SHELL32.dll,43"
$Shortcut.Save()
Write-Host "[OK] Cochesnet Scraper.lnk" -ForegroundColor Green

# 3. Autocasion Scraper
Write-Host "Creating: Autocasion Scraper.lnk ..."
$Shortcut = $WshShell.CreateShortcut("$Desktop\Autocasion Scraper.lnk")
$Shortcut.TargetPath = "$ProjectDir\launch_autocasion_app.bat"
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.Description = "Autocasion Scraper - Brand Selection"
$Shortcut.IconLocation = "C:\Windows\System32\SHELL32.dll,44"
$Shortcut.Save()
Write-Host "[OK] Autocasion Scraper.lnk" -ForegroundColor Green

Write-Host ""
Write-Host "========================================"
Write-Host "  Shortcuts Created Successfully!"
Write-Host "========================================"
Write-Host ""
Write-Host "Check your desktop for these shortcuts:"
Write-Host "  - Unified Scraper.lnk"
Write-Host "  - Cochesnet Scraper.lnk"
Write-Host "  - Autocasion Scraper.lnk"
Write-Host ""
Write-Host "Double-click any shortcut to launch the application."
Write-Host ""
Read-Host "Press Enter to close"
