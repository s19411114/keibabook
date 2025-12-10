$old = [Environment]::GetEnvironmentVariable('Path','User')
$parts = $old -split ';' | Where-Object { $_ -ne '' -and $_ -notmatch 'Python314' }
$new = $parts -join ';'
[Environment]::SetEnvironmentVariable('Path', $new, 'User')
Write-Host 'User PATH updated (Python314 entries removed)'
Write-Host 'New PATH:'
$new -split ';' | ForEach-Object { Write-Host "  $_" }
