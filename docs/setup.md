# Setup

## Prerequisites

- Python 3.10+
- Node.js 18+
- CUDA GPU recommended (CPU works, slower)
- Google Earth Engine account + Cloud project

## 1. Environment file

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```

Set `EE_PROJECT_ID` to your Earth Engine / GCP project id.

## 2. Earth Engine

1. Create a GCP project: https://console.cloud.google.com/projectcreate  
2. Enable Earth Engine API for that project.  
3. Register the project: https://code.earthengine.google.com/register  
4. Authenticate once:

```bash
earthengine authenticate
```

## 3. Model weights

Place weights under `artifacts/models/`:

```text
artifacts/models/land_unetpp_epoch11.pt
artifacts/models/road_resnet50.pt
```

Or run (after editing the download URLs):

```powershell
.\scripts\download_models.ps1
```

## 4. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Server: http://localhost:5000  
Health: http://localhost:5000/api/health

## 5. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173  
Live Demo: http://localhost:5173/demo

## One-command local start (Windows)

```powershell
.\scripts\start_dev.ps1
```

## Verify

1. Open `/demo`
2. Search a city (e.g. Delhi), draw a rectangle
3. Run **Terrain Classification** or **Road Detection**
4. Confirm visualization appears and files land in `artifacts/outputs/`
