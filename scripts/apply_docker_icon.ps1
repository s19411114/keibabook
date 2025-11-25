param(
    [string]$ShortcutName = "🐎 KeibaBook Start"
)

# Common paths where Docker Desktop may store its icon
$paths = @(
    "$env:ProgramFiles\Docker\Docker\resources\docker.ico",
    "$env:ProgramFiles(x86)\Docker\Docker\resources\docker.ico",
    "$env:ProgramFiles\Docker Desktop\resources\docker.ico",
    "$env:ProgramFiles(x86)\Docker Desktop\resources\docker.ico",
    "C:\Program Files\Docker\resources\docker.ico",
    "C:\Program Files\Docker Desktop\resources\docker.ico"
)

$found = $null
foreach ($p in $paths) {
    if (Test-Path $p) { $found = $p; break }
}

if (-not $found) {
    Write-Warning "No docker.ico found in standard locations. If Docker is installed, please pass the path manually or use the --IconPath option in create_console_shortcut.ps1"
    exit 1
}

Write-Host "Applying Docker icon: $found"
& "$PSScriptRoot\set_shortcut_icon.ps1" -ShortcutName $ShortcutName -IconPath $found
