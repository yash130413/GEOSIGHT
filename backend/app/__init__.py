"""GeoSight Flask application factory."""
import torch
from flask import Flask
from flask_cors import CORS

from app.config import LAND_MODEL_PATH, ROAD_MODEL_PATH, OUTPUT_DIR
from app.services.earth_engine import init_earth_engine
from app.services.classification import load_model
from app.services.road_detection import load_road_model
from app.api.routes_health import bp as health_bp
from app.api.routes_classify import bp as classify_bp
from app.api.routes_roads import bp as roads_bp


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    print(f"[*] Output directory: {OUTPUT_DIR}")

    # Land classification model
    print("[*] Loading classification model from:", LAND_MODEL_PATH)
    print("[*] Model file exists:", LAND_MODEL_PATH.exists())
    land_model = None
    try:
        if LAND_MODEL_PATH.exists():
            land_model = load_model(str(LAND_MODEL_PATH))
            print("[OK] Classification model loaded successfully")
            print(f"[OK] Model device: {next(land_model.parameters()).device}")
        else:
            print("[ERROR] Classification model file not found")
    except Exception as e:
        print(f"[ERROR] Failed to load classification model: {e}")
        import traceback

        traceback.print_exc()

    # Road detection model
    print("[*] Loading road detection model from:", ROAD_MODEL_PATH)
    print("[*] Road model file exists:", ROAD_MODEL_PATH.exists())
    road_model = None
    if ROAD_MODEL_PATH.exists():
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            road_model = load_road_model(str(ROAD_MODEL_PATH), device=device)
            print(f"[OK] Road detection model loaded successfully on {device}")
        except Exception as e:
            print(f"[ERROR] Failed to load road detection model: {e}")
            import traceback

            traceback.print_exc()
    else:
        print(f"[ERROR] Road model file not found at: {ROAD_MODEL_PATH}")

    app.extensions["land_model"] = land_model
    app.extensions["road_model"] = road_model

    init_earth_engine()

    app.register_blueprint(health_bp)
    app.register_blueprint(classify_bp)
    app.register_blueprint(roads_bp)

    return app
