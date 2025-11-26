@echo off
REM KeibaBook Scraper - ブラウザ型ショートカット作成
REM ターミナルが表示されない静かな起動用

setlocal

REM デスクトップパスを取得
set DESKTOP=%USERPROFILE%\Desktop
set PROJECT_DIR=%~dp0

REM 1. VBScriptランチャーを作成（ウィンドウ非表示で実行）
set VBS_FILE=%PROJECT_DIR%launcher.vbs
echo Set WshShell = CreateObject("WScript.Shell") > "%VBS_FILE%"
echo WshShell.CurrentDirectory = "%PROJECT_DIR%" >> "%VBS_FILE%"
echo ' Docker起動（非表示） >> "%VBS_FILE%"
echo WshShell.Run "docker compose up -d", 0, True >> "%VBS_FILE%"
echo ' 少し待機 >> "%VBS_FILE%"
echo WScript.Sleep 3000 >> "%VBS_FILE%"
echo ' ブラウザで開く >> "%VBS_FILE%"
echo WshShell.Run "http://localhost:8501", 1, False >> "%VBS_FILE%"

REM 2. インターネットショートカットを作成
set URL_SHORTCUT=%DESKTOP%\KeibaBook (ブラウザで開く).url
echo [InternetShortcut] > "%URL_SHORTCUT%"
echo URL=http://localhost:8501 >> "%URL_SHORTCUT%"
echo IconIndex=0 >> "%URL_SHORTCUT%"

REM 3. ランチャーショートカットを作成（.lnkは複雑なのでバッチ経由）
set LAUNCHER_BAT=%PROJECT_DIR%start_silent.bat
echo @echo off > "%LAUNCHER_BAT%"
echo cd /d "%%~dp0" >> "%LAUNCHER_BAT%"
echo start /min wscript.exe launcher.vbs >> "%LAUNCHER_BAT%"

REM 4. デスクトップにショートカット（.url形式で起動バッチを指す）
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\KeibaBook Scraper.lnk'); $s.TargetPath = '%LAUNCHER_BAT%'; $s.WorkingDirectory = '%PROJECT_DIR%'; $s.IconLocation = 'shell32.dll,14'; $s.WindowStyle = 7; $s.Save()"

echo.
echo ============================================
echo デスクトップにショートカットを作成しました！
echo ============================================
echo.
echo 【作成されたショートカット】
echo 1. KeibaBook Scraper.lnk - ダブルクリックでDocker起動＋ブラウザ自動オープン
echo 2. KeibaBook (ブラウザで開く).url - アプリ起動済み時にブラウザで開くだけ
echo.
echo 【注意】
echo - 初回はDockerイメージのダウンロードに時間がかかることがあります
echo - Docker Desktopが起動している必要があります
echo.
pause
