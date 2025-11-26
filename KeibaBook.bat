@echo off
REM KeibaBook ブラウザ起動型ショートカット
REM 馬の顔が見える競馬ブックスクレイパー

setlocal enabledelayedexpansion
chcp 65001 >nul

echo.
echo ========================================
echo   🐎 KeibaBook アプリケーション起動
echo ========================================
echo.

REM 現在のディレクトリを取得
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo 📂 作業ディレクトリ: %cd%
echo.

REM Docker起動確認
echo ⏳ Docker 状態確認中...
docker-compose ps >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Docker Compose を起動します...
    start /b docker-compose up -d
    if errorlevel 1 (
        echo ❌ Docker 起動に失敗しました
        pause
        exit /b 1
    )
    echo ✅ Docker 起動完了
    timeout /t 5 /nobreak >nul
) else (
    echo ✅ Docker は既に起動しています
)

echo.
echo ⏳ Streamlit サーバー確認中...

REM Streamlitサーバー確認（最大60秒待機）
set "retries=0"
:streamlit_check
if !retries! geq 60 (
    echo ⚠️  Streamlit サーバー起動に時間がかかっています...
    echo 🌐 ブラウザを起動します（サーバー準備中の可能性があります）
    goto open_browser
)

powershell -Command "try { $null = Invoke-WebRequest -Uri 'http://localhost:8501' -TimeoutSec 1 -ErrorAction SilentlyContinue; exit 0 } catch { exit 1 }"
if errorlevel 1 (
    if !retries! equ 0 (
        echo ⏳ Streamlit サーバー起動待機中...
    )
    timeout /t 1 /nobreak >nul
    set /a "retries=!retries!+1"
    goto streamlit_check
)

echo ✅ Streamlit サーバー起動確認完了
echo.

:open_browser
echo 🌐 ブラウザを起動中...
start "" "http://localhost:8501"

echo.
echo ========================================
echo   ✅ KeibaBook 起動完了
echo ========================================
echo.
echo 📌 ブラウザで http://localhost:8501 が開きます
echo 💡 このウィンドウは閉じても構いません
echo 🛑 アプリケーション停止時は: docker-compose down
echo.

REM ウィンドウを自動的に閉じる（3秒後）
timeout /t 3 /nobreak >nul
exit
