$ErrorActionPreference = 'Stop'
 $exePath = Join-Path $PSScriptRoot 'ATI-Agent-Service.exe'
if (-not (Test-Path $exePath)) { $exePath = Join-Path $PSScriptRoot 'dist\ATI-Agent-Service.exe' }
if (-not (Test-Path $exePath)) { throw "ATI-Agent-Service.exe não encontrado em $PSScriptRoot" }
& $exePath stop
& $exePath remove
Write-Host 'Serviço removido. A configuração e os dados em ProgramData foram preservados.'
