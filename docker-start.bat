@echo off
REM Docker環境起動スクリプト (Windows用)
REM このスクリプトはWSL経由でDockerを起動します

echo 🐳 Keibabook Docker環境を起動します...
echo.

REM WSLが利用可能か確認
wsl --list >nul 2>&1
if errorlevel 1 (
    echo ❌ WSLが見つかりません。WSLをインストールしてください。
    pause
    exit /b 1
)

REM WSL経由でdocker-start.shを実行
echo 📂 WSL環境に切り替えています...
wsl bash -c "cd /mnt/c/GeminiCLI/TEST/keibabook && chmod +x docker-start.sh && ./docker-start.sh"

pause
