$ErrorActionPreference = 'Stop'

Set-Location $PSScriptRoot
py -3.12 -m pip install -r requirements.txt
py -3.12 -m pip install pyinstaller
py -3.12 -m PyInstaller --clean --onefile --name ATI-Agent --paths . launcher.py
py -3.12 -m PyInstaller --clean --onefile --name ATI-Agent-Service --paths . --hidden-import win32timezone service.py
py -3.12 -m PyInstaller --clean --onefile --noconsole --name ATI-Agent-Interactive --paths . interactive.py

Write-Host ''
Write-Host 'Executaveis criados em dist\ATI-Agent.exe, dist\ATI-Agent-Service.exe e dist\ATI-Agent-Interactive.exe'
