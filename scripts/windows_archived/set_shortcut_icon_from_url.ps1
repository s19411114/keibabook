param(
    [string]$ShortcutName = "🐎 KeibaBook Start",
    [string]$IconUrl
)

if (-not $IconUrl) {
    Write-Error "Usage: .\set_shortcut_icon_from_url.ps1 -ShortcutName '🐎 KeibaBook Start' -IconUrl 'https://example.com/icon.ico'"
    exit 1
}

$assetsDir = Join-Path $PSScriptRoot '..' 'assets'
if (-not (Test-Path $assetsDir)) { New-Item -ItemType Directory -Path $assetsDir | Out-Null }

$iconFileName = Split-Path $IconUrl -Leaf
$downloadPath = Join-Path $assetsDir $iconFileName

Write-Host "Downloading $IconUrl to $downloadPath"
try {
    Invoke-WebRequest -Uri $IconUrl -OutFile $downloadPath -UseBasicParsing -ErrorAction Stop
} catch {
    Write-Error "Failed to download icon: $_"
    exit 1
}

if (-not (Test-Path $downloadPath)) { Write-Error "Download failed: $downloadPath"; exit 1 }

# If not ICO, warn user
if (($downloadPath -split '\.')[-1].ToLower() -ne 'ico') {
    Write-Warning "Downloaded file is not .ico. Windows expects ICO for shortcut icons. If this is a PNG/SVG, convert to ICO before running the apply step."
}

Write-Host "Applying $downloadPath to shortcut $ShortcutName"
.
\set_shortcut_icon.ps1 -ShortcutName $ShortcutName -IconPath $downloadPath
