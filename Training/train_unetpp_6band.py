r"""
GeoSight - Land-cover training script
=====================================

WHAT THIS TRAINS
    A model that looks at a satellite tile and labels EVERY pixel as one of:
        0 = Background, 1 = Rural, 2 = Urban, 3 = Water

THE MODEL
    U-Net++ with an EfficientNet-B4 encoder (from segmentation_models_pytorch)
      - Encoder (EfficientNet-B4): shrinks the image down and learns features
        like "this texture looks like buildings" or "this looks like water".
      - Decoder (U-Net++): grows it back up to full size so we get one label
        per pixel. U-Net++ adds extra "skip connections" that help keep fine
        details such as edges of rivers and small villages.

THE INPUT (6 bands from Sentinel-2)
    B2 (Blue), B3 (Green), B4 (Red), B8 (Near-Infrared),
    B11 (Short-wave IR 1), B12 (Short-wave IR 2)
    NIR helps spot vegetation, SWIR helps spot buildings and water.

THE STEPS IN THIS FILE
    1. Settings
    2. Dataset   - how one tile + its mask is read from disk
    3. Augmentation - random flips/rotations so the model generalizes
    4. Model     - build U-Net++
    5. Loss      - Dice + Focal (handles rare classes like Water)
    6. Training loop - learn, then check on validation data each epoch
    7. Save a checkpoint every epoch (geosight_final_epoch_N.pt)

NOTE ON HISTORY
    The original script used to train our deployed checkpoints was not kept
    in the repo, so this file was rebuilt from the deployed model.
    It has been checked: checkpoints/geosight_final_epoch_11.pt loads into
    build_model() with every weight matching (strict=True), and it uses the
    same input format as backend/predict.py. Hyperparameters such as batch
    size may differ slightly from the original run.

HOW TO RUN
    set GEOSIGHT_IMG_DIR=path\to\Images
    set GEOSIGHT_MASK_DIR=path\to\Masks
    python train_unetpp_6band.py
"""
import os
import random
import warnings

import numpy as np
import rasterio
import torch
from torch.utils.data import Dataset, DataLoader
import segmentation_models_pytorch as smp
import albumentations as A
from albumentations.pytorch import ToTensorV2
from rasterio.errors import NotGeoreferencedWarning
from tqdm import tqdm

warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)
os.environ['GDAL_NUM_THREADS'] = '1'  # stops rasterio hanging on Windows


# =============================================================================
# 1. SETTINGS
# =============================================================================
IMG_DIR = os.environ.get("GEOSIGHT_IMG_DIR", r"GeoSight_Consolidated_Dataset\Images")
MASK_DIR = os.environ.get("GEOSIGHT_MASK_DIR", r"GeoSight_Consolidated_Masked")
CHECKPOINT_DIR = "checkpoints"

IN_CHANNELS = 6        # 6 satellite bands go in
NUM_CLASSES = 4        # 4 labels come out (Background, Rural, Urban, Water)
BATCH_SIZE = 12        # tiles per training step (lower this if GPU runs out of memory)
EPOCHS = 30            # full passes over the dataset
LEARNING_RATE = 1e-4   # how big each learning step is
VAL_SPLIT = 0.1        # 10% of tiles are kept aside to check the model

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# =============================================================================
# 2. DATASET - reads one image tile and its matching mask
# =============================================================================
class GeoSightDataset(Dataset):
    """
    Each item is a pair:
        image: 6 x H x W  (the satellite bands, scaled to 0-1)
        mask:  H x W      (the correct label 0-3 for every pixel)

    Masks are matched by name:  Delhi_tile_1.tif  ->  Delhi_tile_1_mask.tif
    """

    def __init__(self, image_dir, mask_dir, filenames, transform=None):
        self.image_dir = image_dir
        self.mask_dir = mask_dir
        self.filenames = filenames
        self.transform = transform
        print(f"Dataset ready with {len(self.filenames)} tiles.")

    def __len__(self):
        return len(self.filenames)

    def __getitem__(self, idx):
        img_name = self.filenames[idx]
        img_path = os.path.join(self.image_dir, img_name)
        mask_path = os.path.join(self.mask_dir, img_name.replace(".tif", "_mask.tif"))

        try:
            # --- Read the 6 bands ---
            with rasterio.open(img_path) as src:
                image = src.read([1, 2, 3, 4, 5, 6]).astype(np.float32)

            # Sentinel-2 values are 0-10000, so divide to get 0-1.
            # (backend/predict.py does exactly the same, so training and
            #  prediction see the same kind of numbers.)
            image = np.clip(image / 10000.0, 0, 1)
            image = np.nan_to_num(image, nan=0.0, posinf=1.0, neginf=0.0)

            # Albumentations wants Height x Width x Channels
            image = np.transpose(image, (1, 2, 0))

            # --- Read the mask ---
            with rasterio.open(mask_path) as src:
                mask = src.read(1).astype(np.int64)

            # Any label outside 0-3 is treated as Background
            mask[(mask < 0) | (mask >= NUM_CLASSES)] = 0
            mask = mask.astype(np.uint8)

            # --- Augment and convert to PyTorch tensors ---
            if self.transform:
                augmented = self.transform(image=image, mask=mask)
                image = augmented['image']
                mask = augmented['mask'].long()

            return image, mask

        except Exception as e:
            # If a file is broken, skip it and use a random other tile instead
            print(f"\nCould not read {img_name}: {e}")
            return self.__getitem__(random.randint(0, len(self.filenames) - 1))


# =============================================================================
# 3. AUGMENTATION - random changes so the model doesn't just memorise tiles
# =============================================================================
# Satellite images have no "up", so flips and rotations are always valid.
train_transform = A.Compose([
    A.HorizontalFlip(p=0.5),
    A.VerticalFlip(p=0.5),
    A.RandomRotate90(p=0.5),
    A.Affine(scale=(0.95, 1.05), translate_percent=(-0.05, 0.05), rotate=(-15, 15), p=0.5),
    ToTensorV2(),
])

# Validation images are NOT changed - we want an honest score.
val_transform = A.Compose([
    ToTensorV2(),
])


# =============================================================================
# 4. MODEL - U-Net++ with EfficientNet-B4
# =============================================================================
def build_model(encoder_weights="imagenet"):
    """
    Builds the exact architecture used by backend/predict.py.

    encoder_weights="imagenet" starts the encoder from weights pre-trained on
    normal photos, which makes training much faster. When loading our own
    saved checkpoint, pass encoder_weights=None.
    """
    return smp.UnetPlusPlus(
        encoder_name="efficientnet-b4",
        encoder_weights=encoder_weights,
        in_channels=IN_CHANNELS,
        classes=NUM_CLASSES,
    )


# =============================================================================
# 5-7. TRAINING
# =============================================================================
def main():
    print(f"Training U-Net++ (EfficientNet-B4) on: {device}")

    # --- Split tiles into training (90%) and validation (10%) ---
    all_files = [f for f in os.listdir(IMG_DIR) if f.endswith('.tif')]
    random.seed(42)              # same split every time we run
    random.shuffle(all_files)
    split = int((1 - VAL_SPLIT) * len(all_files))
    train_files, val_files = all_files[:split], all_files[split:]

    train_loader = DataLoader(
        GeoSightDataset(IMG_DIR, MASK_DIR, train_files, train_transform),
        batch_size=BATCH_SIZE, shuffle=True,
        num_workers=4, pin_memory=True, persistent_workers=True,
    )
    val_loader = DataLoader(
        GeoSightDataset(IMG_DIR, MASK_DIR, val_files, val_transform),
        batch_size=BATCH_SIZE, shuffle=False,
        num_workers=4, pin_memory=True,
    )

    # --- Model ---
    model = build_model().to(device)

    # If training crashed earlier, continue from the last recovery save
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    recovery_path = os.path.join(CHECKPOINT_DIR, "geosight_recovery_checkpoint.pt")
    if os.path.exists(recovery_path):
        print("Found recovery checkpoint, resuming from it...")
        model.load_state_dict(torch.load(recovery_path, map_location=device))

    # --- 5. Loss: Dice + Focal ---
    # Dice  : scores how well each predicted region overlaps the true region.
    #         Good for classes that cover few pixels (e.g. Water).
    # Focal : like normal cross-entropy, but focuses on the pixels the model
    #         still gets wrong instead of the easy ones.
    dice_loss = smp.losses.DiceLoss(smp.losses.MULTICLASS_MODE, from_logits=True)
    focal_loss = smp.losses.FocalLoss(smp.losses.MULTICLASS_MODE)

    def compute_loss(outputs, masks):
        return dice_loss(outputs, masks) + focal_loss(outputs, masks)

    # AdamW = Adam optimizer with weight decay (helps avoid overfitting)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)

    # --- 6. Training loop ---
    for epoch in range(EPOCHS):
        print(f"\n--- Epoch {epoch + 1}/{EPOCHS} ---")

        # ---- Learn on training tiles ----
        model.train()
        train_loss = 0.0
        loop = tqdm(train_loader, desc="Training")

        for step, (images, masks) in enumerate(loop):
            images = images.to(device, non_blocking=True)
            masks = masks.to(device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)

            # Mixed precision (bfloat16) on GPU: faster and uses less memory
            with torch.autocast(device_type=device.type, dtype=torch.bfloat16,
                                enabled=device.type == 'cuda'):
                outputs = model(images)            # shape: batch x 4 x H x W
                loss = compute_loss(outputs, masks)

            loss.backward()                        # work out how to adjust weights
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)  # avoid huge jumps
            optimizer.step()                       # adjust the weights

            train_loss += loss.item()
            loop.set_postfix(loss=f"{loss.item():.4f}")

            # Safety save every 400 steps in case the run crashes
            if (step + 1) % 400 == 0:
                torch.save(model.state_dict(), recovery_path)

        # ---- Check on validation tiles (no learning here) ----
        model.eval()
        val_loss = 0.0
        all_tp, all_fp, all_fn, all_tn = [], [], [], []

        with torch.no_grad():
            for images, masks in tqdm(val_loader, desc="Validation"):
                images = images.to(device, non_blocking=True)
                masks = masks.to(device, non_blocking=True)

                outputs = model(images)
                val_loss += compute_loss(outputs, masks).item()

                # Pick the most likely class for each pixel
                preds = torch.argmax(outputs, dim=1, keepdim=True)

                # Count true/false positives/negatives for each class
                tp, fp, fn, tn = smp.metrics.get_stats(
                    preds, masks.unsqueeze(1).long(),
                    mode='multiclass', num_classes=NUM_CLASSES,
                )
                all_tp.append(tp.cpu()); all_fp.append(fp.cpu())
                all_fn.append(fn.cpu()); all_tn.append(tn.cpu())

        tp, fp = torch.cat(all_tp), torch.cat(all_fp)
        fn, tn = torch.cat(all_fn), torch.cat(all_tn)

        # IoU = overlap / union between predicted and true pixels (higher is better)
        iou = smp.metrics.iou_score(tp, fp, fn, tn, reduction="micro")
        accuracy = smp.metrics.accuracy(tp, fp, fn, tn, reduction="macro")

        print(f"Epoch {epoch + 1} results:")
        print(f"  Train loss: {train_loss / len(train_loader):.4f}")
        print(f"  Val loss:   {val_loss / len(val_loader):.4f}")
        print(f"  Val accuracy: {accuracy:.4f}  |  Val mIoU: {iou:.4f}")

        # --- 7. Save this epoch's weights ---
        # backend/app.py uses geosight_final_epoch_11.pt from this series.
        torch.save(model.state_dict(),
                   os.path.join(CHECKPOINT_DIR, f"geosight_final_epoch_{epoch + 1}.pt"))

    print("\nTraining finished.")


if __name__ == '__main__':
    main()
