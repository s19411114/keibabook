# 競馬ブックスクレイパー - Streamlit起動スクリプト（PowerShell版）
# デスクトップやタスクバーにショートカットを作成して使用

Set-Location "C:\GeminiCLI\TEST\keibabook"

# WSLで仮想環境をアクティベートしてStreamlitを起動
wsl bash -c "cd /mnt/c/GeminiCLI/TEST/keibabook && source .venv/bin/activate && streamlit run app.py"

Write-Host "Streamlitを終了しました。何かキーを押して閉じてください..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

