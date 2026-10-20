"""
GeoSight - Model evaluation script
==================================

Measures how well the trained models agree with the ground-truth masks on
the held-out validation tiles, and saves the results for the website's
"Model Insights" page.

It produces REAL metrics (nothing is estimated):
    - confusion matrix (pixel counts)
    - per-class precision, recall, F1 and IoU
    - overall pixel accuracy and mean IoU

VALIDATION SPLIT
    Uses the same 10% hold-out split as training, so the model is scored on
    tiles it never trained on:
      - land cover: random.seed(42) + shuffle, last 10%  (train_unetpp_6band.py)
      - roads:      train_test_split(test_size=0.1, random_state=42)  (Kaggle_Road_Test.py)

HOW TO RUN
    # Land-cover model (U-Net++, 6 bands, 4 classes)
    python Training/evaluate_models.py classification ^
        --images  path/to/GeoSight_Consolidated_Dataset/Images ^
        --masks   path/to/GeoSight_Consolidated_Masked ^
        --checkpoint checkpoints/geosight_final_epoch_11.pt

    # Road model (U-Net ResNet-50, RGB, binary)
    python Training/evaluate_models.py roads ^
        --images  path/to/GeoSight_Consolidated_Dataset/Images ^
        --masks   path/to/Road_Masks_Generated ^
        --checkpoint Models/GeoSight_RoadExpert_Final_PyTorch.pt

    Add --limit 500 to evaluate on a random subset of the validation tiles.

OUTPUT
    Results are merged into
    Geosight_frontend/geosight/src/data/modelEvaluation.json
    and the Insights page shows them automatically on the next build.
"""
import argparse
import json
import os
import random
import sys
from datetime import date

import cv2
import numpy as np
import rasterio
import torch
from tqdm import tqdm

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "backend"))
sys.path.insert(0, os.path.dirname(__file__))

from predict_roads import load_road_model, IMAGENET_MEAN, IMAGENET_STD  # noqa: E402
from train_unetpp_6band import build_model  # noqa: E402

DEFAULT_OUTPUT = os.path.join(REPO_ROOT, "Geosight_frontend", "geosight", "src", "data", "modelEvaluation.json")

CLASSIFICATION_CLASSES = ["Background", "Rural", "Urban", "Water"]
ROAD_CLASSES = ["Non-Road", "Road"]
ROAD_TILE_SIZE = 256


# =============================================================================
# Metrics from a confusion matrix
# =============================================================================
def metrics_from_confusion(cm, class_names):
    """
    cm[i][j] = number of pixels whose TRUE class is i and PREDICTED class is j.
    """
    cm = np.asarray(cm, dtype=np.float64)
    tp = np.diag(cm)
    fp = cm.sum(axis=0) - tp   # predicted as class, but wasn't
    fn = cm.sum(axis=1) - tp   # was class, but predicted as something else

    def safe_div(a, b):
        return np.divide(a, b, out=np.zeros_like(a), where=b > 0)

    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    f1 = safe_div(2 * precision * recall, precision + recall)
    iou = safe_div(tp, tp + fp + fn)

    per_class = {
        name: {
            "precision": round(float(precision[i]) * 100, 2),
            "recall": round(float(recall[i]) * 100, 2),
            "f1": round(float(f1[i]) * 100, 2),
            "iou": round(float(iou[i]) * 100, 2),
            "pixels": int(cm[i].sum()),
        }
        for i, name in enumerate(class_names)
    }
    total = cm.sum()
    return {
        "per_class": per_class,
        "pixel_accuracy": round(float(tp.sum() / total) * 100, 2) if total else 0.0,
        "mean_iou": round(float(iou.mean()) * 100, 2),
    }


# =============================================================================
# Land-cover model
# =============================================================================
def classification_val_split(image_dir):
    """Same split as train_unetpp_6band.py: seed 42 shuffle, last 10%."""
    files = [f for f in os.listdir(image_dir) if f.endswith('.tif')]
    random.seed(42)
    random.shuffle(files)
    return files[int(0.9 * len(files)):]


def evaluate_classification(image_dir, mask_dir, checkpoint, files, device):
    model = build_model(encoder_weights=None)
    model.load_state_dict(torch.load(checkpoint, map_location=device))
    model.to(device).eval()

    n = len(CLASSIFICATION_CLASSES)
    cm = np.zeros((n, n), dtype=np.int64)
    used = 0

    for name in tqdm(files, desc="Evaluating land cover"):
        mask_path = os.path.join(mask_dir, name.replace(".tif", "_mask.tif"))
        if not os.path.exists(mask_path):
            continue

        # Same preprocessing as training and backend/predict.py
        with rasterio.open(os.path.join(image_dir, name)) as src:
            image = src.read([1, 2, 3, 4, 5, 6]).astype(np.float32)
        image = np.nan_to_num(np.clip(image / 10000.0, 0, 1), nan=0.0, posinf=1.0, neginf=0.0)

        with rasterio.open(mask_path) as src:
            mask = src.read(1).astype(np.int64)
        mask[(mask < 0) | (mask >= n)] = 0

        # Pad to a multiple of 32 for U-Net++, then crop back
        _, h, w = image.shape
        pad_h, pad_w = (-h) % 32, (-w) % 32
        padded = np.pad(image, ((0, 0), (0, pad_h), (0, pad_w)), mode='reflect')

        with torch.no_grad():
            logits = model(torch.from_numpy(padded).unsqueeze(0).to(device))
            pred = logits[0, :, :h, :w].argmax(dim=0).cpu().numpy()

        cm += np.bincount(mask.ravel() * n + pred.ravel(), minlength=n * n).reshape(n, n)
        used += 1

    return cm, used


# =============================================================================
# Road model
# =============================================================================
def road_val_split(image_dir):
    """Same split as Kaggle_Road_Test.py."""
    from sklearn.model_selection import train_test_split
    files = [f for f in os.listdir(image_dir) if f.lower().endswith('.tif')]
    _, val = train_test_split(files, test_size=0.1, random_state=42)
    return val


def find_road_mask(mask_dir, name):
    """Same mask naming rules as Kaggle_Road_Test.py."""
    for candidate in (name.replace('.tif', '_road_mask.tif'), name.replace('.tif', '_mask.png'),
                      name.replace('.tif', '.png'), name.replace('.tif', '_mask.tif'), name):
        path = os.path.join(mask_dir, candidate)
        if os.path.exists(path):
            if path.lower().endswith('.tif'):
                with rasterio.open(path) as src:
                    return src.read(1)
            return cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    return None


def evaluate_roads(image_dir, mask_dir, checkpoint, files, device):
    model = load_road_model(checkpoint, device=device)
    cm = np.zeros((2, 2), dtype=np.int64)
    used = 0

    for name in tqdm(files, desc="Evaluating roads"):
        mask = find_road_mask(mask_dir, name)
        if mask is None:
            continue

        # Same preprocessing as Kaggle_Road_Test.py: bands 3,2,1 (B4,B3,B2) as RGB
        with rasterio.open(os.path.join(image_dir, name)) as src:
            img = src.read([3, 2, 1]).transpose(1, 2, 0).astype(np.float32)
        img = np.nan_to_num(img, nan=0.0, posinf=0.0, neginf=0.0)
        if img.max() > img.min():
            img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        else:
            img = np.zeros_like(img, dtype=np.uint8)
        img = cv2.resize(img, (ROAD_TILE_SIZE, ROAD_TILE_SIZE))

        norm = (np.transpose(img.astype(np.float32) / 255.0, (2, 0, 1)) - IMAGENET_MEAN) / IMAGENET_STD
        truth = (cv2.resize(mask.astype(np.uint8), (ROAD_TILE_SIZE, ROAD_TILE_SIZE),
                            interpolation=cv2.INTER_NEAREST) > 0).astype(np.int64)

        with torch.no_grad():
            out = model(torch.from_numpy(norm).float().unsqueeze(0).to(device))
            pred = (torch.sigmoid(out)[0, 0] > 0.5).cpu().numpy().astype(np.int64)

        cm += np.bincount(truth.ravel() * 2 + pred.ravel(), minlength=4).reshape(2, 2)
        used += 1

    return cm, used


# =============================================================================
# Main
# =============================================================================
def save_results(output_path, key, result):
    data = {"classification": None, "roads": None}
    if os.path.exists(output_path):
        with open(output_path, encoding="utf-8") as f:
            data.update(json.load(f))
    data[key] = result
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(f"Saved {key} results to {output_path}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Evaluate GeoSight models on the validation split.")
    parser.add_argument("model", choices=["classification", "roads"])
    parser.add_argument("--images", required=True, help="Folder with the input .tif tiles")
    parser.add_argument("--masks", required=True, help="Folder with the ground-truth masks")
    parser.add_argument("--checkpoint", required=True, help="Model weights (.pt)")
    parser.add_argument("--limit", type=int, default=None, help="Evaluate on N random validation tiles")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="JSON file to write results into")
    args = parser.parse_args(argv)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    is_roads = args.model == "roads"

    files = road_val_split(args.images) if is_roads else classification_val_split(args.images)
    if args.limit:
        files = random.Random(0).sample(files, min(args.limit, len(files)))
    print(f"Evaluating {args.model} on {len(files)} validation tiles ({device})")

    evaluate = evaluate_roads if is_roads else evaluate_classification
    cm, used = evaluate(args.images, args.masks, args.checkpoint, files, device)
    if used == 0:
        sys.exit("No tiles with matching masks were found - nothing to evaluate.")

    class_names = ROAD_CLASSES if is_roads else CLASSIFICATION_CLASSES
    result = {
        "checkpoint": os.path.basename(args.checkpoint),
        "evaluated_on": date.today().isoformat(),
        "num_tiles": used,
        "classes": class_names,
        "confusion_matrix": cm.tolist(),
        **metrics_from_confusion(cm, class_names),
    }
    print(json.dumps({k: result[k] for k in ("num_tiles", "pixel_accuracy", "mean_iou")}, indent=2))
    save_results(args.output, args.model, result)


if __name__ == "__main__":
    main()
