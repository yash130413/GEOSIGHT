import warnings
warnings.filterwarnings('ignore')

import numpy as np

import os
# Folder holding the datasets and outputs (formerly a personal Desktop path).
# Set GEOSIGHT_DATA_ROOT to use another location; defaults to the repository root.
DATA_ROOT = os.environ.get("GEOSIGHT_DATA_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

img_path = os.path.join(DATA_ROOT, "image", "UK_tiles_labeled", "tile_316.tif")

try:
    import rasterio
    with rasterio.open(img_path) as src:
        print(f'Rasterio shape (h, w): {src.shape}, count (bands): {src.count}')
        print("\n--- Summary of 8 Bands (rasterio) ---")
        for i in range(1, src.count + 1):
            band = src.read(i)
            unique_vals = np.unique(band)
            if len(unique_vals) <= 15:
                print(f"Band {i}: min={band.min()}, max={band.max()}, UNIQUE VALUES={unique_vals}")
            else:
                print(f"Band {i}: min={band.min()}, max={band.max()}, mean={band.mean():.2f}")
except Exception as e:
    print("rasterio failed:", e)
    try:
        import tifffile
        img = tifffile.imread(img_path)
        print(f'Shape of the loaded image (tifffile): {img.shape}')
        
        if 8 in img.shape:
            bands_dim = img.shape.index(8)
            img_multi = np.moveaxis(img, bands_dim, 0)
            
            print("\n--- Summary of 8 Bands (tifffile) ---")
            for i in range(8):
                band = img_multi[i]
                unique_vals = np.unique(band)
                if len(unique_vals) <= 15:
                    print(f"Band {i+1}: min={band.min()}, max={band.max()}, UNIQUE VALUES={unique_vals}")
                else:
                    print(f"Band {i+1}: min={band.min()}, max={band.max()}, mean={band.mean():.2f}")
    except Exception as e2:
        print("Both failed.")
