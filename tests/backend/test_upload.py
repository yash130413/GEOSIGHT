"""Phase 1: /api/predict-upload must return real model output or a clear error."""
import io

import pytest
from predict import predict_image

from conftest import write_geotiff


def upload(client, data, filename):
    return client.post(
        "/api/predict-upload",
        data={"file": (io.BytesIO(data), filename)},
        content_type="multipart/form-data",
    )


@pytest.mark.parametrize("bands", [6, 8])
def test_valid_geotiff_returns_real_prediction(client, backend_app, real_model, monkeypatch, tmp_path, bands):
    monkeypatch.setattr(backend_app, "model", real_model)
    tif = write_geotiff(tmp_path / "input.tif", bands=bands)

    res = upload(client, tif.read_bytes(), "my image.tif")
    assert res.status_code == 200, res.get_json()
    body = res.get_json()

    pred = body["prediction"]
    assert pred["dominant_class"] in {"Background", "Rural", "Urban", "Water"}
    assert sum(c["percentage"] for c in pred["class_distribution"].values()) == pytest.approx(100, abs=0.1)
    assert body["info"]["bands"] == bands
    assert body["file"].startswith("upload_my_image_")  # filename sanitised

    # Same numbers as calling the model directly -> the response is real inference
    direct = predict_image(real_model, str(tmp_path / body["file"]))
    assert pred["class_distribution"] == direct["class_distribution"]

    # 4-panel image was generated and can be downloaded
    assert body["visualization_4panel"]
    assert (tmp_path / body["visualization_4panel"]).exists()


def test_repeated_uploads_get_separate_results(client, backend_app, real_model, monkeypatch, tmp_path):
    monkeypatch.setattr(backend_app, "model", real_model)
    a = upload(client, write_geotiff(tmp_path / "a.tif", 6, seed=1).read_bytes(), "a.tif").get_json()
    b = upload(client, write_geotiff(tmp_path / "b.tif", 6, seed=2).read_bytes(), "b.tif").get_json()
    assert a["file"] != b["file"]


@pytest.mark.parametrize("filename", ["photo.jpg", "photo.png", "notes.txt"])
def test_non_geotiff_extensions_rejected(client, filename):
    res = upload(client, b"\x89PNG fake image bytes", filename)
    assert res.status_code == 400
    assert "GeoTIFF" in res.get_json()["error"]


def test_three_band_geotiff_rejected(client, tmp_path):
    tif = write_geotiff(tmp_path / "rgb.tif", bands=3)
    res = upload(client, tif.read_bytes(), "rgb.tif")
    assert res.status_code == 400
    assert "needs 6" in res.get_json()["error"]


def test_empty_file_rejected(client):
    res = upload(client, b"", "empty.tif")
    assert res.status_code == 400


def test_malformed_tif_rejected(client):
    res = upload(client, b"this is not a tiff at all", "broken.tif")
    assert res.status_code == 400
    assert "valid GeoTIFF" in res.get_json()["error"]


def test_missing_file_field_rejected(client):
    res = client.post("/api/predict-upload", data={}, content_type="multipart/form-data")
    assert res.status_code == 400


def test_model_not_loaded_returns_503_not_fake_result(client, backend_app, monkeypatch, tmp_path):
    monkeypatch.setattr(backend_app, "model", None)
    tif = write_geotiff(tmp_path / "x.tif", bands=6)
    res = upload(client, tif.read_bytes(), "x.tif")
    assert res.status_code == 503
    assert "prediction" not in res.get_json()
