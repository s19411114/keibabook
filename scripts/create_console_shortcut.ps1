param(
    [string]$Name = "KeibaBook Console",
    [string]$TargetScript = "$PSScriptRoot\run_nicegui.ps1",
    [string]$IconPath = ""
)

# Creates a desktop shortcut that launches a PowerShell console and runs start_dev.ps1 with -NoExit
try {
    $desktop = [Environment]::GetFolderPath('Desktop')
    $shortcutPath = Join-Path $desktop ("$Name.lnk")
    $shell = New-Object -ComObject WScript.Shell
    $sc = $shell.CreateShortcut($shortcutPath)
    $psPath = (Get-Command powershell.exe).Source
    $repoRoot = (Split-Path $PSScriptRoot -Parent)
    $command = "Set-Location -Path '$repoRoot'; .\scripts\start_streamlit_win.ps1"
    $args = '-NoExit -ExecutionPolicy Bypass -Command "' + $command + '"'
    $sc.TargetPath = $psPath
    $sc.Arguments = $args
    $sc.WorkingDirectory = Split-Path $TargetScript
    if ($IconPath -and (Test-Path $IconPath)) {
        $sc.IconLocation = (Resolve-Path $IconPath).Path
    } else {
        # try to find icons in project structure
        $candidate1 = Join-Path (Split-Path $PSScriptRoot -Parent) 'scripts\keiba.ico'
        $candidate2 = Join-Path (Split-Path $PSScriptRoot -Parent) 'assets\keiba.ico'
        if (Test-Path $candidate1) { $sc.IconLocation = $candidate1 } elseif (Test-Path $candidate2) { $sc.IconLocation = $candidate2 }
    }
    $sc.WindowStyle = 1
    $sc.Description = "Start KeibaBook Streamlit UI (venv) and keep console open"
    $sc.Save()
    Write-Host "Console shortcut created: $shortcutPath"
} catch {
    Write-Error "Failed to create console shortcut: $_"
}
