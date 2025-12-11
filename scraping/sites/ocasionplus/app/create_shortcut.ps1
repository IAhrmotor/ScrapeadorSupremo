# PowerShell script to create desktop shortcut for OcasionPlus Scraper

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $ScriptDir).Parent.Parent.Parent.Parent.FullName
$GuiPath = Join-Path $ScriptDir "gui.py"

$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = "$DesktopPath\OcasionPlus Scraper.lnk"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "pythonw.exe"
$Shortcut.Arguments = "`"$GuiPath`""
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.Description = "OcasionPlus Car Scraper with HeadlessX"
$Shortcut.Save()

Write-Host "Shortcut created at: $ShortcutPath"
