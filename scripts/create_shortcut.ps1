param(
    [string]$Name = "KeibaBook Start",
    [string]$Target = "$PSScriptRoot\start_dev.cmd"
)

# Creates a desktop shortcut to start_dev.cmd in this repo's scripts directory.
# Usage: Right-click and Run with PowerShell, or run from terminal.

try {
    $desktop = [Environment]::GetFolderPath('Desktop')
    $shortcutPath = Join-Path $desktop ("$Name.lnk")
    $shell = New-Object -ComObject WScript.Shell
    $sc = $shell.CreateShortcut($shortcutPath)
    $sc.TargetPath = $Target
    $sc.WorkingDirectory = Split-Path $Target
    $sc.WindowStyle = 1
    $sc.Description = "Start KeibaBook dev environment (Docker + Streamlit)"
    $sc.Save()
    Write-Host "Shortcut created: $shortcutPath"
} catch {
    Write-Error "Failed to create shortcut: $_"
}
