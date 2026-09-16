param(
    [Parameter(Mandatory = $true)][ValidatePattern('^https?://')][string]$ApiUrl,
    [switch]$SkipApiHealthCheck
)
$ErrorActionPreference = 'Stop'
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Abra o PowerShell como Administrador para instalar o agente.'
}
$apiUrl = $ApiUrl.TrimEnd('/')
$healthUrl = ($apiUrl -replace '/api/v1$', '') + '/health'
$source = Join-Path $PSScriptRoot 'ATI-Agent-Interactive.exe'
$appDir = Join-Path $env:ProgramData 'ATI Work Analytics'
$dataDir = Join-Path $appDir 'data'
$destination = Join-Path $appDir 'ATI-Agent-Interactive.exe'
$shortcutPath = Join-Path ([Environment]::GetFolderPath('CommonStartup')) 'ATI Work Analytics Agent.lnk'
$taskName = 'ATI Work Analytics Agent Watchdog'

if (-not (Test-Path -LiteralPath $source)) { throw "Executável não encontrado: $source" }
if (-not $SkipApiHealthCheck) {
    try {
        $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 10
        if ($health.status -ne 'ok') { throw 'Resposta de health inválida.' }
    } catch { throw "Não foi possível acessar a API em $healthUrl. Corrija a URL ou use -SkipApiHealthCheck somente se a rede ainda não estiver disponível." }
}
New-Item -ItemType Directory -Force -Path $appDir, $dataDir | Out-Null
# Standard users can write only the local SQLite queue and log. They cannot alter the executable or configuration.
icacls $dataDir /grant '*S-1-5-32-545:(OI)(CI)M' /T | Out-Null
@{ api_url = $apiUrl; collection_interval_seconds = 5; sync_interval_seconds = 60; idle_threshold_seconds = 60; data_directory = $dataDir } | ConvertTo-Json | Set-Content -Path (Join-Path $appDir 'config.json') -Encoding UTF8
Copy-Item -LiteralPath $source -Destination $destination -Force
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $destination; $shortcut.WorkingDirectory = $appDir; $shortcut.WindowStyle = 7; $shortcut.Description = 'ATI Work Analytics — agente de atividade'; $shortcut.Save()
$taskAction = "`"$destination`""
schtasks.exe /Create /TN $taskName /TR $taskAction /SC MINUTE /MO 1 /IT /F | Out-Null
Write-Host "Instalação concluída em $appDir"
Write-Host 'O agente iniciará no próximo logon e será revalidado a cada minuto após suspensão ou desbloqueio.'
Write-Host 'Agora aprove a máquina PENDING no dashboard e faça logoff/logon.'
