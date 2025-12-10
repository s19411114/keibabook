param(
    [string]$ShortcutName = "🐎 KeibaBook Start",
    [string]$IconPath
)

if (-not (Test-Path $IconPath)) {
    Write-Error "Icon file not found: $IconPath"
    exit 1
}

$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop ("$ShortcutName.lnk")
if (-not (Test-Path $shortcutPath)) {
    Write-Error "Shortcut not found: $shortcutPath"
    exit 1
}

$shell = New-Object -ComObject WScript.Shell
$sc = $shell.CreateShortcut($shortcutPath)
$sc.IconLocation = (Resolve-Path $IconPath).Path
$sc.Save()
Write-Host "Set icon for $shortcutPath to $IconPath"
