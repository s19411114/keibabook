param(
    [string]$NamePattern = '*KeibaBook*.lnk'
)

$sc = Get-ChildItem $env:UserProfile\Desktop -Filter $NamePattern | Select-Object -First 1
if (-not $sc) {
    Write-Host "No shortcut found on desktop matching $NamePattern"
    exit 1
}

$sh = (New-Object -ComObject WScript.Shell).CreateShortcut($sc.FullName)
Write-Host "Found shortcut: $($sc.FullName)"
Write-Host "IconLocation: $($sh.IconLocation)"
Write-Host "Target: $($sh.TargetPath)"
