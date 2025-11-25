@echo off
REM KeibaBook Scraper - デスクトップショートカット作成スクリプト
REM ダブルクリックでStreamlit UIを起動し、ブラウザで開く

setlocal

REM デスクトップパスを取得
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT_NAME=KeibaBook Scraper.url
set SHORTCUT_PATH=%DESKTOP%\%SHORTCUT_NAME%

REM インターネットショートカット（.url）を作成
echo [InternetShortcut] > "%SHORTCUT_PATH%"
echo URL=http://localhost:8501 >> "%SHORTCUT_PATH%"
echo IconIndex=0 >> "%SHORTCUT_PATH%"
echo IconFile=%SystemRoot%\System32\SHELL32.dll,14 >> "%SHORTCUT_PATH%"

echo.
echo ショートカット "%SHORTCUT_NAME%" をデスクトップに作成しました。
echo.
echo 【使い方】
echo 1. まず docker-start.bat を実行してアプリを起動
echo 2. デスクトップの "%SHORTCUT_NAME%" をダブルクリック
echo 3. ブラウザで http://localhost:8501 が開きます
echo.
pause
