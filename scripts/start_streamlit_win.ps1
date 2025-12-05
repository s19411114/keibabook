<#
KeibaBook: Windows venv 起動 (PowerShell)
Usage:
  .\scripts\start_streamlit_win.ps1
#>
Set-Location -LiteralPath (Join-Path $PSScriptRoot "..")

Write-Host "============================================="
Write-Host "🐎 KeibaBook: Windows venv 起動 (PowerShell)"
Write-Host "============================================="

if (-Not (Test-Path -Path ".venv\Scripts\python.exe")) {
    Write-Error "仮想環境 (.venv) が見つかりません。まず作成してください。例: python -m venv .venv"
    exit 1
}

# dot-source Activate.ps1 to set env in current session
. .\.venv\Scripts\Activate.ps1

Write-Host "Running Streamlit..."
python -m streamlit run app.py

Write-Host "Streamlit process exited. Press Enter to close..."
[void][System.Console]::ReadLine()
