@echo off
REM 競馬ブックスクレイパー - Streamlit起動スクリプト
REM デスクトップやタスクバーにショートカットを作成して使用

cd /d C:\GeminiCLI\TEST\keibabook

REM WSLで仮想環境をアクティベートしてStreamlitを起動
wsl bash -c "cd /mnt/c/GeminiCLI/TEST/keibabook && source .venv/bin/activate && streamlit run app.py"

pause

