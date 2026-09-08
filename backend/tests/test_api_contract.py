"""
API contract smoke tests.

These hit a live server if GEOSIGHT_API_BASE is set; otherwise they are skipped.
Example:
  set GEOSIGHT_API_BASE=http://localhost:5000
  pytest backend/tests/test_api_contract.py -q
"""
import os

import pytest

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

BASE = os.getenv("GEOSIGHT_API_BASE")


@pytest.mark.skipif(not BASE or requests is None, reason="Live API not configured")
def test_health_contract():
    res = requests.get(f"{BASE}/api/health", timeout=10)
    assert res.status_code == 200
    body = res.json()
    assert body.get("status") == "ok"
    assert "message" in body


@pytest.mark.skipif(not BASE or requests is None, reason="Live API not configured")
def test_fetch_image_requires_bounds():
    res = requests.post(f"{BASE}/api/fetch-image", json={}, timeout=10)
    assert res.status_code == 400
    assert "error" in res.json()
