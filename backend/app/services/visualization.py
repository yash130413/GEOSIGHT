"""Visualization helpers for classification and road detection."""
import os
import traceback

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import rasterio
import torch
from PIL import Image
from skimage.morphology import remove_small_objects

from app.services.road_detection import preprocess

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

CLASS_COLORS = {
    0: [128, 128, 128],
    1: [34, 139, 34],
    2: [255, 107, 107],
    3: [65, 105, 225],
}


def apply_morphological_filter(pred_mask, min_water_size=500):
    """Remove small false water detections."""
    filtered = pred_mask.copy()
    water_mask = pred_mask == 3
    if np.sum(water_mask) > 0:
        water_mask_cleaned = remove_small_objects(water_mask, min_size=min_water_size)
        fake_water = water_mask & ~water_mask_cleaned
        filtered[fake_water] = 2
    return filtered


def mask_to_rgb(mask):
    h, w = mask.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for class_id, color in CLASS_COLORS.items():
        rgb[mask == class_id] = color
    return rgb


def generate_4panel(model, image_path, output_path):
    """Generate 4-panel classification visualization and save as PNG."""
    try:
        print(f"[*] Generating 4-panel from: {image_path}")
        print(f"[*] Output will be saved to: {output_path}")

        with rasterio.open(image_path) as src:
            image = src.read([1, 2, 3, 4, 5, 6]).astype(np.float32)
            print(f"[DEBUG] Image shape: {image.shape}")

        image = np.clip(image / 10000.0, 0, 1)
        image = np.nan_to_num(image, nan=0.0, posinf=1.0, neginf=0.0)

        c, h, w = image.shape
        new_h = ((h + 31) // 32) * 32
        new_w = ((w + 31) // 32) * 32
        padded = np.pad(image, ((0, 0), (0, new_h - h), (0, new_w - w)), mode="reflect")
        print(f"[DEBUG] Padded shape: {padded.shape}")

        tensor = torch.from_numpy(padded).unsqueeze(0).to(device)
        with torch.no_grad():
            outputs = model(tensor)
            outputs = outputs[:, :, :h, :w]
            raw_pred = torch.argmax(outputs, dim=1).squeeze(0).cpu().numpy()
        print(f"[DEBUG] Prediction shape: {raw_pred.shape}")

        filtered_pred = apply_morphological_filter(raw_pred)
        rgb_raw = mask_to_rgb(raw_pred)
        rgb_filtered = mask_to_rgb(filtered_pred)

        rgb_orig = np.stack([image[2], image[1], image[0]], axis=0)
        rgb_orig = np.transpose(rgb_orig, (1, 2, 0))
        rgb_orig = np.clip(rgb_orig * 3.5 * 255, 0, 255).astype(np.uint8)

        overlay = (rgb_orig * 0.6 + rgb_filtered * 0.4).astype(np.uint8)

        top = np.hstack([rgb_orig, rgb_raw])
        bottom = np.hstack([rgb_filtered, overlay])
        final = np.vstack([top, bottom])

        Image.fromarray(final).save(output_path)
        print(f"[OK] 4-panel saved successfully to: {output_path}")
        return output_path
    except Exception as e:
        print(f"[ERROR] Failed to generate 4-panel: {e}")
        traceback.print_exc()
        raise


def _clean_road_network(mask_255):
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask_255, cv2.MORPH_OPEN, kernel)
    kernel_connect = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_connect)

    skeleton = np.zeros_like(mask)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    temp_mask = mask.copy()
    for _ in range(10):
        eroded = cv2.erode(temp_mask, element)
        temp = cv2.dilate(eroded, element)
        temp = cv2.subtract(temp_mask, temp)
        skeleton = cv2.bitwise_or(skeleton, temp)
        temp_mask = eroded.copy()
        if cv2.countNonZero(temp_mask) == 0:
            break
    return skeleton


def generate_road_visualization(model, image_path, output_path):
    """Generate 3-panel road detection visualization."""
    device_local = next(model.parameters()).device

    img_norm, original_uint8 = preprocess(image_path)

    tensor = torch.from_numpy(img_norm).float().unsqueeze(0).to(device_local)
    with torch.no_grad():
        output = model(tensor)
        pred_mask = (torch.sigmoid(output) > 0.5).squeeze().cpu().numpy().astype(np.uint8)

    pred_mask_255 = (pred_mask * 255).astype(np.uint8)
    clean_roads = _clean_road_network(pred_mask_255)

    road_viz = np.ones((256, 256, 3), dtype=np.uint8) * 255
    road_viz[clean_roads > 0] = [0, 0, 0]

    overlay = original_uint8.copy()
    overlay[clean_roads > 0] = [255, 100, 0]

    tile_name = os.path.basename(image_path)
    fig = plt.figure(figsize=(16, 6), facecolor="white")
    fig.suptitle(f"Road Detection: {tile_name}", fontsize=14, fontweight="bold", y=1.0)

    gs = gridspec.GridSpec(
        1, 3, figure=fig, wspace=0.05, left=0.01, right=0.99, top=0.85, bottom=0.01
    )

    ax1 = fig.add_subplot(gs[0])
    ax1.imshow(original_uint8)
    ax1.set_title("Satellite Image", fontsize=13, fontweight="bold", pad=12)
    ax1.axis("off")

    ax2 = fig.add_subplot(gs[1])
    ax2.imshow(road_viz)
    ax2.set_title("Predicted Road Network", fontsize=13, fontweight="bold", pad=12)
    ax2.axis("off")

    ax3 = fig.add_subplot(gs[2])
    ax3.imshow(overlay)
    ax3.set_title("Road Overlay", fontsize=13, fontweight="bold", pad=12)
    ax3.axis("off")

    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
