"""
Phase 4: the rebuilt training script, the evaluation script and the backend
must agree on architecture, preprocessing, output size and class meaning.
"""
import glob
import os
import sys

import numpy as np
import pytest
import rasterio
import torch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for sub in ("backend", "Training", os.path.join("tests", "backend")):
    sys.path.insert(0, os.path.join(ROOT, sub))

import train_unetpp_6band as train            # noqa: E402
import evaluate_models                        # noqa: E402
import predict                                # noqa: E402
import predict_roads                          # noqa: E402
from conftest import write_geotiff, CHECKPOINT  # noqa: E402

CHECKPOINT_DIR = os.path.dirname(CHECKPOINT)
needs_checkpoint = pytest.mark.skipif(not os.path.exists(CHECKPOINT), reason=f"no checkpoint at {CHECKPOINT}")


def test_class_order_is_the_same_everywhere():
    assert [predict.CLASS_NAMES[i] for i in range(4)] == evaluate_models.CLASSIFICATION_CLASSES
    assert train.NUM_CLASSES == 4 and train.IN_CHANNELS == 6


@needs_checkpoint
def test_every_saved_epoch_loads_into_training_architecture():
    ckpts = sorted(glob.glob(os.path.join(CHECKPOINT_DIR, "geosight_final_epoch_*.pt")))
    assert ckpts
    for path in ckpts:
        model = train.build_model(encoder_weights=None)
        model.load_state_dict(torch.load(path, map_location="cpu"), strict=True)


def test_training_and_backend_preprocessing_match(tmp_path):
    tif = write_geotiff(tmp_path / "t_1.tif", bands=8, height=64, width=64)
    mask = np.zeros((1, 64, 64), dtype=np.uint8)
    with rasterio.open(tmp_path / "t_1_mask.tif", "w", driver="GTiff", height=64, width=64,
                       count=1, dtype="uint8") as dst:
        dst.write(mask)

    ds = train.GeoSightDataset(str(tmp_path), str(tmp_path), ["t_1.tif"], transform=train.val_transform)
    train_tensor, _ = ds[0]

    with rasterio.open(tif) as src:   # exactly what backend/predict.py does
        backend = np.nan_to_num(np.clip(src.read([1, 2, 3, 4, 5, 6]).astype(np.float32) / 10000.0, 0, 1),
                                nan=0.0, posinf=1.0, neginf=0.0)
    assert train_tensor.shape == (6, 64, 64)
    np.testing.assert_array_equal(train_tensor.numpy(), backend)


@needs_checkpoint
def test_backend_prediction_equals_training_pipeline_forward(tmp_path):
    tif = write_geotiff(tmp_path / "x.tif", bands=6, height=70, width=90)   # not a multiple of 32
    model = predict.load_model(CHECKPOINT)
    result = predict.predict_image(model, str(tif))
    assert result["image_size"] == {"width": 90, "height": 70}
    assert result["total_pixels"] == 70 * 90

    image = predict.np.clip(rasterio.open(tif).read([1, 2, 3, 4, 5, 6]).astype(np.float32) / 10000.0, 0, 1)
    padded = np.pad(image, ((0, 0), (0, 96 - 70), (0, 96 - 90)), mode="reflect")
    with torch.no_grad():
        logits = model(torch.from_numpy(padded).unsqueeze(0).to(predict.device))[0, :, :70, :90]
    pred = logits.argmax(0).cpu().numpy()
    for i, name in predict.CLASS_NAMES.items():
        assert result["class_distribution"][name]["pixels"] == int((pred == i).sum())


def test_road_preprocessing_matches_between_backend_and_evaluation(tmp_path):
    # Training/evaluation read bands 3,2,1 (B4,B3,B2) of an 8-band tile;
    # the backend downloads B4,B3,B2 directly and reads bands 1,2,3.
    tile = write_geotiff(tmp_path / "tile.tif", bands=8, height=200, width=180)
    with rasterio.open(tile) as src:
        rgb, profile = src.read([3, 2, 1]), src.profile
    profile.update(count=3)
    with rasterio.open(tmp_path / "rgb.tif", "w", **profile) as dst:
        dst.write(rgb)

    backend_input, _ = predict_roads._preprocess(str(tmp_path / "rgb.tif"))

    import cv2
    img = rasterio.open(tile).read([3, 2, 1]).transpose(1, 2, 0).astype(np.float32)
    img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    img = cv2.resize(img, (256, 256))
    eval_input = (np.transpose(img.astype(np.float32) / 255.0, (2, 0, 1)) - evaluate_models.IMAGENET_MEAN) \
        / evaluate_models.IMAGENET_STD
    assert backend_input.shape == (3, 256, 256)
    np.testing.assert_allclose(backend_input, eval_input, rtol=1e-6)
