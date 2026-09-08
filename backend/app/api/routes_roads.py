"""Road detection routes."""
import traceback
from datetime import datetime

import torch
from flask import Blueprint, current_app, jsonify, request, send_file

from app.config import OUTPUT_DIR
from app.schemas.requests import validate_bounds
from app.services.earth_engine import fetch_rgb_geotiff, parse_date_range
from app.services.road_detection import predict_roads
from app.services.visualization import generate_road_visualization

bp = Blueprint("roads", __name__)


@bp.post("/api/detect-roads")
def detect_roads():
    try:
        data = request.json or {}
        bounds, err = validate_bounds(data)
        if err:
            return jsonify({"error": err}), 400

        start_date, end_date, max_cloud_cover = parse_date_range(data)
        min_lat, min_lon = bounds["minLat"], bounds["minLon"]

        print(
            f"\n[*] Detecting roads for bounds: "
            f"({min_lat}, {min_lon}) to ({bounds['maxLat']}, {bounds['maxLon']})"
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        coord_str = f"lat{min_lat:.2f}_lon{min_lon:.2f}"
        filename = f"road_input_{coord_str}_{timestamp}.tif"
        output_path = OUTPUT_DIR / filename

        try:
            fetch_rgb_geotiff(
                bounds, start_date, end_date, max_cloud_cover, str(output_path)
            )
        except FileNotFoundError as e:
            return jsonify(
                {
                    "error": str(e),
                    "suggestion": "Try increasing cloudCover or expanding date range",
                }
            ), 404

        road_model = current_app.extensions.get("road_model")
        road_result = None
        road_error = None
        viz_filename = None

        if road_model is not None:
            try:
                print("[*] Running road detection...")
                device = "cuda" if torch.cuda.is_available() else "cpu"
                road_result = predict_roads(road_model, str(output_path), device=device)
                print(
                    f"[OK] Road detection complete: "
                    f"{road_result['road_percentage']:.2f}% roads"
                )

                print("[*] Generating road visualization...")
                viz_filename = f"road_viz_{coord_str}_{timestamp}.png"
                viz_path = OUTPUT_DIR / viz_filename
                generate_road_visualization(road_model, str(output_path), str(viz_path))

                if not viz_path.exists():
                    viz_filename = None
                else:
                    print(f"[OK] Visualization saved: {viz_filename}")
            except Exception as e:
                print(f"[ERROR] Road detection failed: {e}")
                traceback.print_exc()
                road_error = str(e)
        else:
            road_error = "Road model not loaded"

        response_data = {
            "success": True,
            "message": "Road detection completed",
            "file": filename,
            "model": "RoadExpert (ResNet-50)",
        }

        if road_result:
            response_data["road_detection"] = {
                "road_percentage": road_result["road_percentage"],
                "road_pixels": road_result["road_pixels"],
                "total_pixels": road_result["total_pixels"],
            }
            if viz_filename:
                response_data["visualization"] = viz_filename
        else:
            response_data["error"] = road_error

        return jsonify(response_data)

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@bp.get("/api/download/<filename>")
def download_file(filename):
    try:
        file_path = OUTPUT_DIR / filename
        print(f"[*] Download request for: {filename}")
        print(f"[*] Full path: {file_path}")
        print(f"[*] File exists: {file_path.exists()}")

        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404

        if filename.endswith(".png"):
            mimetype = "image/png"
            as_attachment = False
        elif filename.endswith(".tif") or filename.endswith(".tiff"):
            mimetype = "image/tiff"
            as_attachment = True
        else:
            mimetype = "application/octet-stream"
            as_attachment = True

        response = send_file(
            file_path, mimetype=mimetype, as_attachment=as_attachment
        )
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
