Param(
    [switch]$NoBuild,
    [switch]$Open
)

# This PowerShell script automates starting the development environment on Windows.
# It calls Docker Compose to up the container and runs Streamlit inside it.

Set-StrictMode -Version Latest

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $scriptDir/.. | Out-Null

$hostDir = (Get-Item -Path (Resolve-Path .)).FullName

# If WSL is installed, sync the C: drive project into WSL home for better IO
if (Get-Command wsl -ErrorAction SilentlyContinue) {
    try {
        $wslHome = wsl bash -lc 'echo $HOME' 2>$null
        $wslHome = $wslHome.Trim()
        if ($wslHome) {
            $wslHost = "/home/$($wslHome -replace '/home/','')/keibabook"
            Write-Host "Syncing to WSL home: $wslHost"
            wsl rsync -a --delete /mnt/c/GeminiCLI/TEST/keibabook/ $wslHost
            $hostDir = $wslHost
        }
    } catch {
        Write-Host "WSL sync skipped: $_"
    }
}

$env:HOST_PROJECT_DIR = $hostDir

if (-not $NoBuild) {
    Write-Host "Building and starting containers..."
    docker compose up -d --build
} else {
    Write-Host "Starting containers (no build)..."
    docker compose up -d
}

Write-Host "Starting Streamlit in container (detached)..."
try {
    # Use Start-Process to launch the Streamlit command detached so the script returns control
    $dockerArgs = 'compose exec -T app bash -lc "streamlit run app.py --server.port=8501"'
    Start-Process -FilePath 'docker' -ArgumentList $dockerArgs -WindowStyle Hidden
} catch {
    Write-Host "Failed to start Streamlit detached, attempting foreground..."
    docker compose exec -T app bash -lc 'streamlit run app.py --server.port=8501'
}

if ($Open) {
    Start-Process "http://localhost:8501"
}

Pop-Location | Out-Null
