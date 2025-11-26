@echo off
REM KeibaBook アプリ起動ショートカット作成スクリプト

setlocal enabledelayedexpansion
chcp 65001 > nul

echo.
echo ========================================
echo  🐎 KeibaBook デスクトップショートカット作成
echo ========================================
echo.

REM スクリプトの実行場所
set SCRIPT_DIR=%~dp0
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT_NAME=KeibaBook-App

echo 📂 スクリプト位置: %SCRIPT_DIR%
echo 📍 デスクトップ: %DESKTOP%
echo.

REM VBScript で ショートカットを作成
set TEMP_VBS=%TEMP%\create_shortcut.vbs

(
echo Set oWS = WScript.CreateObject("WScript.Shell"^)
echo sLinkFile = "%DESKTOP%\%SHORTCUT_NAME%.lnk"
echo Set oLink = oWS.CreateShortcut(sLinkFile^)
echo oLink.TargetPath = "powershell.exe"
echo oLink.Arguments = "-ExecutionPolicy Bypass -File ""%SCRIPT_DIR%start_app_browser.ps1"" -NoWait"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%.."
echo oLink.Description = "KeibaBook Streamlit UI - 統合起動"
echo oLink.IconLocation = "C:\Program Files\Internet Explorer\iexplore.exe,0"
echo oLink.Save
echo WScript.Echo "Shortcut created: " ^& sLinkFile
) > "%TEMP_VBS%"

cscript.exe "%TEMP_VBS%"
del "%TEMP_VBS%"

echo.
echo ✅ ショートカット作成完了！
echo   デスクトップに "%SHORTCUT_NAME%.lnk" が作成されました
echo.
echo 🚀 使用方法:
echo   1. デスクトップの "KeibaBook-App" をダブルクリック
echo   2. ブラウザが自動的に起動します
echo.

pause
