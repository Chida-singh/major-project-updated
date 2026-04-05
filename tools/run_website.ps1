param(
  [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not (Test-Path .\.venv\Scripts\Activate.ps1)) {
  Write-Host "Missing .venv. Create it with: py -3.11 -m venv .venv" -ForegroundColor Red
  exit 1
}

. .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip | Out-Null
pip install -r requirements.txt | Out-Null

python -m uvicorn server.main:app --reload --port $Port

