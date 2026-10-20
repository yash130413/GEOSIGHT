"""
Shared fixtures for backend tests.

Earth Engine is replaced with stubs so the tests run offline. Tests that need
the real land-cover model are skipped when the checkpoint is not available
(set GEOSIGHT_CHECKPOINT to its path to enable them).
"""
import os
import sys

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

DEFAULT_CHECKPOINT = os.path.join(REPO_ROOT, "checkpoints", "geosight_final_epoch_11.pt")
CHECKPOINT = os.environ.get("GEOSIGHT_CHECKPOINT", DEFAULT_CHECKPOINT)


@pytest.fixture(scope="session")
def backend_app():
    """Import backend/app.py with Earth Engine stubbed out."""
    import ee
    ee.Initialize = lambda *a, **k: None
    ee.Authenticate = lambda *a, **k: None
    import app as app_module
    return app_module


@pytest.fixture(scope="session")
def real_model(backend_app):
    if not os.path.exists(CHECKPOINT):
        pytest.skip(f"Checkpoint not found: {CHECKPOINT}")
    from predict import load_model
    return load_model(CHECKPOINT)


@pytest.fixture
def client(backend_app, tmp_path, monkeypatch):
    monkeypatch.setattr(backend_app, "OUTPUT_DIR", str(tmp_path))
    backend_app.app.config["TESTING"] = True
    return backend_app.app.test_client()


def write_geotiff(path, bands, height=64, width=64, seed=0):
    """Write a synthetic Sentinel-2-like GeoTIFF (reflectance 0-10000)."""
    rng = np.random.default_rng(seed)
    data = rng.integers(200, 4000, size=(bands, height, width)).astype(np.float32)
    with rasterio.open(
        path, "w", driver="GTiff", height=height, width=width, count=bands,
        dtype="float32", crs="EPSG:4326", transform=from_origin(77.0, 28.7, 0.0001, 0.0001),
    ) as dst:
        dst.write(data)
    return path
