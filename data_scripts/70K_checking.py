import os
import rasterio
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
# Folder holding the datasets and outputs (formerly a machine-specific drive path).
# Set GEOSIGHT_DATA_ROOT to use another location; defaults to the repository root.
DATA_ROOT = os.environ.get("GEOSIGHT_DATA_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


folders = [
    os.path.join(DATA_ROOT, "Delhi_tiles_8band_overlap_50"), 
    os.path.join(DATA_ROOT, "Haryana_all_combined_tif_tiles"),
    os.path.join(DATA_ROOT, "Kanpur_tiles_8band_overlap_50"),
    os.path.join(DATA_ROOT, "Sikkim_tiles_8band_overlap_50pct_clean"),
    os.path.join(DATA_ROOT, "UK_tiles_all_tif")
]

def analyze_tile(file_info):
    folder, filename = file_info
    path = os.path.join(folder, filename)
    try:
        with rasterio.open(path) as src:
            # Read only the 4 bands we need for identification (B2, B3, B4, B6)
            data = src.read([2, 3, 4, 6]).astype('float32')
            
            # 1. Reject tiles with too many NaNs
            if np.isnan(data).mean() > 0.15: 
                return None

            # 2. Calculate Spectral Signatures
            # Band 2=Green, 3=Red, 4=NIR, 6=SWIR
            green, red, nir, swir = data[0], data[1], data[2], data[3]
            
            # Mean Indices (using epsilon to avoid div by zero)
            eps = 1e-6
            ndvi = np.nanmean((nir - red) / (nir + red + eps))
            ndbi = np.nanmean((swir - nir) / (swir + nir + eps))
            ndwi = np.nanmean((green - nir) / (green + nir + eps))

            return {
                'filename': filename,
                'state': os.path.basename(folder).split('_')[0],
                'ndvi': ndvi, 'ndbi': ndbi, 'ndwi': ndwi,
                'path': path
            }
    except:
        return None

if __name__ == "__main__":
    all_tasks = []
    for fld in folders:
        all_tasks.extend([(fld, f) for f in os.listdir(fld) if f.endswith('.tif')])

    print(f"Scanning {len(all_tasks)} images...")
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(tqdm(executor.map(analyze_tile, all_tasks), total=len(all_tasks)))

    df = pd.DataFrame([r for r in results if r is not None])
    df.to_csv('geosight_manifest_70k.csv', index=False)
    print(f"Success! {len(df)} valid tiles cataloged.")