@echo off
chcp 65001 > nul
echo ============================================
echo 🐎 競馬ブックスクレイパーを起動しています...
echo ============================================
echo.

:: 現在のディレクトリをプロジェクトルートに変更
cd /d "%~dp0"

:: Docker Composeでアプリを起動
echo Docker Compose を起動中...
docker-compose up -d

:: Streamlitが起動するまで待機
echo Streamlit の起動を待機中（15秒）...
timeout /t 15 /nobreak > nul

:: ブラウザを開く
echo ブラウザを開きます...
start http://localhost:8501

echo.
echo ============================================
echo ✅ 起動完了！ブラウザでアプリが開きます。
echo.
echo 終了するには:
echo   docker-compose down
echo ============================================
echo.
pause
