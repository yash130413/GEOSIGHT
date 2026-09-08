# GeoSight

AI-powered satellite land-cover classification and road detection for India-focused geospatial analysis.

**Live Demo flow:** draw an AOI on a map → fetch Sentinel-2 via Google Earth Engine → run U-Net++ (land) or U-Net/ResNet-50 (roads) → view stats + visualizations.

## Quick start

```powershell
# 1) Env
copy .env.example .env
copy frontend\.env.example frontend\.env

# 2) Models → artifacts\models\
#    land_unetpp_epoch11.pt
#    road_resnet50.pt

# 3) Run both servers
.\scripts\start_dev.ps1
```

- Frontend: http://localhost:5173  
- Backend health: http://localhost:5000/api/health  
- Demo: http://localhost:5173/demo  

Full setup (Earth Engine, deps): [docs/setup.md](docs/setup.md)

## Repository layout

```text
geosight/
├── frontend/          # React + Vite UI
├── backend/           # Flask API (app/api + app/services)
├── artifacts/         # Local models + outputs (gitignored)
├── docs/              # Architecture, API, model card
├── ml/                # Placeholder for training code
└── scripts/           # Dev launchers / model download helpers
```

## Tech stack

| Area | Stack |
|------|--------|
| Frontend | React 18, Vite, Leaflet, Framer Motion |
| Backend | Flask, Earth Engine API, Rasterio |
| ML | PyTorch, segmentation-models-pytorch |

## Docs

- [Architecture](docs/architecture.md)
- [Setup](docs/setup.md)
- [API](docs/api.md)
- [Model card](docs/model-card.md)

## License

MIT — see [LICENSE](LICENSE)
