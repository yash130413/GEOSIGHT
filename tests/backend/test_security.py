"""Phase 3: security defaults, download path safety, CORS and input validation."""
import json
import os
import subprocess
import sys

import pytest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
VALID_BOUNDS = {"minLon": 77.20, "minLat": 28.60, "maxLon": 77.22, "maxLat": 28.62}


# ---------------------------------------------------------------- startup defaults
RUN_MAIN = r'''
import json, runpy, ee, flask
ee.Initialize = lambda *a, **k: None
flask.Flask.run = lambda self, **kw: print("RUN" + json.dumps(kw))
runpy.run_path("app.py", run_name="__main__")
'''


def run_main(extra_env):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GEOSIGHT_")}
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "GEOSIGHT_MODEL_PATH": "missing.pt",
                "GEOSIGHT_ROAD_MODEL_PATH": "missing.pt", **extra_env})
    proc = subprocess.run([sys.executable, "-c", RUN_MAIN], cwd=BACKEND_DIR, env=env,
                          capture_output=True, text=True, timeout=300)
    line = next(l for l in proc.stdout.splitlines() if l.startswith("RUN"))
    return json.loads(line[3:]), proc.stdout


def test_defaults_are_local_only_and_debug_off():
    kwargs, _ = run_main({})
    assert kwargs == {"debug": False, "host": "127.0.0.1", "port": 5000}


def test_network_and_debug_need_explicit_opt_in():
    kwargs, stdout = run_main({"GEOSIGHT_HOST": "0.0.0.0", "GEOSIGHT_PORT": "8080", "GEOSIGHT_DEBUG": "1"})
    assert kwargs == {"debug": True, "host": "0.0.0.0", "port": 8080}
    assert "reachable from other computers" in stdout


# ---------------------------------------------------------------- downloads
@pytest.fixture
def files(backend_app, tmp_path, monkeypatch):
    out = tmp_path / "outputs"
    out.mkdir()
    (out / "result.png").write_bytes(b"\x89PNG inside")
    (out / "result.tif").write_bytes(b"II*\x00 inside")
    (tmp_path / "secret.png").write_bytes(b"TOP SECRET")
    (tmp_path / "secret.tif").write_bytes(b"TOP SECRET")
    monkeypatch.setattr(backend_app, "OUTPUT_DIR", str(out))
    return backend_app.app.test_client()


def test_files_inside_output_dir_are_served(files):
    png = files.get("/api/download/result.png")
    assert png.status_code == 200 and png.data == b"\x89PNG inside"
    assert png.mimetype == "image/png"
    tif = files.get("/api/download/result.tif")
    assert tif.status_code == 200 and "attachment" in tif.headers["Content-Disposition"]


@pytest.mark.parametrize("name", [
    "..%5Csecret.png",            # Windows-style  ..\secret.png
    "..%2Fsecret.png",            # Unix-style     ../secret.png
    "%2E%2E%5Csecret.tif",        # encoded dots
    "..%5C..%5Csecret.png",
    "outputs%5C..%5C..%5Csecret.png",
    "C:%5CWindows%5Cwin.ini%00.png",
    "%5C%5Cserver%5Cshare%5Cx.png",
])
def test_path_traversal_is_blocked(files, name):
    res = files.get(f"/api/download/{name}")
    assert res.status_code in (400, 404)
    assert b"TOP SECRET" not in res.data


@pytest.mark.parametrize("name", ["app.py", "pytest.ini", "result.exe", "notes.txt"])
def test_only_png_and_tif_can_be_downloaded(files, name):
    assert files.get(f"/api/download/{name}").status_code == 400


# ---------------------------------------------------------------- CORS
def test_cors_allows_frontend_origin(client):
    res = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert res.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    pre = client.options("/api/fetch-image", headers={
        "Origin": "http://127.0.0.1:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    })
    assert pre.headers.get("Access-Control-Allow-Origin") == "http://127.0.0.1:5173"


@pytest.mark.parametrize("origin", ["https://evil.example", "http://localhost:5174", "null"])
def test_cors_rejects_other_origins(client, origin):
    res = client.get("/api/health", headers={"Origin": origin})
    assert "Access-Control-Allow-Origin" not in res.headers


# ---------------------------------------------------------------- input validation
@pytest.mark.parametrize("body,fragment", [
    ({}, "Missing bounds"),
    ({"bounds": "77,28,78,29"}, "Missing bounds"),
    ({"bounds": {**VALID_BOUNDS, "minLon": "abc"}}, "minLon must be a number"),
    ({"bounds": {**VALID_BOUNDS, "maxLat": None}}, "maxLat must be a number"),
    ({"bounds": {**VALID_BOUNDS, "minLat": True}}, "minLat must be a number"),
    ({"bounds": {"minLon": 77.22, "minLat": 28.60, "maxLon": 77.20, "maxLat": 28.62}}, "minLon < maxLon"),
    ({"bounds": {"minLon": 77.20, "minLat": 28.62, "maxLon": 77.22, "maxLat": 28.60}}, "minLat < maxLat"),
    ({"bounds": {**VALID_BOUNDS, "maxLon": 190}}, "Longitude"),
    ({"bounds": {**VALID_BOUNDS, "minLat": -95}}, "Latitude"),
    ({"bounds": {"minLon": 77.0, "minLat": 28.0, "maxLon": 78.0, "maxLat": 29.0}}, "too large"),
    ({"bounds": VALID_BOUNDS, "cloudCover": 150}, "cloudCover"),
    ({"bounds": VALID_BOUNDS, "cloudCover": "ten"}, "cloudCover"),
    ({"bounds": VALID_BOUNDS, "startDate": "01-01-2024"}, "YYYY-MM-DD"),
    ({"bounds": VALID_BOUNDS, "startDate": "2024-12-31", "endDate": "2024-01-01"}, "after endDate"),
])
@pytest.mark.parametrize("endpoint", ["/api/fetch-image", "/api/detect-roads"])
def test_invalid_requests_rejected(client, endpoint, body, fragment):
    res = client.post(endpoint, json=body)
    assert res.status_code == 400
    assert fragment in res.get_json()["error"]


@pytest.mark.parametrize("endpoint", ["/api/fetch-image", "/api/detect-roads"])
def test_malformed_json_rejected_without_parser_details(client, endpoint):
    res = client.post(endpoint, data="{bad json", content_type="application/json")
    assert res.status_code == 400
    assert res.get_json() == {"error": "Request body must be a JSON object"}


def test_valid_request_passes_validation(client, backend_app, monkeypatch):
    # Earth Engine is stubbed, so the first real EE call fails -> mapped to 502, not 400
    seen = {}

    class FakeGeometry:
        @staticmethod
        def Rectangle(coords):
            seen["coords"] = coords
            raise backend_app.ee.EEException("quota exceeded")

    monkeypatch.setattr(backend_app.ee, "Geometry", FakeGeometry)
    res = client.post("/api/fetch-image", json={"bounds": VALID_BOUNDS})
    assert seen["coords"] == [77.20, 28.60, 77.22, 28.62]
    assert res.status_code == 502
    assert res.get_json()["error"] == "Earth Engine error: quota exceeded"


def test_unexpected_errors_do_not_leak_internals(client, backend_app, monkeypatch):
    class Boom:
        @staticmethod
        def Rectangle(coords):
            raise RuntimeError(r"C:\Users\someone\secret\path.tif exploded")

    monkeypatch.setattr(backend_app.ee, "Geometry", Boom)
    for endpoint in ("/api/fetch-image", "/api/detect-roads"):
        res = client.post(endpoint, json={"bounds": VALID_BOUNDS})
        assert res.status_code == 500
        text = json.dumps(res.get_json())
        assert "secret" not in text and "Traceback" not in text and "C:\\\\" not in text


def test_unknown_routes_and_methods_return_json(client):
    assert client.get("/api/nope").get_json() == {"error": "Not found"}
    assert client.get("/api/fetch-image").status_code == 405
