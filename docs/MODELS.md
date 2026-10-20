# Model checkpoints

The trained weights are **not stored in git** (`*.pt` is ignored because the files are 80–130 MB each).
Ask a project maintainer for the files, then put them where the backend expects them.

## Required files

| Model | File | Default location | Size | SHA-256 |
|---|---|---|---|---|
| Land cover (U-Net++ / EfficientNet-B4) | `geosight_final_epoch_11.pt` | `checkpoints/` | 84,091,206 bytes | `091e4d23777cafba08157af47fca4a7be8d2b5cc250694b1c389a9ad9e5ab375` |
| Roads (U-Net / ResNet-50) | `GeoSight_RoadExpert_Final_PyTorch.pt` | `Models/` | 130,446,586 bytes | `e0380ade43badbae7464edc1dfb51d736e4ed223efd0a2eee6e354ecd58e1b3d` |

Check a downloaded file:

```bash
python -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" checkpoints/geosight_final_epoch_11.pt
```

To keep the files somewhere else, point the backend at them:

```bash
set GEOSIGHT_MODEL_PATH=D:\weights\geosight_final_epoch_11.pt
set GEOSIGHT_ROAD_MODEL_PATH=D:\weights\GeoSight_RoadExpert_Final_PyTorch.pt
```

If a file is missing the backend still starts. `/api/health` reports the model as `missing`, and
requests that need it return an error naming the expected path.

## What each model expects

### Land cover: `geosight_final_epoch_11.pt`

| | |
|---|---|
| Architecture | `smp.UnetPlusPlus(encoder_name="efficientnet-b4", in_channels=6, classes=4)` (segmentation-models-pytorch 0.5.0) |
| Input | Sentinel-2 bands **B2, B3, B4, B8, B11, B12** (in that order), 10 m |
| Preprocessing | `clip(value / 10000, 0, 1)`, NaN → 0, pad height/width to a multiple of 32 |
| Output | 4 logits per pixel: 0 Background, 1 Rural, 2 Urban, 3 Water |
| Training script | `Training/train_unetpp_6band.py` (rebuilt; all 28 saved epoch checkpoints load into it with `strict=True`) |
| Inference code | `backend/predict.py`, `backend/generate_4panel.py` |

Epoch 11 was chosen using the per-epoch class-coverage analysis in
`all_epochs_analysis/all_epochs_results.csv` (best quality score).

### Roads: `GeoSight_RoadExpert_Final_PyTorch.pt`

| | |
|---|---|
| Architecture | `smp.Unet(encoder_name="resnet50", in_channels=3, classes=1)` |
| Input | Sentinel-2 **B4, B3, B2** (RGB) |
| Preprocessing | min–max scale to 0–255, resize to 256×256, `/255`, ImageNet mean/std |
| Output | 1 logit per pixel; `sigmoid > 0.5` = road |
| Training script | `Scripts/Training/Kaggle_Road_Test.py` (10 epochs, batch 8, Adam lr 1e-4, Dice + BCE) |
| Inference code | `backend/predict_roads.py`, `backend/generate_road_viz.py` |

## Measuring accuracy

`Training/evaluate_models.py` scores either model on the held-out validation split and writes the
results to `Geosight_frontend/geosight/src/data/modelEvaluation.json`, which the website's
Insights and About pages display. Until it has been run, those pages show "Not evaluated yet".
