# KeibaBook 統合起動スクリプト (PowerShell版)
# 機能: Docker起動 → Streamlit起動 → ブラウザ起動（最適化版）

param(
    [switch]$SkipDocker = $false,
    [switch]$NoWait = $false,
    [int]$Port = 8501,
    [string]$Browser = "default"
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# カラー出力用関数
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    $colors = @{
        "Success" = "Green"
        "Warning" = "Yellow"
        "Error" = "Red"
        "Info" = "Cyan"
        "Step" = "Magenta"
    }
    if ($colors.ContainsKey($Color)) {
        Write-Host $Message -ForegroundColor $colors[$Color]
    } else {
        Write-Host $Message -ForegroundColor $Color
    }
}

# タイトル
Clear-Host
Write-ColorOutput @"

╔════════════════════════════════════════╗
║  🐎 KeibaBook アプリケーション起動    ║
║     Streamlit UI + Docker              ║
╚════════════════════════════════════════╝

"@ "Step"

# 作業ディレクトリ
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptRoot -ErrorAction Stop

Write-ColorOutput "📂 作業ディレクトリ: $ScriptRoot" "Info"
Write-Host ""

# Docker チェック
if (-not $SkipDocker) {
    Write-ColorOutput "⏳ Docker 状態確認中..." "Info"
    
    try {
        $dockerPs = docker-compose ps 2>&1
        $isRunning = $dockerPs -match "app.*Up"
        
        if (-not $isRunning) {
            Write-ColorOutput "🔄 Docker Compose を起動します..." "Warning"
            docker-compose up -d | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "✅ Docker 起動完了（10秒待機）" "Success"
                Start-Sleep -Seconds 10
            } else {
                Write-ColorOutput "❌ Docker 起動に失敗しました" "Error"
                Read-Host "Enterキーを押して終了"
                exit 1
            }
        } else {
            Write-ColorOutput "✅ Docker は既に起動しています" "Success"
        }
    } catch {
        Write-ColorOutput "⚠️  Docker チェックがスキップされました（Docker非インストール？）" "Warning"
    }
}

Write-Host ""

# Streamlit サーバー起動確認
Write-ColorOutput "⏳ Streamlit サーバー確認中 (http://localhost:$Port)..." "Info"

$maxRetries = 60
$retries = 0
$serverReady = $false

while ($retries -lt $maxRetries -and -not $serverReady) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$Port" -TimeoutSec 1 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $serverReady = $true
            Write-ColorOutput "✅ Streamlit サーバー起動確認完了" "Success"
        }
    } catch {
        # サーバーがまだ起動していない
    }
    
    if (-not $serverReady) {
        if ($retries % 5 -eq 0) {
            Write-Host "   ⏳ サーバー起動待機中... ($retries秒)" -ForegroundColor Gray
        }
        Start-Sleep -Milliseconds 500
        $retries += 0.5
    }
}

if (-not $serverReady) {
    Write-ColorOutput "⚠️  サーバーの起動確認がタイムアウトしました（起動を続行）" "Warning"
}

Write-Host ""

# ブラウザ起動
Write-ColorOutput "🌐 ブラウザを起動中..." "Info"

$url = "http://localhost:$Port"

if ($Browser -eq "default") {
    # デフォルトブラウザで起動
    Start-Process $url
} elseif ($Browser -eq "chrome") {
    # Chrome
    $chromePath = Get-ChildItem -Path @(
        "C:\Program Files\Google\Chrome\Application\chrome.exe",
        "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ) -ErrorAction SilentlyContinue | Select-Object -First 1
    
    if ($chromePath) {
        Start-Process $chromePath.FullName -ArgumentList $url
    } else {
        Write-ColorOutput "Chrome が見つかりません。デフォルトブラウザで起動します。" "Warning"
        Start-Process $url
    }
} elseif ($Browser -eq "edge") {
    # Edge
    $edgePath = Get-ChildItem -Path @(
        "C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    ) -ErrorAction SilentlyContinue | Select-Object -First 1
    
    if ($edgePath) {
        Start-Process $edgePath.FullName -ArgumentList $url
    } else {
        Write-ColorOutput "Edge が見つかりません。デフォルトブラウザで起動します。" "Warning"
        Start-Process $url
    }
} else {
    Start-Process $url
}

Write-Host ""
Write-ColorOutput @"
╔════════════════════════════════════════╗
║      ✅ 起動完了！                     ║
╚════════════════════════════════════════╝

🔗 URL: $url
📌 ブラウザで自動的に開きます
💡 アプリを終了する場合:
   - Streamlit: Ctrl+C
   - Docker: docker-compose down

"@ "Success"

if (-not $NoWait) {
    Read-Host "Enterキーを押して終了"
}
