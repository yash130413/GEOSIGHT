#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/artifacts/models" "$ROOT/artifacts/outputs"

echo "Place model weights manually, or set LAND_MODEL_URL / ROAD_MODEL_URL and re-run."
echo "Expected files:"
echo "  $ROOT/artifacts/models/land_unetpp_epoch11.pt"
echo "  $ROOT/artifacts/models/road_resnet50.pt"

if [[ -n "${LAND_MODEL_URL:-}" ]]; then
  curl -L "$LAND_MODEL_URL" -o "$ROOT/artifacts/models/land_unetpp_epoch11.pt"
fi
if [[ -n "${ROAD_MODEL_URL:-}" ]]; then
  curl -L "$ROAD_MODEL_URL" -o "$ROOT/artifacts/models/road_resnet50.pt"
fi
