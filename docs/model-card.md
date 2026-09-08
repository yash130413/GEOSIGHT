# Model card

## Land classification

| Field | Value |
|-------|--------|
| Task | Multiclass semantic segmentation |
| Architecture | U-Net++ |
| Encoder | EfficientNet-B4 (ImageNet init during training) |
| Input | 6×H×W Sentinel-2 bands: B2, B3, B4, B8, B11, B12 |
| Output classes | Background, Rural, Urban, Water |
| Tile size (train) | 256×256 |
| Checkpoint | `artifacts/models/land_unetpp_epoch11.pt` |
| Normalization | Reflectance / 10000, clipped to [0, 1] |

### Notes / limitations

- NDVI/NDBI are fetched for the GeoTIFF but not used at inference (first 6 bands only).
- Small false water blobs are filtered in the 4-panel visualization.
- Performance depends on cloud cover, season, and AOI size.
- Best qualitative results reported around epoch 11 on India-focused tiles (~70K training tiles).

## Road detection

| Field | Value |
|-------|--------|
| Task | Binary segmentation (road vs non-road) |
| Architecture | U-Net |
| Encoder | ResNet-50 |
| Input | RGB (B4, B3, B2), resized to 256×256 |
| Checkpoint | `artifacts/models/road_resnet50.pt` |
| Normalization | Min-max → ImageNet mean/std |

### Notes / limitations

- Input is resized to 256×256; very large AOIs lose fine detail.
- Thin roads may fragment; morphological cleaning is applied for visualization.
- Threshold is sigmoid > 0.5.

## Ethical / operational use

Intended for research, planning demos, and educational portfolios. Not a substitute for surveyed cadastral or navigation data.
