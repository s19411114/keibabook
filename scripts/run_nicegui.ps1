<#
Run NiceGUI UI (PowerShell wrapper)
#>
Set-Location -LiteralPath (Join-Path $PSScriptRoot "..")

if (Test-Path ".venv\Scripts\Activate.ps1") {
    . .\.venv\Scripts\Activate.ps1
}

Write-Host "Starting NiceGUI (app_nicegui.py)..."
python -m app_nicegui
