"""
Flask Backend for GeoSight
Receives coordinates from frontend and fetches Sentinel-2 images from GEE

Configuration (environment variables, all optional):
    GEOSIGHT_MODEL_PATH       land-cover checkpoint
                              (default: <repo>/checkpoints/geosight_final_epoch_11.pt)
    GEOSIGHT_ROAD_MODEL_PATH  road checkpoint
                              (default: <repo>/Models/GeoSight_RoadExpert_Final_PyTorch.pt)
    GEOSIGHT_OUTPUT_DIR       where downloaded/generated files go (default: <repo>/backend_outputs)
    GEOSIGHT_EE_PROJECT       Google Earth Engine cloud project (default: gen-lang-client-0871361958)
    GEOSIGHT_HOST             interface to bind (default 127.0.0.1 = this computer only;
                              0.0.0.0 exposes the API to the network)
    GEOSIGHT_PORT             port (default 5000)
    GEOSIGHT_DEBUG            set to 1 for Flask debug mode (NEVER on a shared network:
                              the debugger allows running arbitrary code)
    GEOSIGHT_CORS_ORIGINS     comma-separated frontend origins allowed to call the API
                              (default http://localhost:5173,http://127.0.0.1:5173)

For a deployment, run with a production server instead of app.run(), e.g.:
    waitress-serve --host 0.0.0.0 --port 5000 app:app
"""
import math
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import ee
import os
import rasterio
import requests
import torch
from datetime import datetime, timedelta
from predict import load_model, predict_image
from generate_4panel import generate_4panel
from predict_roads import load_road_model, predict_roads
from generate_road_viz import generate_road_visualization

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 MB upload limit
CORS_ORIGINS = [o.strip() for o in os.environ.get(
    "GEOSIGHT_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}})

# --- Configuration ---
PROJECT_ID = os.environ.get("GEOSIGHT_EE_PROJECT", "gen-lang-client-0871361958")
OUTPUT_DIR = os.path.abspath(os.environ.get("GEOSIGHT_OUTPUT_DIR", os.path.join(REPO_ROOT, "backend_outputs")))
MODEL_PATH = os.path.abspath(os.environ.get(
    "GEOSIGHT_MODEL_PATH", os.path.join(REPO_ROOT, "checkpoints", "geosight_final_epoch_11.pt")))
ROAD_MODEL_PATH = os.path.abspath(os.environ.get(
    "GEOSIGHT_ROAD_MODEL_PATH", os.path.join(REPO_ROOT, "Models", "GeoSight_RoadExpert_Final_PyTorch.pt")))

os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"[*] Output directory: {OUTPUT_DIR}")

device = 'cuda' if torch.cuda.is_available() else 'cpu'


def missing_checkpoint_message(path, env_var):
    return (f"Checkpoint not found at {path}. Download it (see docs/MODELS.md) "
            f"and place it there, or set {env_var} to its location.")


# --- Land-cover model (U-Net++ / EfficientNet-B4, epoch 11) ---
# Architecture matches Training/train_unetpp_6band.py
model = None
model_error = None
print("[*] Loading classification model from:", MODEL_PATH)
if not os.path.exists(MODEL_PATH):
    model_error = missing_checkpoint_message(MODEL_PATH, "GEOSIGHT_MODEL_PATH")
    print(f"[ERROR] {model_error}")
else:
    try:
        model = load_model(MODEL_PATH)
        print(f"[OK] Classification model loaded on {next(model.parameters()).device}")
    except Exception as e:
        model_error = f"Failed to load classification model: {e}"
        print(f"[ERROR] {model_error}")

# --- Road model (U-Net / ResNet-50) ---
road_model = None
road_model_error = None
print("[*] Loading road detection model from:", ROAD_MODEL_PATH)
if not os.path.exists(ROAD_MODEL_PATH):
    road_model_error = missing_checkpoint_message(ROAD_MODEL_PATH, "GEOSIGHT_ROAD_MODEL_PATH")
    print(f"[ERROR] {road_model_error}")
else:
    try:
        road_model = load_road_model(ROAD_MODEL_PATH, device=device)
        print(f"[OK] Road detection model loaded on {device}")
    except Exception as e:
        road_model_error = f"Failed to load road detection model: {e}"
        print(f"[ERROR] {road_model_error}")

# --- Earth Engine ---
# Never prompt for login inside the server; if this fails the API still runs
# (uploads work) and the map endpoints return a clear 503 instead.
EE_INITIALIZED = False
ee_error = None
try:
    ee.Initialize(project=PROJECT_ID)
    EE_INITIALIZED = True
    print(f"[OK] Earth Engine initialized (project: {PROJECT_ID})")
except Exception as e:
    ee_error = str(e)
    print(f"[WARNING] Earth Engine initialization failed for project '{PROJECT_ID}': {e}")
    print("[INFO] Map-based analysis is disabled. Run `earthengine authenticate` once, and set "
          "GEOSIGHT_EE_PROJECT to a Google Cloud project registered for Earth Engine.")


def earth_engine_unavailable():
    return jsonify({
        'error': 'Earth Engine is not configured on the server',
        'suggestion': 'Run `earthengine authenticate` and set GEOSIGHT_EE_PROJECT, then restart the backend'
    }), 503


# --- Request validation ---
# Earth Engine refuses downloads over ~50 MB; 8 float32 bands at 10 m is 32 bytes/pixel,
# so cap the area well below that (about 150 km2).
MAX_AREA_PIXELS = 1_500_000
DATE_FORMAT = '%Y-%m-%d'


def bad_request(message):
    return jsonify({'error': message}), 400


def parse_analysis_request():
    """
    Validate the JSON body shared by /api/fetch-image and /api/detect-roads.
    Returns (params, None) on success or (None, error_response).
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, bad_request('Request body must be a JSON object')

    bounds = data.get('bounds')
    if not isinstance(bounds, dict):
        return None, bad_request('Missing bounds parameter')

    coords = []
    for key in ('minLon', 'minLat', 'maxLon', 'maxLat'):
        value = bounds.get(key)
        # bool is a subclass of int, so reject it explicitly
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            return None, bad_request(f'bounds.{key} must be a number')
        coords.append(float(value))
    min_lon, min_lat, max_lon, max_lat = coords

    if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
        return None, bad_request('Longitude must be between -180 and 180')
    if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
        return None, bad_request('Latitude must be between -90 and 90')
    if min_lon >= max_lon or min_lat >= max_lat:
        return None, bad_request('bounds must have minLon < maxLon and minLat < maxLat')

    # Approximate size of the 10 m image that would be downloaded
    mid_lat = math.radians((min_lat + max_lat) / 2)
    width_px = (max_lon - min_lon) * 111_320 * math.cos(mid_lat) / 10
    height_px = (max_lat - min_lat) * 110_540 / 10
    if width_px * height_px > MAX_AREA_PIXELS:
        area_km2 = width_px * height_px * 100 / 1e6
        return None, bad_request(
            f'Selected area is too large (~{area_km2:.0f} km2). '
            f'Please select at most ~{MAX_AREA_PIXELS * 100 / 1e6:.0f} km2.')

    cloud_cover = data.get('cloudCover', 10)
    if isinstance(cloud_cover, bool) or not isinstance(cloud_cover, (int, float)) or not 0 <= cloud_cover <= 100:
        return None, bad_request('cloudCover must be a number between 0 and 100')

    start_date = data.get('startDate', (datetime.now() - timedelta(days=180)).strftime(DATE_FORMAT))
    end_date = data.get('endDate', datetime.now().strftime(DATE_FORMAT))
    try:
        start = datetime.strptime(str(start_date), DATE_FORMAT)
        end = datetime.strptime(str(end_date), DATE_FORMAT)
    except ValueError:
        return None, bad_request('startDate and endDate must use the format YYYY-MM-DD')
    if start > end:
        return None, bad_request('startDate must not be after endDate')

    return {
        'bounds': (min_lon, min_lat, max_lon, max_lat),
        'cloud_cover': cloud_cover,
        'start_date': start_date,
        'end_date': end_date,
    }, None


def server_error(context, exc):
    """Log full details on the server; return a message without internals to the client."""
    import traceback
    print(f"[FAIL] {context}: {exc}")
    traceback.print_exc()
    if isinstance(exc, ee.EEException):
        return jsonify({'error': f'Earth Engine error: {exc}'}), 502
    return jsonify({'error': f'{context} failed due to a server error'}), 500


# --- Earth Engine + inference helpers shared by the endpoints ---
LAND_COVER_BANDS = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12', 'NDVI', 'NDBI']
DOWNLOAD_TIMEOUT_S = 300


def get_median_composite(params):
    """
    Cloud-filtered Sentinel-2 median composite for the requested area and dates.
    Returns (region, image), or (region, None) when no scene matches.
    """
    region = ee.Geometry.Rectangle(list(params['bounds']))
    collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(region) \
        .filterDate(params['start_date'], params['end_date']) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', params['cloud_cover']))

    count = collection.size().getInfo()
    if count == 0:
        return region, None
    print(f"[OK] Found {count} images")
    # Median composite reduces leftover clouds
    return region, collection.median()


def no_images_found(params):
    return jsonify({
        'error': f"No images found with <{params['cloud_cover']}% cloud cover",
        'suggestion': 'Try increasing cloudCover or expanding date range'
    }), 404


def land_cover_bands(image):
    """
    The 8 bands saved for the land-cover model, all Float32 at 10 m:
    B2, B3, B4, B8, B11, B12 (model input) + NDVI, NDBI (kept for analysis).
    """
    b2 = image.select('B2').toFloat()   # Blue - 10m
    b3 = image.select('B3').toFloat()   # Green - 10m
    b4 = image.select('B4').toFloat()   # Red - 10m
    b8 = image.select('B8').toFloat()   # NIR - 10m
    # Resample B11 and B12 from 20m to 10m
    b11 = image.select('B11').resample('bilinear').reproject(crs='EPSG:4326', scale=10).toFloat()
    b12 = image.select('B12').resample('bilinear').reproject(crs='EPSG:4326', scale=10).toFloat()

    ndvi = b8.subtract(b4).divide(b8.add(b4)).rename('NDVI').toFloat()
    ndbi = b11.subtract(b8).divide(b11.add(b8)).rename('NDBI').toFloat()

    return ee.Image.cat([
        b2.rename('B2'), b3.rename('B3'), b4.rename('B4'), b8.rename('B8'),
        b11.rename('B11'), b12.rename('B12'), ndvi, ndbi
    ])


def output_name(params):
    """Unique-ish name for output files: coordinates + timestamp."""
    min_lon, min_lat = params['bounds'][0], params['bounds'][1]
    return f"lat{min_lat:.2f}_lon{min_lon:.2f}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def download_geotiff(image, region, output_path, bands=None):
    """Download an Earth Engine image as a 10 m GeoTIFF."""
    url_params = {'region': region, 'scale': 10, 'format': 'GEO_TIFF'}
    if bands:
        url_params['bands'] = bands
    url = image.getDownloadURL(url_params)

    response = requests.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT_S)
    if response.status_code != 200:
        raise ee.EEException(f'Image download failed (HTTP {response.status_code})')
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"[OK] Downloaded {os.path.basename(output_path)}")


def raster_info(path):
    with rasterio.open(path) as src:
        res = src.res[1]
        if src.crs is not None and src.crs.is_geographic:
            # Pixel size is in degrees (EPSG:4326); 1 degree of latitude is ~111 km
            res = res * 111_320
        return {
            'width': src.width,
            'height': src.height,
            'bands': src.count,
            'resolution': f'{res:.0f} m' if res >= 1 else f'{res:.2f} m',
        }


def run_land_cover(image_path, name):
    """
    Land-cover prediction + 4-panel image for a 6+ band GeoTIFF.
    Returns (prediction, panel_filename, error_message).
    """
    if model is None:
        return None, None, model_error or "Model not loaded"
    try:
        prediction = predict_image(model, image_path)
        print(f"[OK] Prediction complete: {prediction['dominant_class']}")

        panel_filename = f"4panel_{name}.png"
        generate_4panel(model, image_path, os.path.join(OUTPUT_DIR, panel_filename))
        if not os.path.exists(os.path.join(OUTPUT_DIR, panel_filename)):
            panel_filename = None
        return prediction, panel_filename, None
    except Exception as e:
        print(f"[ERROR] Prediction/4-panel generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None, 'Model inference failed for this image'


@app.errorhandler(404)
def not_found(_):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(405)
def method_not_allowed(_):
    return jsonify({'error': 'Method not allowed'}), 405


@app.errorhandler(413)
def too_large(_):
    return jsonify({'error': 'File is too large (limit 200 MB)'}), 413


@app.route('/', methods=['GET'])
def index():
    """Opening the API address in a browser shows what is running instead of a 404."""
    return jsonify({
        'service': 'GeoSight API',
        'status': 'ok',
        'frontend': 'http://localhost:5173',
        'endpoints': ['/api/health', '/api/fetch-image', '/api/predict-upload',
                      '/api/detect-roads', '/api/download/<filename>'],
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'GeoSight backend is running',
        'earth_engine': 'connected' if EE_INITIALIZED else 'not configured',
        'classification_model': 'loaded' if model is not None else 'missing',
        'road_model': 'loaded' if road_model is not None else 'missing',
    })


@app.route('/api/fetch-image', methods=['POST'])
def fetch_image():
    """
    Fetch a Sentinel-2 image from GEE and run land-cover classification.

    Expected JSON body:
    {
        "bounds": {"minLon": 77.0, "minLat": 28.5, "maxLon": 77.1, "maxLat": 28.6},
        "cloudCover": 10,
        "startDate": "2024-01-01",
        "endDate": "2024-12-31"
    }
    """
    if not EE_INITIALIZED:
        return earth_engine_unavailable()

    try:
        params, error = parse_analysis_request()
        if error:
            return error

        print(f"\n[*] Fetching image for bounds {params['bounds']}, cloud cover <{params['cloud_cover']}%, "
              f"{params['start_date']} to {params['end_date']}")
        region, image = get_median_composite(params)
        if image is None:
            return no_images_found(params)

        final_image = land_cover_bands(image)
        name = output_name(params)
        filename = f"sentinel2_{name}.tif"
        output_path = os.path.join(OUTPUT_DIR, filename)
        download_geotiff(final_image, region, output_path, bands=LAND_COVER_BANDS)

        info = raster_info(output_path)
        info['band_order'] = LAND_COVER_BANDS

        prediction_result, panel_filename, prediction_error = run_land_cover(output_path, name)

        response_data = {
            'success': True,
            'message': 'Image fetched successfully',
            'file': filename,
            'info': info,
        }
        if prediction_result:
            response_data['prediction'] = prediction_result
            if panel_filename:
                response_data['visualization_4panel'] = panel_filename
        else:
            response_data['prediction_error'] = prediction_error
        return jsonify(response_data)

    except Exception as e:
        return server_error('Image analysis', e)


@app.route('/api/predict-upload', methods=['POST'])
def predict_upload():
    """
    Run land-cover classification on an uploaded GeoTIFF.

    Form-data field "file": a .tif/.tiff with at least 6 bands in the order
    B2, B3, B4, B8, B11, B12 (Sentinel-2 surface reflectance, 0-10000).
    """
    from rasterio.errors import RasterioIOError

    uploaded = request.files.get('file')
    if uploaded is None or uploaded.filename == '':
        return jsonify({'error': 'No file uploaded'}), 400

    if not uploaded.filename.lower().endswith(('.tif', '.tiff')):
        return jsonify({'error': 'Please upload a GeoTIFF (.tif / .tiff) file'}), 400

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base = os.path.splitext(secure_filename(uploaded.filename))[0] or 'image'
    filename = f"upload_{base}_{timestamp}.tif"
    output_path = os.path.join(OUTPUT_DIR, filename)
    uploaded.save(output_path)
    print(f"\n[*] Uploaded file saved to: {output_path}")

    if os.path.getsize(output_path) == 0:
        os.remove(output_path)
        return jsonify({'error': 'Uploaded file is empty'}), 400

    try:
        info = raster_info(output_path)
    except RasterioIOError:
        os.remove(output_path)
        return jsonify({'error': 'File is not a valid GeoTIFF'}), 400

    if info['bands'] < 6:
        os.remove(output_path)
        return jsonify({
            'error': f"Image has {info['bands']} band(s); the model needs 6 "
                     "(B2, B3, B4, B8, B11, B12). Use \"Select from Map\" for other areas."
        }), 400

    if model is None:
        return jsonify({'error': model_error or 'Classification model not loaded on the server'}), 503

    prediction_result, panel_filename, prediction_error = run_land_cover(output_path, f"upload_{base}_{timestamp}")
    if prediction_result is None:
        return jsonify({'error': prediction_error}), 500

    response_data = {
        'success': True,
        'message': 'Image classified successfully',
        'file': filename,
        'info': info,
        'prediction': prediction_result,
    }
    if panel_filename:
        response_data['visualization_4panel'] = panel_filename
    return jsonify(response_data)


@app.route('/api/detect-roads', methods=['POST'])
def detect_roads():
    """
    Fetch an RGB Sentinel-2 image from GEE and detect roads in it.
    Same JSON body as /api/fetch-image.
    """
    if not EE_INITIALIZED:
        return earth_engine_unavailable()

    try:
        params, error = parse_analysis_request()
        if error:
            return error

        print(f"\n[*] Detecting roads for bounds {params['bounds']}")
        region, image = get_median_composite(params)
        if image is None:
            return no_images_found(params)

        # Road model input: B4, B3, B2 (RGB), same order as in training
        rgb_image = ee.Image.cat([
            image.select('B4').toFloat(),
            image.select('B3').toFloat(),
            image.select('B2').toFloat()
        ])
        name = output_name(params)
        filename = f"road_input_{name}.tif"
        output_path = os.path.join(OUTPUT_DIR, filename)
        download_geotiff(rgb_image, region, output_path)

        road_result = None
        road_error = None
        viz_filename = None

        if road_model is not None:
            try:
                print("[*] Running road detection...")
                road_result = predict_roads(road_model, output_path, device=device)
                print(f"[OK] Road detection complete: {road_result['road_percentage']:.2f}% roads")

                viz_filename = f"road_viz_{name}.png"
                viz_path = os.path.join(OUTPUT_DIR, viz_filename)
                generate_road_visualization(road_model, output_path, viz_path)
                if not os.path.exists(viz_path):
                    viz_filename = None
            except Exception as e:
                print(f"[ERROR] Road detection failed: {e}")
                import traceback
                traceback.print_exc()
                road_error = 'Road detection failed for this image'
        else:
            road_error = road_model_error or "Road model not loaded"

        response_data = {
            'success': True,
            'message': 'Road detection completed',
            'file': filename,
            'model': 'RoadExpert (ResNet-50)'
        }
        if road_result:
            response_data['road_detection'] = {
                'road_percentage': road_result['road_percentage'],
                'road_pixels': road_result['road_pixels'],
                'total_pixels': road_result['total_pixels']
            }
            if viz_filename:
                response_data['visualization'] = viz_filename
        else:
            response_data['error'] = road_error
        return jsonify(response_data)

    except Exception as e:
        return server_error('Road detection', e)


@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download a generated GeoTIFF or PNG from OUTPUT_DIR (and nowhere else)."""
    lower = filename.lower()
    if lower.endswith('.png'):
        mimetype, as_attachment = 'image/png', False      # display in browser
    elif lower.endswith(('.tif', '.tiff')):
        mimetype, as_attachment = 'image/tiff', True      # download
    else:
        return jsonify({'error': 'Only .png and .tif files can be downloaded'}), 400

    # send_from_directory rejects names that resolve outside OUTPUT_DIR
    # (e.g. "..\\secret.png" or absolute paths) with a 404.
    return send_from_directory(OUTPUT_DIR, filename, mimetype=mimetype, as_attachment=as_attachment)


if __name__ == '__main__':
    host = os.environ.get("GEOSIGHT_HOST", "127.0.0.1")
    port = int(os.environ.get("GEOSIGHT_PORT", "5000"))
    debug = os.environ.get("GEOSIGHT_DEBUG") == "1"

    print("=" * 60)
    print("GEOSIGHT FLASK BACKEND")
    print("=" * 60)
    print("\nEndpoints:")
    print("  GET  /api/health")
    print("  POST /api/fetch-image     (Earth Engine image + land-cover prediction)")
    print("  POST /api/predict-upload  (uploaded GeoTIFF + land-cover prediction)")
    print("  POST /api/detect-roads    (Earth Engine image + road detection)")
    print("  GET  /api/download/<filename>")
    print(f"\nModel: {MODEL_PATH}")
    print(f"Allowed frontend origins: {', '.join(CORS_ORIGINS)}")
    print(f"Starting server on http://{host}:{port} (debug={'on' if debug else 'off'})")
    if host not in ('127.0.0.1', 'localhost'):
        print("[WARNING] The API is reachable from other computers on this network.")
    print("=" * 60)

    app.run(debug=debug, host=host, port=port)
