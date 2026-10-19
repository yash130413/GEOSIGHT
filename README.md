# GeoSight 🌍

GeoSight is a comprehensive machine learning pipeline that automatically performs multiclass semantic segmentation on high-resolution geographical TIF satellite imagery. The objective is to identify and map the terrain into distinct classes: Background, Rural, Urban, and Water.

## Features

- **Deep Learning Architecture:** Uses a `LinkNet` segmentation model powered by a `ResNet50` backbone.
- **Data Augmentation:** Features aggressive data augmentation during training using `Albumentations` to build robust geospatial predictions.
- **Geospatial Processing:** Handles multi-band (6-channel) satellite imagery leveraging the `rasterio` library dynamically.
- **Mixed Precision Training:** Uses `torch.amp` (bfloat16) to fit large geographic batches into RTX hardware at scale.

## Project Structure

```text
GEO/
├── backend/              # Flask API, inference, and visualization services
│   ├── app.py            # Runtime entry point
│   ├── predict.py        # Land-cover model loading and inference
│   ├── predict_roads.py  # Road model loading and inference
│   └── requirements.txt  # Backend runtime dependencies
├── Training/
│   └── train.py          # Primary 6-band LinkNet/ResNet50 training pipeline
├── data_scripts/         # Mask generation, labeling, and dataset preparation
├── Scripts/
│   ├── Data_Processing/  # Dataset and tile processing
│   ├── Testing/          # Model and road evaluation scripts
│   └── Visualization/   # Offline visualization tools
├── tools/
│   ├── analysis/         # Standalone image and tile analysis utilities
│   ├── earth_engine/     # Earth Engine authentication and fetch utilities
│   └── modeling/         # Standalone model inspection and mask utilities
├── tests/                # Local smoke tests and manual test pages
├── docs/
│   ├── guides/           # Setup, feature, and troubleshooting guides
│   ├── Claude.md         # Development notes
│   └── Logbook.md        # Project log
├── Geosight_frontend/
│   └── geosight/         # Frontend application
├── checkpoints/          # Trained model weights (ignored by Git)
├── backend_outputs/      # Runtime API outputs (ignored/generated)
├── outputs/              # Offline processing outputs
├── visualizations/       # Generated visualization outputs
└── requirements.txt      # Shared Python dependencies
```

Root-level files are limited to project manifests, launch scripts, sample
imagery, and this README. Generated results and local Python environments are
kept outside the source tree organization and are not part of the runtime
architecture.

### Model architecture

The production land-cover model is trained by `Training/train.py` and loaded by
`backend/predict.py`. It is a 6-band LinkNet model with a ResNet50 encoder and
four output classes: Background, Rural, Urban, and Water. The backend currently
loads `checkpoints/geosight_final_epoch_11.pt`.

Road extraction is a separate model and is intentionally kept independent from
land-cover classification. Its runtime implementation is in
`backend/predict_roads.py`, with weights stored under `Models/`.

The former 8-band experimental trainer was removed because the runtime backend
uses the 6-band model and the 8-band script was not part of the active pipeline.

## Setup & Installation

Assuming you have Python and a capable CUDA GPU installed:

1. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv myenv
   myenv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Ensure PyTorch is installed with CUDA capability to run the models efficiently on GPUs.*

## Usage

### 1. Training The Model
Update the `IMG_DIR` and `MASK_DIR` paths in `Training/train.py` to match where your `TIF` satellite and labeled masks are isolated.
```bash
python Training/train.py
```
This script will output `.pt` files containing model checkpoints inside the `checkpoints/` directory every epoch.

### 2. Full Inference / Visualization
Evaluate your completed model across the dataset by using the relevant script in `Scripts/Visualization/`.
```bash
python Scripts/Visualization/visualization.py
```
Predictions will be written to discrete `.tif` single-channel rasters.

### 3. Start the application

From the repository root:

```bat
start_system.bat
```

The script starts the Flask API from `backend/` and the Vite frontend from
`Geosight_frontend/geosight/`.

## Evaluation Metrics

This project uses:
- Micro Intersection over Union (mIoU)
- Macro Accuracy
- Combined `DiceLoss` + `FocalLoss` for highly imbalanced class weighting (e.g. Water vs. Background).

## Artificial Intelligence (MCP) Integrations

This codebase is configured to be augmented by an AI using **Model Context Protocol (MCP) Servers**.
The configuration file is located at `.cursor/mcp.json` (or you can copy its contents to your `claude_desktop_config.json`).

The following MCP integrations are built-in:
1. **geosight-filesystem**: Allows the AI to natively securely read/write to the `GeoSight2` dataset and code directories.
2. **geosight-sqlite**: Allows the AI to query the massive dataset manifest via SQL. *(Note: First run `python data_scripts/csv_to_sqlite.py` to convert your `geosight_manifest_70k.csv` into the required `geosight.db` file).*
3. **geosight-memory**: Allows the AI to remember critical learning rate curves, hyperparameter tuning failures, and hardware constraints persistently across your coding sessions.
4. **github-mcp**: Syncs PRs and Issues perfectly. *(Provide your token in the config).*
5. **fetch-docs**: Lets the AI dynamically read PyTorch and Rasterio documentation online if an API deprecates.
