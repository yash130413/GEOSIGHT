"""Phase 2: configuration via environment variables and graceful startup."""
import json
import os
import subprocess
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

# Imports app.py in a fresh interpreter (module-level config is read at import),
# with Earth Engine either stubbed to succeed or to fail, then calls endpoints.
PROBE = r'''
import json, sys, io
import ee
def fail(*a, **k): raise Exception("no credentials")
ee.Initialize = (lambda *a, **k: None) if sys.argv[1] == "ok" else fail
ee.Authenticate = lambda *a, **k: (_ for _ in ()).throw(AssertionError("server must never prompt for login"))
import app
c = app.app.test_client()
body = {"bounds": {"minLon": 77.0, "minLat": 28.5, "maxLon": 77.1, "maxLat": 28.6}}
tif = open(sys.argv[2], "rb").read()
out = {
    "project": app.PROJECT_ID,
    "output_dir": app.OUTPUT_DIR,
    "model_path": app.MODEL_PATH,
    "health": c.get("/api/health").get_json(),
    "fetch": [c.post("/api/fetch-image", json=body).status_code],
    "roads": [c.post("/api/detect-roads", json=body).status_code],
}
r = c.post("/api/predict-upload", data={"file": (io.BytesIO(tif), "x.tif")}, content_type="multipart/form-data")
out["upload"] = [r.status_code, r.get_json()]
r = c.post("/api/fetch-image", json=body)
out["fetch"].append(r.get_json())
print("PROBE" + json.dumps(out))
'''


def run_probe(tmp_path, ee_mode, extra_env):
    from conftest import write_geotiff
    tif = write_geotiff(tmp_path / "probe.tif", bands=6)
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **extra_env}
    proc = subprocess.run(
        [sys.executable, "-c", PROBE, ee_mode, str(tif)],
        cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=300,
    )
    line = next((l for l in proc.stdout.splitlines() if l.startswith("PROBE")), None)
    assert line, proc.stdout[-2000:] + proc.stderr[-2000:]
    return json.loads(line[len("PROBE"):])


def test_missing_checkpoints_and_no_earth_engine_still_start(tmp_path):
    out = run_probe(tmp_path, "fail", {
        "GEOSIGHT_MODEL_PATH": str(tmp_path / "nope.pt"),
        "GEOSIGHT_ROAD_MODEL_PATH": str(tmp_path / "nope_road.pt"),
        "GEOSIGHT_OUTPUT_DIR": str(tmp_path / "outputs"),
        "GEOSIGHT_EE_PROJECT": "my-test-project",
    })
    # Settings come from the environment
    assert out["project"] == "my-test-project"
    assert out["output_dir"] == str(tmp_path / "outputs")
    assert os.path.isdir(tmp_path / "outputs")

    # Server is up and reports what is missing
    assert out["health"]["status"] == "ok"
    assert out["health"]["earth_engine"] == "not configured"
    assert out["health"]["classification_model"] == "missing"
    assert out["health"]["road_model"] == "missing"

    # Earth Engine endpoints refuse clearly instead of crashing
    assert out["fetch"][0] == 503
    assert out["roads"][0] == 503
    assert "Earth Engine" in out["fetch"][1]["error"]

    # Upload explains where the checkpoint should be
    status, body = out["upload"]
    assert status == 503
    assert "nope.pt" in body["error"] and "GEOSIGHT_MODEL_PATH" in body["error"]


def test_default_paths_point_inside_repo(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GEOSIGHT_")}
    out = run_probe(tmp_path, "ok", {**env, "GEOSIGHT_OUTPUT_DIR": str(tmp_path / "o")})
    repo = os.path.dirname(BACKEND_DIR)
    assert out["model_path"] == os.path.join(repo, "checkpoints", "geosight_final_epoch_11.pt")
    assert out["project"] == "gen-lang-client-0871361958"
    assert out["health"]["earth_engine"] == "connected"
