param([Parameter(Mandatory = $true)][string]$ApiUrl)
$ErrorActionPreference = 'Stop'
$appDir = Join-Path $env:ProgramData 'ATI Work Analytics'
$dataDir = Join-Path $appDir 'data'
New-Item -ItemType Directory -Force -Path $appDir, $dataDir | Out-Null
# Only the SQLite queue/log directory is writable by standard users. The executable and config remain administrator-controlled.
icacls $dataDir /grant '*S-1-5-32-545:(OI)(CI)M' /T | Out-Null
$config = @{ api_url = $ApiUrl.TrimEnd('/'); collection_interval_seconds = 5; sync_interval_seconds = 60; idle_threshold_seconds = 60; data_directory = $dataDir } | ConvertTo-Json
Set-Content -Path (Join-Path $appDir 'config.json') -Value $config -Encoding UTF8
$source = Join-Path $PSScriptRoot 'ATI-Agent-Interactive.exe'
if (-not (Test-Path $source)) { throw 'ATI-Agent-Interactive.exe não encontrado.' }
Copy-Item $source (Join-Path $appDir 'ATI-Agent-Interactive.exe') -Force
Write-Host 'Arquivos instalados. Configure uma Scheduled Task de logon via GPO para executar ATI-Agent-Interactive.exe no contexto do usuário.'
