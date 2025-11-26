@echo off
REM KeibaBook デスクトップショートカット作成スクリプト
REM 馬のアイコン付きブラウザ起動型ショートカット

setlocal enabledelayedexpansion
chcp 65001 >nul

echo.
echo ========================================
echo  🐎 KeibaBook ショートカット作成
echo ========================================
echo.

REM 現在のディレクトリとファイルパスを取得
set "SCRIPT_DIR=%~dp0"
set "BATCH_FILE=%SCRIPT_DIR%KeibaBook.bat"
set "ICON_FILE=%SCRIPT_DIR%assets\horse.ico"

REM デスクトップパスを取得
set "DESKTOP=%USERPROFILE%\Desktop"

echo 📂 プロジェクトディレクトリ: %SCRIPT_DIR%
echo 🖥️  デスクトップパス: %DESKTOP%
echo.

REM アイコンファイルの存在確認
if not exist "%ICON_FILE%" (
    echo ⚠️  警告: アイコンファイルが見つかりません
    echo    パス: %ICON_FILE%
    echo    デフォルトアイコンを使用します
)

REM PowerShellでショートカットを作成
echo 🔧 ショートカットを作成中...

powershell -Command ^
"$WshShell = New-Object -ComObject WScript.Shell; ^
$Shortcut = $WshShell.CreateShortcut('%DESKTOP%\KeibaBook.lnk'); ^
$Shortcut.TargetPath = '%BATCH_FILE%'; ^
$Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; ^
$Shortcut.Description = '競馬ブックスクレイパー（ブラウザ起動型）'; ^
$Shortcut.IconLocation = '%ICON_FILE%,0'; ^
$Shortcut.Save()"

if errorlevel 1 (
    echo ❌ ショートカット作成に失敗しました
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✅ ショートカット作成完了！
echo ========================================
echo.
echo 📍 場所: %DESKTOP%\KeibaBook.lnk
echo 🐎 アイコン: 馬のアイコン
echo 🌐 機能: ブラウザ自動起動
echo.
echo 💡 Tip: タスクバーにピン留めもできます
echo.

pause
