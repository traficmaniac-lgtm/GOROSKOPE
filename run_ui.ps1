Param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $MyInvocation.MyCommand.Path -Parent
Set-Location $projectRoot

$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-Not (Test-Path $python)) {
    Write-Error "Не найден $python. Запустите 00_setup_repo.ps1"
}

& $python -m ui.control_panel
