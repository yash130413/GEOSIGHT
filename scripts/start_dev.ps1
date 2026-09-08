$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "Starting GeoSight backend + frontend..."
Write-Host "Backend:  http://localhost:5000"
Write-Host "Frontend: http://localhost:5173"
Write-Host "Demo:     http://localhost:5173/demo"

Start-Process powershell -ArgumentList @(
  '-NoExit', '-Command',
  "Set-Location '$Root\backend'; python run.py"
)

Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList @(
  '-NoExit', '-Command',
  "Set-Location '$Root\frontend'; npm run dev"
)
