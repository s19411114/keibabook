@echo off
REM KeibaBook アプリケーション統合起動スクリプト
REM 機能: Docker起動 → Streamlit起動 → ブラウザ自動起動

setlocal enabledelayedexpansion
chcp 65001 > nul

echo.
echo ========================================
echo   🐎 KeibaBook アプリケーション起動
echo ========================================
echo.

REM ディレクトリ確認
cd /d "%~dp0\.."
if errorlevel 1 (
    echo ❌ ディレクトリ移動に失敗しました
    pause
    exit /b 1
)

echo 📂 作業ディレクトリ: %cd%
echo.

REM Docker起動確認
echo ⏳ Docker 状態確認中...
docker-compose ps >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Docker Compose を起動します...
    docker-compose up -d
    if errorlevel 1 (
        echo ❌ Docker 起動に失敗しました
        pause
        exit /b 1
    )
    echo ✅ Docker 起動完了
    timeout /t 3
) else (
    echo ✅ Docker は既に起動しています
)

echo.
echo ⏳ Streamlit サーバー確認中...

REM Streamlitサーバー確認（最大30秒待機）
set "retries=0"
:streamlit_check
if !retries! geq 30 (
    echo ⚠️  Streamlit サーバー起動に時間がかかっています...
    timeout /t 3
    goto open_browser
)

powershell -Command "try { $null = Invoke-WebRequest -Uri 'http://localhost:8501' -TimeoutSec 1 -ErrorAction SilentlyContinue; exit 0 } catch { exit 1 }"
if errorlevel 1 (
    echo ⏳ Streamlit サーバー起動待機中... (!retries!秒)
    timeout /t 1 /nobreak
    set /a "retries=!retries!+1"
    goto streamlit_check
)

echo ✅ Streamlit サーバー起動確認完了
echo.

:open_browser
echo 🌐 ブラウザを起動中...
start "KeibaBook" "http://localhost:8501"

echo.
echo ========================================
echo   ✅ KeibaBook アプリケーション起動完了
echo ========================================
echo.
echo 📌 ブラウザで http://localhost:8501 が開きます
echo 💡 アプリケーション停止時は Ctrl+C を押してください
echo.

pause
