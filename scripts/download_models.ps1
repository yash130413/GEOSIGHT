$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
New-Item -ItemType Directory -Force -Path "$Root\artifacts\models", "$Root\artifacts\outputs" | Out-Null

Write-Host "Expected model files:"
Write-Host "  $Root\artifacts\models\land_unetpp_epoch11.pt"
Write-Host "  $Root\artifacts\models\road_resnet50.pt"

if ($env:LAND_MODEL_URL) {
  Invoke-WebRequest -Uri $env:LAND_MODEL_URL -OutFile "$Root\artifacts\models\land_unetpp_epoch11.pt"
}
if ($env:ROAD_MODEL_URL) {
  Invoke-WebRequest -Uri $env:ROAD_MODEL_URL -OutFile "$Root\artifacts\models\road_resnet50.pt"
}

Write-Host "Done. If URLs were not set, copy .pt files into artifacts\models manually."
