@echo off
chcp 65001 > nul
echo 🐎 競馬ブックスクレイパーを起動しています...
echo.

:: WSLでStreamlitを起動 (新しいウィンドウで実行)
start "KeibaBook Scraper Log" wsl bash -c "cd /mnt/c/GeminiCLI/TEST/keibabook && source venv/bin/activate && streamlit run app.py --server.address 0.0.0.0 --server.enableCORS false --server.headless true"

:: 起動待ち (5秒)
echo サーバーの立ち上がりを待っています...
timeout /t 5 > nul

:: ブラウザを開く
echo ブラウザを開きます...
start http://localhost:8501

echo.
echo ✅ 起動しました！
echo 画面が開かない場合は http://localhost:8501 にアクセスしてください。
echo.
pause
