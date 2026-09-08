"""Entry point: python -m app.main  (from backend/)"""
from app import create_app
from app.config import FLASK_DEBUG, FLASK_HOST, FLASK_PORT, LAND_MODEL_PATH

app = create_app()

if __name__ == "__main__":
    print("=" * 60)
    print("GEOSIGHT FLASK BACKEND")
    print("=" * 60)
    print("\nEndpoints:")
    print("  GET  /api/health")
    print("  POST /api/fetch-image (terrain classification)")
    print("  POST /api/detect-roads (road detection)")
    print("  GET  /api/download/<filename>")
    print(f"\nLand model: {LAND_MODEL_PATH}")
    print(f"Starting server on http://{FLASK_HOST}:{FLASK_PORT}")
    print("=" * 60)

    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)
