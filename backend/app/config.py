"""Application configuration — paths and environment."""
import os
from pathlib import Path

# backend/app/config.py -> repo root is parents[2]
ROOT_DIR = Path(__file__).resolve().parents[2]

_env_file = ROOT_DIR / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        # Lightweight .env loader (no python-dotenv required)
        for line in _env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

EE_PROJECT_ID = os.getenv("EE_PROJECT_ID", "geosight-95054")
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")

ARTIFACTS_DIR = ROOT_DIR / "artifacts"
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(ARTIFACTS_DIR / "outputs")))
MODELS_DIR = Path(os.getenv("MODELS_DIR", str(ARTIFACTS_DIR / "models")))

LAND_MODEL_PATH = Path(
    os.getenv("LAND_MODEL_PATH", str(MODELS_DIR / "land_unetpp_epoch11.pt"))
)
ROAD_MODEL_PATH = Path(
    os.getenv("ROAD_MODEL_PATH", str(MODELS_DIR / "road_resnet50.pt"))
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
