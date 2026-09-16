$ErrorActionPreference = 'Stop'
$appDir = Join-Path $env:ProgramData 'ATI Work Analytics'
$shortcutPath = Join-Path ([Environment]::GetFolderPath('CommonStartup')) 'ATI Work Analytics Agent.lnk'
$taskName = 'ATI Work Analytics Agent Watchdog'
Remove-Item -LiteralPath $shortcutPath -Force -ErrorAction SilentlyContinue
schtasks.exe /Delete /TN $taskName /F | Out-Null
Remove-Item -LiteralPath $appDir -Recurse -Force -ErrorAction SilentlyContinue
Write-Host 'ATI Work Analytics Agent removido. A fila SQLite local também foi apagada.'
