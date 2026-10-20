import torch
import os
# Folder holding the datasets and outputs (formerly a machine-specific drive path).
# Set GEOSIGHT_DATA_ROOT to use another location; defaults to the repository root.
DATA_ROOT = os.environ.get("GEOSIGHT_DATA_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

sd = torch.load(os.path.join(DATA_ROOT, "Models", "GeoSight_RoadExpert_Final_PyTorch.pt"), map_location='cpu', weights_only=False)
print('TOP LEVEL TYPE:', type(sd))
if isinstance(sd, dict):
    print('TOP KEYS:', list(sd.keys())[:5])
    inner = sd.get('model', sd.get('state_dict', sd))
else:
    inner = sd
keys = list(inner.keys())
print('TOTAL KEYS:', len(keys))
for k in keys[:30]:
    print(k, '->', inner[k].shape)
