$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$releaseDir = Join-Path $PSScriptRoot 'dist\ATI-Work-Analytics-Agent'
if (Test-Path -LiteralPath $releaseDir) { Remove-Item -LiteralPath $releaseDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null

# A Windows Service cannot observe a user's desktop; build only the invisible interactive agent.
py -3.12 --version
py -3.12 -m pip install --upgrade pip
py -3.12 -m pip install -r requirements.txt pyinstaller
py -3.12 -m PyInstaller --noconfirm --clean --onefile --noconsole --name ATI-Agent-Interactive --paths . --hidden-import win32gui --hidden-import win32process --hidden-import win32timezone --distpath $releaseDir --workpath build interactive.py
$artifact = Join-Path $releaseDir 'ATI-Agent-Interactive.exe'
if (-not (Test-Path -LiteralPath $artifact)) { throw "Build concluído sem o artefato esperado: $artifact" }
Copy-Item -LiteralPath 'install-interactive-agent.ps1', 'uninstall-interactive-agent.ps1', 'README.md' -Destination $releaseDir
Write-Host "Pacote pronto: $releaseDir"
Get-FileHash -Algorithm SHA256 $artifact | Format-List
