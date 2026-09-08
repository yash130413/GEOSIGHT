"""Google Earth Engine Sentinel-2 fetch helpers."""
from datetime import datetime, timedelta

import ee
import requests

from app.config import EE_PROJECT_ID


def init_earth_engine():
    """Initialize Earth Engine with project ID; authenticate if needed."""
    try:
        ee.Initialize(project=EE_PROJECT_ID)
        print("[OK] Earth Engine initialized")
    except Exception:
        print("[INFO] Authenticating Earth Engine...")
        ee.Authenticate()
        ee.Initialize(project=EE_PROJECT_ID)
        print("[OK] Authenticated")


def parse_date_range(data):
    start_date = data.get(
        "startDate", (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    )
    end_date = data.get("endDate", datetime.now().strftime("%Y-%m-%d"))
    max_cloud_cover = data.get("cloudCover", 10)
    return start_date, end_date, max_cloud_cover


def fetch_multispectral_geotiff(bounds, start_date, end_date, max_cloud_cover, output_path):
    """
    Fetch 8-band Sentinel-2 median composite (B2–B12 + NDVI + NDBI) as GeoTIFF.
    Returns (width, height, bands, resolution) metadata.
    """
    import rasterio

    min_lon = bounds["minLon"]
    min_lat = bounds["minLat"]
    max_lon = bounds["maxLon"]
    max_lat = bounds["maxLat"]

    region = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])
    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud_cover))
    )

    count = collection.size().getInfo()
    if count == 0:
        raise FileNotFoundError(
            f"No images found with <{max_cloud_cover}% cloud cover"
        )

    print(f"[OK] Found {count} images")
    image = collection.median()

    b2 = image.select("B2").toFloat()
    b3 = image.select("B3").toFloat()
    b4 = image.select("B4").toFloat()
    b8 = image.select("B8").toFloat()
    b11 = (
        image.select("B11")
        .resample("bilinear")
        .reproject(crs="EPSG:4326", scale=10)
        .toFloat()
    )
    b12 = (
        image.select("B12")
        .resample("bilinear")
        .reproject(crs="EPSG:4326", scale=10)
        .toFloat()
    )

    ndvi = b8.subtract(b4).divide(b8.add(b4)).rename("NDVI").toFloat()
    ndbi = b11.subtract(b8).divide(b11.add(b8)).rename("NDBI").toFloat()

    final_image = ee.Image.cat(
        [
            b2.rename("B2"),
            b3.rename("B3"),
            b4.rename("B4"),
            b8.rename("B8"),
            b11.rename("B11"),
            b12.rename("B12"),
            ndvi,
            ndbi,
        ]
    )

    print("[*] Bands: B2, B3, B4, B8, B11, B12, NDVI, NDBI (all Float32, 10m)")
    print(f"[*] Downloading to: {output_path}")

    url = final_image.getDownloadURL(
        {
            "region": region,
            "scale": 10,
            "format": "GEO_TIFF",
            "bands": ["B2", "B3", "B4", "B8", "B11", "B12", "NDVI", "NDBI"],
        }
    )

    response = requests.get(url, stream=True)
    if response.status_code != 200:
        raise RuntimeError(f"Download failed: {response.status_code}")

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print("[OK] Download complete!")

    with rasterio.open(output_path) as src:
        return {
            "width": src.width,
            "height": src.height,
            "bands": src.count,
            "resolution": f"{src.res[0]}m",
            "band_order": ["B2", "B3", "B4", "B8", "B11", "B12", "NDVI", "NDBI"],
        }


def fetch_rgb_geotiff(bounds, start_date, end_date, max_cloud_cover, output_path):
    """Fetch RGB (B4, B3, B2) Sentinel-2 median composite as GeoTIFF."""
    min_lon = bounds["minLon"]
    min_lat = bounds["minLat"]
    max_lon = bounds["maxLon"]
    max_lat = bounds["maxLat"]

    region = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])
    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud_cover))
    )

    count = collection.size().getInfo()
    if count == 0:
        raise FileNotFoundError(
            f"No images found with <{max_cloud_cover}% cloud cover"
        )

    print(f"[OK] Found {count} images")
    image = collection.median()

    rgb_image = ee.Image.cat(
        [
            image.select("B4").toFloat(),
            image.select("B3").toFloat(),
            image.select("B2").toFloat(),
        ]
    )

    url = rgb_image.getDownloadURL(
        {"region": region, "scale": 10, "format": "GEO_TIFF"}
    )

    response = requests.get(url, stream=True)
    if response.status_code != 200:
        raise RuntimeError(f"Download failed: {response.status_code}")

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print("[OK] Download complete!")
