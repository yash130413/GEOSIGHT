"""Phase 4: shared Earth Engine helpers and offline end-to-end tests of both EE endpoints."""
import re
import shutil

import pytest

from conftest import write_geotiff

BODY = {"bounds": {"minLon": 77.20, "minLat": 28.60, "maxLon": 77.22, "maxLat": 28.62},
        "cloudCover": 15, "startDate": "2024-01-01", "endDate": "2024-06-30"}


class FakeCollection:
    """Records the filters the code applies; size() returns the given scene count."""

    def __init__(self, log, count):
        self.log, self.count = log, count

    def filterBounds(self, region):
        self.log["region"] = region
        return self

    def filterDate(self, start, end):
        self.log["dates"] = (start, end)
        return self

    def filter(self, f):
        self.log["filter"] = f
        return self

    def size(self):
        return type("N", (), {"getInfo": lambda _s: self.count})()

    def median(self):
        return FakeImage()


class FakeImage:
    """Stand-in for ee.Image: every operation returns itself."""

    def __getattr__(self, name):
        return lambda *a, **k: self

    def getDownloadURL(self, params):
        FakeImage.last_params = params
        return "https://earthengine.example/download"


@pytest.fixture
def fake_ee(backend_app, monkeypatch):
    log = {"count": 3}
    ee = backend_app.ee
    monkeypatch.setattr(ee.Geometry, "Rectangle", staticmethod(lambda coords: ("rect", tuple(coords))))
    monkeypatch.setattr(ee, "ImageCollection", lambda name: FakeCollection(log, log["count"]))
    monkeypatch.setattr(ee.Filter, "lt", staticmethod(lambda prop, v: ("lt", prop, v)))
    monkeypatch.setattr(ee.Image, "cat", staticmethod(lambda bands: FakeImage()))
    return log


@pytest.fixture
def fake_download(backend_app, monkeypatch, tmp_path):
    """requests.get returns the bytes of a synthetic GeoTIFF with the requested band count."""
    state = {"status": 200, "bands": 8}

    class Resp:
        def __init__(self, data, status):
            self.data, self.status_code = data, status

        def iter_content(self, chunk_size):
            yield self.data

    def get(url, stream, timeout):
        state["timeout"] = timeout
        src = write_geotiff(tmp_path / "src.tif", bands=state["bands"], height=96, width=96)
        return Resp(src.read_bytes(), state["status"])

    monkeypatch.setattr(backend_app.requests, "get", get)
    return state


def test_median_composite_applies_request_filters(backend_app, fake_ee):
    params = {"bounds": (77.2, 28.6, 77.22, 28.62), "cloud_cover": 15,
              "start_date": "2024-01-01", "end_date": "2024-06-30"}
    region, image = backend_app.get_median_composite(params)
    assert region == ("rect", (77.2, 28.6, 77.22, 28.62))
    assert image is not None
    assert fake_ee["dates"] == ("2024-01-01", "2024-06-30")
    assert fake_ee["filter"] == ("lt", "CLOUDY_PIXEL_PERCENTAGE", 15)


def test_median_composite_none_when_no_scenes(backend_app, fake_ee):
    fake_ee["count"] = 0
    _, image = backend_app.get_median_composite(
        {"bounds": (0, 0, 0.01, 0.01), "cloud_cover": 1, "start_date": "2024-01-01", "end_date": "2024-01-02"})
    assert image is None


def test_output_name_has_coordinates_and_timestamp(backend_app):
    name = backend_app.output_name({"bounds": (77.209, 28.613, 77.3, 28.7)})
    assert re.fullmatch(r"lat28\.61_lon77\.21_\d{8}_\d{6}", name)


def test_download_failure_raises_earth_engine_error(backend_app, fake_download, tmp_path):
    fake_download["status"] = 500
    with pytest.raises(backend_app.ee.EEException):
        backend_app.download_geotiff(FakeImage(), "region", str(tmp_path / "x.tif"))


def test_fetch_image_end_to_end(client, backend_app, real_model, monkeypatch, fake_ee, fake_download, tmp_path):
    monkeypatch.setattr(backend_app, "model", real_model)
    res = client.post("/api/fetch-image", json=BODY)
    assert res.status_code == 200, res.get_json()
    body = res.get_json()
    assert FakeImage.last_params["bands"] == ["B2", "B3", "B4", "B8", "B11", "B12", "NDVI", "NDBI"]
    assert FakeImage.last_params["scale"] == 10
    assert fake_download["timeout"] == 300
    assert body["info"]["bands"] == 8 and body["info"]["band_order"][0] == "B2"
    assert body["prediction"]["dominant_class"] in {"Background", "Rural", "Urban", "Water"}
    assert body["file"].startswith("sentinel2_lat28.60_lon77.20_")
    assert (tmp_path / body["visualization_4panel"]).exists()
    assert "path" not in body


def test_fetch_image_no_scenes_returns_404(client, fake_ee):
    fake_ee["count"] = 0
    res = client.post("/api/fetch-image", json=BODY)
    assert res.status_code == 404
    assert "suggestion" in res.get_json()


def test_fetch_image_without_model_reports_prediction_error(client, backend_app, monkeypatch, fake_ee, fake_download):
    monkeypatch.setattr(backend_app, "model", None)
    res = client.post("/api/fetch-image", json=BODY)
    assert res.status_code == 200
    assert "prediction" not in res.get_json() and res.get_json()["prediction_error"]


def test_detect_roads_end_to_end(client, backend_app, monkeypatch, fake_ee, fake_download, tmp_path):
    road_ckpt = backend_app.ROAD_MODEL_PATH
    if backend_app.road_model is None:
        pytest.skip(f"Road checkpoint not available: {road_ckpt}")
    fake_download["bands"] = 3
    res = client.post("/api/detect-roads", json=BODY)
    assert res.status_code == 200, res.get_json()
    body = res.get_json()
    assert "bands" not in FakeImage.last_params      # RGB image downloaded as-is
    det = body["road_detection"]
    assert det["total_pixels"] == 256 * 256          # model works on 256x256 tiles
    assert 0 <= det["road_percentage"] <= 100
    assert (tmp_path / body["visualization"]).exists()
