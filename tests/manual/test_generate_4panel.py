"""
Test 4-panel generation with existing TIF file
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'backend'))

from generate_4panel import generate_4panel
from predict import load_model
# Folder holding the datasets and outputs (formerly a machine-specific drive path).
# Set GEOSIGHT_DATA_ROOT to use another location; defaults to the repository root.
DATA_ROOT = os.environ.get("GEOSIGHT_DATA_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


# Find a test TIF file
test_files = [
    os.path.join(DATA_ROOT, "data", "train", "images", "sample_01_tile_0001.tif"),
    os.path.join(DATA_ROOT, "data", "train", "images", "sample_01_tile_0002.tif"),
    os.path.join(DATA_ROOT, "data", "train", "images", "sample_01_tile_0003.tif"),
]

# Find first existing file
test_tif = None
for f in test_files:
    if os.path.exists(f):
        test_tif = f
        break

if not test_tif:
    print("[ERROR] No test TIF files found!")
    print("Please provide path to a 6-band GeoTIFF file")
    sys.exit(1)

print("=" * 60)
print("TESTING 4-PANEL GENERATION")
print("=" * 60)
print(f"\n[*] Using test file: {test_tif}")

# Load model
MODEL_PATH = os.path.join(DATA_ROOT, "checkpoints", "geosight_final_epoch_11.pt")
print(f"[*] Loading model from: {MODEL_PATH}")

if not os.path.exists(MODEL_PATH):
    print(f"[ERROR] Model not found at: {MODEL_PATH}")
    sys.exit(1)

try:
    model = load_model(MODEL_PATH)
    print("[OK] Model loaded successfully")
except Exception as e:
    print(f"[ERROR] Failed to load model: {e}")
    sys.exit(1)

# Generate 4-panel
output_path = os.path.join(DATA_ROOT, "backend_outputs", "test_4panel.png")
print(f"\n[*] Generating 4-panel...")
print(f"[*] Output: {output_path}")

try:
    generate_4panel(model, test_tif, output_path)
    
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        print(f"\n[OK] SUCCESS! 4-panel generated")
        print(f"[OK] File: {output_path}")
        print(f"[OK] Size: {size:,} bytes")
        print(f"\n[*] You can view it at: {output_path}")
    else:
        print(f"\n[ERROR] File was not created!")
        
except Exception as e:
    print(f"\n[ERROR] Failed to generate 4-panel: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
