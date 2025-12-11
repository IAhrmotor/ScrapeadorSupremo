# PowerShell script to create desktop shortcut for Coordinated Scraper

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $ScriptDir).Parent.Parent.Parent.FullName

$WshShell = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$Shortcut = $WshShell.CreateShortcut("$Desktop\Scraper Coordinado.lnk")
$Shortcut.TargetPath = Join-Path $ProjectRoot "launch_coordinated_scraper.bat"
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.Description = "Scraper Coordinado - Multi-Scraper con Proteccion DNS"
$Shortcut.Save()

Write-Host "Acceso directo creado en el escritorio: Scraper Coordinado"
