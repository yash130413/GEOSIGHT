"""Land classification routes."""
import traceback
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request

from app.schemas.requests import validate_bounds
from app.services.earth_engine import fetch_multispectral_geotiff, parse_date_range
from app.services.classification import predict_image
from app.services.visualization import generate_4panel
from app.config import OUTPUT_DIR

bp = Blueprint("classify", __name__)


@bp.post("/api/fetch-image")
def fetch_image():
    try:
        data = request.json or {}
        bounds, err = validate_bounds(data)
        if err:
            return jsonify({"error": err}), 400

        start_date, end_date, max_cloud_cover = parse_date_range(data)
        min_lat, min_lon = bounds["minLat"], bounds["minLon"]

        print(
            f"\n[*] Fetching image for bounds: "
            f"({min_lat}, {min_lon}) to ({bounds['maxLat']}, {bounds['maxLon']})"
        )
        print(f"    Cloud cover: <{max_cloud_cover}%")
        print(f"    Date range: {start_date} to {end_date}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        coord_str = f"lat{min_lat:.2f}_lon{min_lon:.2f}"
        filename = f"sentinel2_{coord_str}_{timestamp}.tif"
        output_path = OUTPUT_DIR / filename

        try:
            info = fetch_multispectral_geotiff(
                bounds, start_date, end_date, max_cloud_cover, str(output_path)
            )
        except FileNotFoundError as e:
            return jsonify(
                {
                    "error": str(e),
                    "suggestion": "Try increasing cloudCover or expanding date range",
                }
            ), 404

        model = current_app.extensions.get("land_model")
        prediction_result = None
        prediction_error = None
        panel_filename = None

        print("[*] Running model prediction...")
        print(f"[DEBUG] Model is None: {model is None}")
        print(f"[DEBUG] Output path: {output_path}")
        print(f"[DEBUG] File exists: {output_path.exists()}")

        if model is not None:
            try:
                prediction_result = predict_image(model, str(output_path))
                print(f"[OK] Prediction complete: {prediction_result['dominant_class']}")

                print("[*] Generating 4-panel visualization...")
                panel_filename = f"4panel_{coord_str}_{timestamp}.png"
                panel_4_path = OUTPUT_DIR / panel_filename
                generate_4panel(model, str(output_path), str(panel_4_path))

                if panel_4_path.exists():
                    print(f"[OK] 4-panel saved: {panel_filename}")
                else:
                    panel_filename = None
            except Exception as pred_error:
                print(f"[ERROR] Prediction/4-panel generation failed: {pred_error}")
                traceback.print_exc()
                prediction_error = str(pred_error)
                panel_filename = None
        else:
            prediction_error = "Model not loaded"

        response_data = {
            "success": True,
            "message": "Image fetched successfully",
            "file": filename,
            "path": str(output_path),
            "info": info,
        }

        if prediction_result:
            response_data["prediction"] = prediction_result
            if panel_filename:
                response_data["visualization_4panel"] = panel_filename
        else:
            response_data["prediction_error"] = prediction_error

        return jsonify(response_data)

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
