import os
import rasterio, numpy as np, glob, torch, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'backend'))
from predict_roads import RoadSegmentationModel, load_road_model

# Folder holding the datasets and outputs (formerly a machine-specific drive path).
# Set GEOSIGHT_DATA_ROOT to use another location; defaults to the repository root.
DATA_ROOT = os.environ.get("GEOSIGHT_DATA_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

files = glob.glob(os.path.join(DATA_ROOT, "backend_outputs", "road_input*.tif"))
with rasterio.open(files[-1]) as src:
    img = src.read()[:3].astype(np.float32)

print('Raw min/max:', img.min(), img.max())
print('Raw mean:', img.mean())

model = load_road_model(os.path.join(DATA_ROOT, "Models", "GeoSight_RoadExpert_Final_PyTorch.pt"), device='cpu')

# Test different normalizations
norms = {
    'minmax': (img - img.min()) / (img.max() - img.min() + 1e-8),
    'div10000': np.clip(img / 10000.0, 0, 1),
    'div255': np.clip(img / 255.0, 0, 1),
    'imagenet': (img / 10000.0),  # then imagenet stats
}

for name, norm_img in norms.items():
    t = torch.from_numpy(norm_img).unsqueeze(0)
    with torch.no_grad():
        out = model(t)
        sig = torch.sigmoid(out)
        road_pct = (sig > 0.5).float().mean().item() * 100
        print(f'{name}: sigmoid range [{sig.min():.3f}, {sig.max():.3f}], road%={road_pct:.1f}%')
