param(
    [string]$ShortcutName = "🐎 KeibaBook Start"
)

function Try-Search-Folder($folder) {
    if (Test-Path $folder) {
        try {
            Get-ChildItem -Path $folder -Filter 'docker*.ico' -Recurse -ErrorAction SilentlyContinue -Force | Select-Object -First 1
        } catch {
            $null
        }
    }
}

$candidates = @()
$candidates += Try-Search-Folder "$env:ProgramFiles"
if (Test-Path 'C:\Program Files (x86)') { $candidates += Try-Search-Folder 'C:\Program Files (x86)' }
if ($env:LOCALAPPDATA) { $candidates += Try-Search-Folder "$env:LOCALAPPDATA\Programs" }
if ($env:ProgramW6432) { $candidates += Try-Search-Folder "$env:ProgramW6432" }

$found = $null
foreach ($c in $candidates) {
    if ($c -and $c.FullName) { $found = $c.FullName; break }
}

if (-not $found) {
    Write-Warning "Docker icon not found in scanned locations. Please run apply_docker_icon.ps1 or provide a .ico file to set_shortcut_icon.ps1"
    exit 1
}

Write-Host "Found Docker icon: $found"
& "$PSScriptRoot\set_shortcut_icon.ps1" -ShortcutName $ShortcutName -IconPath $found
