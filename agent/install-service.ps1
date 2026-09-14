$ErrorActionPreference = 'Stop'

$serviceDir = Join-Path $env:ProgramData 'ATI Work Analytics'
New-Item -ItemType Directory -Force -Path $serviceDir | Out-Null

$apiUrl = Read-Host 'URL da API (ex.: http://10.36.30.100:9000/api/v1)'
$config = @{
    api_url = $apiUrl.TrimEnd('/')
    collection_interval_seconds = 5
    sync_interval_seconds = 60
    idle_threshold_seconds = 60
    data_directory = (Join-Path $serviceDir 'data')
} | ConvertTo-Json
Set-Content -Path (Join-Path $serviceDir 'config.json') -Value $config -Encoding UTF8

 $exePath = Join-Path $PSScriptRoot 'ATI-Agent-Service.exe'
if (-not (Test-Path $exePath)) { $exePath = Join-Path $PSScriptRoot 'dist\ATI-Agent-Service.exe' }
if (-not (Test-Path $exePath)) { throw "ATI-Agent-Service.exe não encontrado em $PSScriptRoot" }
& $exePath --startup auto install
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar o serviço ATIWorkAnalytics." }
& $exePath start --wait 15
if ($LASTEXITCODE -ne 0) { throw "O serviço foi instalado, mas não iniciou. Consulte: sc.exe query ATIWorkAnalytics" }

Write-Host ''
Write-Host 'Serviço instalado e iniciado.'
Write-Host 'Verifique em http://localhost:9001/machines e aprove a máquina PENDING.'
Write-Host 'Para remover: .\uninstall-service.ps1'
