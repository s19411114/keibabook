# Streamlit UIをブラウザで起動するショートカットを作成
# 実行方法: powershell -ExecutionPolicy Bypass -File scripts/create_browser_shortcut.ps1

param(
    [string]$ShortcutName = "KeibaBook-Browser",
    [string]$DesktopPath = "$env:USERPROFILE\Desktop"
)

# Docker Composeが起動しているか確認
function Test-DockerCompose {
    try {
        $result = docker-compose ps 2>&1
        return $result -like "*app*"
    } catch {
        return $false
    }
}

# Streamlitポート確認
function Test-StreamlitPort {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8501" -TimeoutSec 2 -ErrorAction SilentlyContinue
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

Write-Host "🐎 KeibaBook ブラウザショートカット作成ツール" -ForegroundColor Cyan

# ショートカット保存先の確認
if (-not (Test-Path $DesktopPath)) {
    Write-Host "⚠️  デスクトップパスが見つかりません: $DesktopPath" -ForegroundColor Yellow
    $DesktopPath = [System.IO.Path]::Combine($env:USERPROFILE, "Desktop")
}

$ShortcutPath = "$DesktopPath\$ShortcutName.lnk"

Write-Host "📍 ショートカット保存先: $ShortcutPath" -ForegroundColor Green

# Windows Scriptを使用してショートカットを作成
$WshShell = New-Object -ComObject WScript.Shell

# ショートカットオブジェクトを作成
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)

# 実行ファイル: PowerShell
$Shortcut.TargetPath = "powershell.exe"

# 引数: Streamlitを起動してブラウザを開く
$Shortcut.Arguments = '-NoExit -Command "Start-Process ''http://localhost:8501'' -WindowStyle Maximized"'

# アイコン（Windows内蔵のブラウザアイコン）
$Shortcut.IconLocation = "C:\Program Files\Internet Explorer\iexplore.exe,0"

# ショートカットの説明
$Shortcut.Description = "KeibaBook Streamlit UI - ブラウザで起動"

# 作業ディレクトリ
$Shortcut.WorkingDirectory = $env:USERPROFILE

# ショートカットを保存
$Shortcut.Save()

Write-Host "✅ ショートカット作成完了！" -ForegroundColor Green
Write-Host "   $ShortcutPath" -ForegroundColor Cyan

# ショートカット設定の表示
Write-Host ""
Write-Host "📋 ショートカット設定:" -ForegroundColor Cyan
Write-Host "   ターゲット: $($Shortcut.TargetPath)"
Write-Host "   引数: $($Shortcut.Arguments)"
Write-Host "   説明: $($Shortcut.Description)"
Write-Host ""

# 使用方法
Write-Host "🚀 使用方法:" -ForegroundColor Yellow
Write-Host "1. 先に Docker を起動してください: docker-compose up -d"
Write-Host "2. ショートカットをダブルクリック"
Write-Host "3. ブラウザで http://localhost:8501 が自動で開きます"
Write-Host ""
Write-Host "💡 ヒント: Streamlit UIを停止する場合は Ctrl+C を押してください"
