param(
    [string]$ShortcutName = '🐎 KeibaBook Start',
    [string]$IconPath = 'C:\GeminiCLI\TEST\keibabook\assets\horse.ico'
)

$desktop = [Environment]::GetFolderPath('Desktop')
$scPath = Join-Path $desktop "$ShortcutName.lnk"
if (-not (Test-Path $scPath)) {
    Write-Host "Shortcut not found: $scPath"
    exit 1
}

$shell = New-Object -ComObject WScript.Shell
$sc = $shell.CreateShortcut($scPath)

# Set a valid target so Windows shows the icon; use powershell.exe to invoke start script
$powershellPath = (Get-Command powershell.exe).Source
$sc.TargetPath = $powershellPath
$sc.Arguments = "-NoExit -ExecutionPolicy Bypass -File 'C:\\GeminiCLI\\TEST\\keibabook\\scripts\\start_dev.ps1'"
$sc.WorkingDirectory = 'C:\GeminiCLI\TEST\keibabook\scripts'

if (Test-Path $IconPath) { $sc.IconLocation = (Resolve-Path $IconPath).Path }
$sc.Save()
Write-Host "Updated shortcut: $scPath, IconLocation: $($sc.IconLocation)"
