// All calls to the GeoSight Flask backend go through this file.
// Set VITE_API_BASE_URL in .env to point the frontend at a different backend.
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000').replace(/\/+$/, '');

// Earth Engine download + model inference can take a while on large areas
const ANALYSIS_TIMEOUT_MS = 5 * 60 * 1000;

export const SUPPORTED_UPLOAD_EXTENSIONS = ['.tif', '.tiff'];

export const isSupportedUpload = (file) =>
  !!file && SUPPORTED_UPLOAD_EXTENSIONS.some((ext) => file.name.toLowerCase().endsWith(ext));

/** URL for a file the backend generated (GeoTIFF or PNG visualization). */
export const getFileUrl = (filename) =>
  `${API_BASE_URL}/api/download/${encodeURIComponent(filename)}`;

/**
 * fetch() wrapper with a timeout and readable errors.
 * Resolves with the parsed JSON body; rejects with an Error whose message
 * is safe to show to the user.
 */
async function request(path, options = {}, timeoutMs = ANALYSIS_TIMEOUT_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...options, signal: controller.signal });
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error(`The backend did not respond within ${Math.round(timeoutMs / 1000)} seconds. Try a smaller area.`);
    }
    throw new Error(`Could not reach the backend at ${API_BASE_URL}. Is it running?`);
  } finally {
    clearTimeout(timer);
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    // Non-JSON body (e.g. a proxy error page)
  }

  if (!response.ok) {
    const message = data?.error || `Backend returned an error (HTTP ${response.status})`;
    throw new Error(data?.suggestion ? `${message}. ${data.suggestion}` : message);
  }
  if (!data) {
    throw new Error('Backend returned an empty or invalid response');
  }
  return data;
}

/**
 * Fetch a Sentinel-2 image for the given bounds and run a model on it.
 * model: 'classification' (land cover) or 'roads'
 */
export const analyzeRegion = (model, bounds) =>
  request(model === 'roads' ? '/api/detect-roads' : '/api/fetch-image', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      bounds,
      cloudCover: 10,
      startDate: '2024-01-01',
      endDate: '2024-12-31'
    })
  });

/** Run land-cover classification on an uploaded 6-band GeoTIFF. */
export const classifyUpload = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return request('/api/predict-upload', { method: 'POST', body: formData });
};
