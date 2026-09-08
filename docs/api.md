# API

Base URL (local): `http://localhost:5000`

## `GET /api/health`

Returns service status.

```json
{
  "status": "ok",
  "message": "GeoSight backend is running",
  "earth_engine": "connected"
}
```

## `POST /api/fetch-image`

Fetch Sentinel-2 imagery and run land-cover classification.

### Request

```json
{
  "bounds": {
    "minLon": 77.0,
    "minLat": 28.5,
    "maxLon": 77.3,
    "maxLat": 28.7
  },
  "cloudCover": 10,
  "startDate": "2024-01-01",
  "endDate": "2024-12-31"
}
```

### Success response (shape)

```json
{
  "success": true,
  "file": "sentinel2_lat28.50_lon77.00_YYYYMMDD_HHMMSS.tif",
  "info": {
    "width": 512,
    "height": 512,
    "bands": 8,
    "resolution": "10.0m",
    "band_order": ["B2", "B3", "B4", "B8", "B11", "B12", "NDVI", "NDBI"]
  },
  "prediction": {
    "dominant_class": "Urban",
    "class_distribution": {},
    "image_size": { "width": 512, "height": 512 },
    "total_pixels": 262144
  },
  "visualization_4panel": "4panel_....png"
}
```

## `POST /api/detect-roads`

Fetch RGB Sentinel-2 imagery and run road detection.

Request body matches `fetch-image` (`bounds`, optional `cloudCover`, `startDate`, `endDate`).

### Success response (shape)

```json
{
  "success": true,
  "file": "road_input_....tif",
  "model": "RoadExpert (ResNet-50)",
  "road_detection": {
    "road_percentage": 12.34,
    "road_pixels": 8000,
    "total_pixels": 65536
  },
  "visualization": "road_viz_....png"
}
```

## `GET /api/download/<filename>`

Serves a generated GeoTIFF (attachment) or PNG (inline) from `artifacts/outputs/`.
