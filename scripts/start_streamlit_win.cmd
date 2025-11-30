@echo off
chcp 65001 > nul
echo ============================================
echo 🐎 KeibaBook: Windows venv 起動 (cmd)
echo ============================================

:: Move to repository root (script directory)
cd /d "%~dp0\.."

:: Check venv exists
if not exist ".venv\Scripts\python.exe" (
  echo 仮想環境 (.venv) が見つかりません。まず作成してください。
  echo 例: python -m venv .venv
  pause
  exit /b 1
)

:: Activate and run Streamlit
call .\.venv\Scripts\activate.bat
echo Running Streamlit...
python -m streamlit run app.py
echo Streamlit process exited.
pause
