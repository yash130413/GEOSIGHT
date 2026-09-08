# Architecture

## Overview

GeoSight is a full-stack geospatial AI system:

1. User selects an area of interest (AOI) on a Leaflet map in the React frontend.
2. Frontend calls the Flask API with bounding-box coordinates.
3. Backend fetches a Sentinel-2 median composite from Google Earth Engine.
4. A PyTorch segmentation model runs inference.
5. Backend returns JSON stats plus PNG visualizations served from `artifacts/outputs/`.

```text
┌─────────────┐     HTTP JSON      ┌──────────────────┐     GEE API      ┌────────────────┐
│  React UI   │ ─────────────────► │  Flask backend   │ ───────────────► │ Earth Engine   │
│  (Vite)     │ ◄───────────────── │  app/api + svc   │ ◄─────────────── │ Sentinel-2     │
└─────────────┘   stats + PNG URL  └────────┬─────────┘                  └────────────────┘
                                            │
                                            ▼
                                   ┌──────────────────┐
                                   │ PyTorch models   │
                                   │ land U-Net++     │
                                   │ road U-Net       │
                                   └──────────────────┘
```

## Components

| Layer | Path | Responsibility |
|-------|------|----------------|
| Frontend | `frontend/` | Marketing site + Live Demo map UI |
| API | `backend/app/api/` | HTTP routes / validation |
| Services | `backend/app/services/` | GEE fetch, inference, visualization |
| Config | `backend/app/config.py` | Env-driven paths and ports |
| Artifacts | `artifacts/` | Local model weights + generated outputs (gitignored) |

## Models

- **Land classification:** U-Net++ + EfficientNet-B4, 6 Sentinel-2 bands → Background / Rural / Urban / Water
- **Road detection:** U-Net + ResNet-50, RGB → binary road mask

Weights are expected at:

- `artifacts/models/land_unetpp_epoch11.pt`
- `artifacts/models/road_resnet50.pt`

## API surface

See [api.md](./api.md).
