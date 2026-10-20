import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import 'leaflet-draw';
import Button from '../common/Button';
import { analyzeRegion, classifyUpload, isSupportedUpload, SUPPORTED_UPLOAD_EXTENSIONS } from '../../services/api';
import './MapUploadPanel.css';

import Icon from '../common/Icon';
// Fix Leaflet default icon paths
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});



function MapUploadPanel({ onClassify, processing }) {
  const [useMap, setUseMap] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [selectedBounds, setSelectedBounds] = useState(null);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [manualLat, setManualLat] = useState('');
  const [manualLon, setManualLon] = useState('');
  const [fetchStatus, setFetchStatus] = useState(null);
  const [fetchedImageData, setFetchedImageData] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [placeName, setPlaceName] = useState('');
  const [searchingPlace, setSearchingPlace] = useState(false);
  const [selectedModel, setSelectedModel] = useState('classification'); // 'classification' or 'roads'
  const fileInputRef = useRef(null);
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const drawnItemsRef = useRef(null);

  useEffect(() => {
    if (useMap && mapRef.current && !mapInstanceRef.current) {
      setTimeout(() => {
        try {
          console.log('[Map] Initializing map...');
          const map = L.map(mapRef.current, {
            zoomControl: true,
            attributionControl: true,
            preferCanvas: false
          }).setView([20.5937, 78.9629], 5);
          
          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
          }).addTo(map);
          
          console.log('[Map] Creating FeatureGroup...');
          const drawnItems = new L.FeatureGroup();
          map.addLayer(drawnItems);
          drawnItemsRef.current = drawnItems;
          
          console.log('[Map] Adding draw control...');
          const drawControl = new L.Control.Draw({
            position: 'topright',
            draw: {
              rectangle: {
                shapeOptions: {
                  color: '#3b82f6',
                  weight: 2,
                  fillOpacity: 0.2
                },
                showArea: false,  // Disable area display to avoid the bug
                metric: false,
                repeatMode: false
              },
              polygon: false,
              circle: false,
              circlemarker: false,
              marker: false,
              polyline: false
            },
            edit: {
              featureGroup: drawnItems,
              remove: true
            }
          });
          map.addControl(drawControl);
          console.log('[Map] Draw control added successfully');
          
          // Log when draw starts
          map.on('draw:drawstart', (e) => {
            console.log('[Map] Draw started:', e.layerType);
          });
          
          map.on('draw:drawstop', () => {
            console.log('[Map] Draw stopped');
          });
          
          map.on(L.Draw.Event.CREATED, (e) => {
            console.log('[Map] Rectangle created!');
            const layer = e.layer;
            drawnItems.clearLayers();
            drawnItems.addLayer(layer);
            
            const bounds = layer.getBounds();
            const boundsData = {
              minLon: bounds.getWest(),
              minLat: bounds.getSouth(),
              maxLon: bounds.getEast(),
              maxLat: bounds.getNorth()
            };
            console.log('[Map] Bounds:', boundsData);
            setSelectedBounds(boundsData);
            setErrorMessage(null);
            setFetchedImageData(null);
          });
          
          map.on(L.Draw.Event.EDITED, (e) => {
            console.log('[Map] Rectangle edited');
            const layers = e.layers;
            layers.eachLayer((layer) => {
              const bounds = layer.getBounds();
              setSelectedBounds({
                minLon: bounds.getWest(),
                minLat: bounds.getSouth(),
                maxLon: bounds.getEast(),
                maxLat: bounds.getNorth()
              });
            });
          });
          
          map.on(L.Draw.Event.DELETED, () => {
            console.log('[Map] Rectangle deleted');
            setSelectedBounds(null);
            setErrorMessage(null);
            setFetchedImageData(null);
          });
          
          if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
              (position) => {
                map.setView([position.coords.latitude, position.coords.longitude], 13);
                setCurrentLocation({
                  lat: position.coords.latitude,
                  lon: position.coords.longitude
                });
              },
              () => {
                console.log('[Map] Location access denied, using default location');
              }
            );
          }
          
          setTimeout(() => {
            map.invalidateSize();
            console.log('[Map] Map size invalidated');
          }, 100);
          
          mapInstanceRef.current = map;
          console.log('[Map] Map initialized successfully');
        } catch (error) {
          console.error('[Map] Error initializing map:', error);
        }
      }, 100);
    }
    
    return () => {
      if (mapInstanceRef.current) {
        console.log('[Map] Cleaning up map instance');
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [useMap]);

  const handleFileChange = (file) => {
    setFetchStatus(null);
    setFetchedImageData(null);
    if (!file) return;
    if (file.size === 0) {
      setSelectedFile(null);
      setErrorMessage(`"${file.name}" is empty.`);
      return;
    }
    if (!isSupportedUpload(file)) {
      // The model needs 6 Sentinel-2 bands, which JPG/PNG files cannot hold
      setSelectedFile(null);
      setErrorMessage(
        `"${file.name}" is not supported. Upload a 6-band Sentinel-2 GeoTIFF (${SUPPORTED_UPLOAD_EXTENSIONS.join(', ')}) ` +
        'with bands B2, B3, B4, B8, B11, B12, or use "Select from Map" instead.'
      );
      return;
    }
    setErrorMessage(null);
    setSelectedFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFileChange(e.dataTransfer.files[0]);
  };

  const handleUploadClassify = async () => {
    if (!selectedFile) {
      setErrorMessage('Please choose a GeoTIFF file first');
      return;
    }

    setFetchStatus('fetching');
    setErrorMessage(null);
    setFetchedImageData(null);

    try {
      const data = await classifyUpload(selectedFile);
      if (data.prediction) {
        setFetchStatus('success');
        setFetchedImageData(data);
        onClassify(null, 'upload', data.prediction, data.visualization_4panel);
      } else {
        setFetchStatus('error');
        setErrorMessage('Prediction failed: ' + (data.prediction_error || 'unknown error'));
      }
    } catch (err) {
      setFetchStatus('error');
      setErrorMessage(err.message);
    }
  };

  const handleGetLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const location = {
            lat: position.coords.latitude,
            lon: position.coords.longitude
          };
          setCurrentLocation(location);
          if (mapInstanceRef.current) {
            mapInstanceRef.current.setView([location.lat, location.lon], 13);
          }
        },
        (error) => {
          alert('Unable to get location: ' + error.message);
        }
      );
    } else {
      alert('Geolocation is not supported by your browser');
    }
  };

  const handleGoToCoordinates = () => {
    const lat = parseFloat(manualLat);
    const lon = parseFloat(manualLon);
    
    if (isNaN(lat) || isNaN(lon)) {
      alert('Please enter valid coordinates');
      return;
    }
    
    if (lat < -90 || lat > 90) {
      alert('Latitude must be between -90 and 90');
      return;
    }
    
    if (lon < -180 || lon > 180) {
      alert('Longitude must be between -180 and 180');
      return;
    }
    
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setView([lat, lon], 13);
      setCurrentLocation({ lat, lon });
    }
  };

  const handleFetchByCoordinates = async () => {
    const lat = parseFloat(manualLat);
    const lon = parseFloat(manualLon);
    
    if (isNaN(lat) || isNaN(lon)) {
      setErrorMessage('Please enter valid coordinates');
      return;
    }
    
    if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
      setErrorMessage('Invalid coordinate range');
      return;
    }
    
    // Create a small bounding box around the coordinates (0.02 degrees ~ 2km)
    const offset = 0.01;
    const bounds = {
      minLon: lon - offset,
      minLat: lat - offset,
      maxLon: lon + offset,
      maxLat: lat + offset
    };
    
    setSelectedBounds(bounds);
    await analyzeBounds(bounds);
  };

  const handleFetchAndClassify = async () => {
    if (!selectedBounds) {
      setErrorMessage('Please draw a rectangle on the map first');
      return;
    }
    
    await analyzeBounds(selectedBounds);
  };

  // Fetch Sentinel-2 imagery for the bounds and run the selected model
  const analyzeBounds = async (bounds) => {
    setFetchStatus('fetching');
    setErrorMessage(null);
    setFetchedImageData(null);

    try {
      const data = await analyzeRegion(selectedModel, bounds);
      if (selectedModel === 'roads' && data.road_detection) {
        setFetchStatus('success');
        setFetchedImageData(data);
        onClassify(null, 'roads', data.road_detection, data.visualization);
      } else if (selectedModel === 'classification' && data.prediction) {
        setFetchStatus('success');
        setFetchedImageData(data);
        onClassify(null, 'map', data.prediction, data.visualization_4panel);
      } else {
        setFetchStatus('error');
        setErrorMessage('Prediction failed: ' + (data.prediction_error || data.error || 'unknown error'));
      }
    } catch (err) {
      setFetchStatus('error');
      setErrorMessage(err.message);
    }
  };
  
  const searchPlace = async () => {
    if (!placeName.trim()) {
      setErrorMessage('Please enter a place name');
      return;
    }

    setSearchingPlace(true);
    setErrorMessage(null);
    // Clear previous results when searching new place
    setFetchedImageData(null);
    setFetchStatus(null);

    try {
      // Using Nominatim (OpenStreetMap) geocoding API
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(placeName)}&limit=1`
      );
      
      const data = await response.json();
      
      if (data && data.length > 0) {
        const { lat, lon, display_name } = data[0];
        const latitude = parseFloat(lat);
        const longitude = parseFloat(lon);
        
        console.log(`Found: ${display_name} at ${latitude}, ${longitude}`);
        
        // Set coordinates in manual input fields
        setManualLat(latitude.toFixed(4));
        setManualLon(longitude.toFixed(4));
        
        // Navigate map to location
        if (mapInstanceRef.current) {
          mapInstanceRef.current.setView([latitude, longitude], 13);
          setCurrentLocation({ lat: latitude, lon: longitude });
        }
        
        setErrorMessage(null);
      } else {
        setErrorMessage(`Place "${placeName}" not found. Try a different name.`);
      }
    } catch (err) {
      setErrorMessage('Failed to search place: ' + err.message);
    } finally {
      setSearchingPlace(false);
    }
  };
  
  const handleSubmit = () => {
    if (useMap) {
      // Check if coordinates are entered but no rectangle drawn
      if (manualLat && manualLon && !selectedBounds) {
        handleFetchByCoordinates();
      } else {
        handleFetchAndClassify();
      }
    } else {
      handleUploadClassify();
    }
  };

  return (
    <div className="map-upload-panel">
      <motion.div 
        className="upload-section"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <h2>Image Source</h2>
        
        <div className="source-toggle">
          <button 
            className={!useMap ? 'active' : ''}
            onClick={() => { setUseMap(false); setErrorMessage(null); setFetchStatus(null); setFetchedImageData(null); }}
          >
            <Icon emoji="📁" /> Upload Image
          </button>
          <button 
            className={useMap ? 'active' : ''}
            onClick={() => { setUseMap(true); setErrorMessage(null); setFetchStatus(null); setFetchedImageData(null); }}
          >
            <Icon emoji="🗺️" /> Select from Map
          </button>
        </div>

        {!useMap ? (
          <>
            <div 
              className={`drop-zone ${dragOver ? 'drag-over' : ''} ${selectedFile ? 'has-file' : ''}`}
              onDrop={handleDrop}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onClick={() => fileInputRef.current?.click()}
            >
              <input 
                ref={fileInputRef}
                type="file" 
                accept={SUPPORTED_UPLOAD_EXTENSIONS.join(',')}
                onChange={(e) => handleFileChange(e.target.files[0])}
                style={{ display: 'none' }}
              />
              
              {!selectedFile ? (
                <div className="drop-content">
                  <div className="upload-icon"><Icon emoji="📡" /></div>
                  <h3>Drop satellite image here</h3>
                  <p>or click to browse files</p>
                  <div className="supported-formats">
                    <span>Supported: 6-band Sentinel-2 GeoTIFF (.tif)</span>
                  </div>
                </div>
              ) : (
                <div className="file-preview">
                  <div className="file-info">
                    <span className="file-name">{selectedFile.name}</span>
                    <span className="file-size">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</span>
                  </div>
                </div>
              )}
            </div>

            {errorMessage && (
              <div className="message-box error">
                <strong>Error:</strong> {errorMessage}
              </div>
            )}

            {fetchStatus === 'fetching' && (
              <div className="message-box info">
                <strong>Info:</strong> Running the land-cover model on your image...
              </div>
            )}
          </>
        ) : (
          <>
            <div className="map-mode">
              <div className="map-controls">
                <div className="model-selection">
                  <h4>Select Analysis Model</h4>
                  <div className="model-buttons">
                    <button
                      className={`model-btn ${selectedModel === 'classification' ? 'active' : ''}`}
                      onClick={() => {
                        setSelectedModel('classification');
                        setFetchedImageData(null);
                        setErrorMessage(null);
                      }}
                    >
                      <Icon emoji="🌍" /> Land Classification
                    </button>
                    <button
                      className={`model-btn ${selectedModel === 'roads' ? 'active' : ''}`}
                      onClick={() => {
                        setSelectedModel('roads');
                        setFetchedImageData(null);
                        setErrorMessage(null);
                      }}
                    >
                      <Icon emoji="🛣️" /> Road Detection
                    </button>
                  </div>
                  <p className="model-description">
                    {selectedModel === 'classification'
                      ? 'Classifies terrain into: Background, Rural, Urban, Water'
                      : 'Detects and segments road networks from satellite imagery'}
                  </p>
                </div>

                <div className="location-section">
                  <div className="place-search-section">
                    <h4><Icon emoji="🔍" /> Search by Place Name</h4>
                    <div className="place-search-input">
                      <input
                        type="text"
                        placeholder="e.g., Delhi, Mumbai, Bareilly"
                        value={placeName}
                        onChange={(e) => setPlaceName(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && searchPlace()}
                      />
                      <button
                        className="search-place-btn"
                        onClick={searchPlace}
                        disabled={searchingPlace || !placeName.trim()}
                      >
                        {searchingPlace ? 'Searching...' : 'Search'}
                      </button>
                    </div>
                    <p className="helper-text">Map will navigate to the location and fill coordinates</p>
                  </div>

                  <div className="divider-text">OR</div>

                  <button className="location-btn" onClick={handleGetLocation}>
                    <Icon emoji="📍" /> Get Current Location
                  </button>

                  <div className="divider-text">OR</div>

                  <div className="manual-coords">
                    <h4>Enter Coordinates Manually</h4>
                    <div className="coords-input-group">
                      <input
                        type="number"
                        placeholder="Latitude (e.g., 28.6139)"
                        value={manualLat}
                        onChange={(e) => setManualLat(e.target.value)}
                        step="0.0001"
                        min="-90"
                        max="90"
                      />
                      <input
                        type="number"
                        placeholder="Longitude (e.g., 77.2090)"
                        value={manualLon}
                        onChange={(e) => setManualLon(e.target.value)}
                        step="0.0001"
                        min="-180"
                        max="180"
                      />
                      <div className="coord-buttons">
                        <button className="go-btn" onClick={handleGoToCoordinates}>
                          View on Map
                        </button>
                        <button className="fetch-direct-btn" onClick={handleFetchByCoordinates}>
                          Fetch Directly
                        </button>
                      </div>
                    </div>
                  </div>

                  {currentLocation && (
                    <div className="location-display">
                      <p><Icon emoji="📍" /> Lat: {currentLocation.lat.toFixed(4)}, Lon: {currentLocation.lon.toFixed(4)}</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="map-stage">
                <div className="map-container" ref={mapRef}></div>

                {selectedBounds ? (
                  <div className="bounds-display">
                    <h4>Selected Area</h4>
                    <div className="coords-list">
                      <div><span>Min Lon:</span> <span>{selectedBounds.minLon.toFixed(4)}</span></div>
                      <div><span>Min Lat:</span> <span>{selectedBounds.minLat.toFixed(4)}</span></div>
                      <div><span>Max Lon:</span> <span>{selectedBounds.maxLon.toFixed(4)}</span></div>
                      <div><span>Max Lat:</span> <span>{selectedBounds.maxLat.toFixed(4)}</span></div>
                    </div>
                  </div>
                ) : (
                  <div className="no-selection-msg">
                    No area selected. Use the rectangle tool to draw on the map.
                  </div>
                )}

                {errorMessage && (
                  <div className="message-box error">
                    <strong>Error:</strong> {errorMessage}
                  </div>
                )}

                {fetchStatus === 'fetching' && (
                  <div className="message-box info">
                    <strong>Info:</strong> Fetching image from Google Earth Engine...
                  </div>
                )}

                {fetchedImageData && (
                  <div className="message-box success">
                    <strong><Icon emoji="✅" /> Analysis Complete!</strong>
                    <div className="prediction-summary">
                      {selectedModel === 'classification' && fetchedImageData.prediction && (
                        <>
                          <h4>Dominant Class: {fetchedImageData.prediction.dominant_class}</h4>
                          <div className="class-breakdown">
                            {Object.entries(fetchedImageData.prediction.class_distribution).map(([className, stats]) => (
                              <div key={className} className="class-stat">
                                <span className="class-name">{className}:</span>
                                <span className="class-percentage">{stats.percentage}%</span>
                                <span className="class-confidence">(confidence: {(stats.confidence * 100).toFixed(1)}%)</span>
                              </div>
                            ))}
                          </div>
                          <p className="image-details">
                            <strong>Image:</strong> {fetchedImageData.info.width} x {fetchedImageData.info.height} px
                            {' | '}{fetchedImageData.info.bands} bands
                            {fetchedImageData.info.bands > 6 ? ' (model uses the first 6)' : ''}
                            {' | '}{fetchedImageData.info.resolution}
                          </p>
                        </>
                      )}
                      {selectedModel === 'roads' && fetchedImageData.road_detection && (
                        <>
                          <h4>Road Detection Results</h4>
                          <div className="class-breakdown">
                            <div className="class-stat">
                              <span className="class-name">Road Coverage:</span>
                              <span className="class-percentage">{fetchedImageData.road_detection.road_percentage.toFixed(2)}%</span>
                            </div>
                            <div className="class-stat">
                              <span className="class-name">Road Pixels:</span>
                              <span className="class-percentage">{fetchedImageData.road_detection.road_pixels.toLocaleString()}</span>
                            </div>
                            <div className="class-stat">
                              <span className="class-name">Total Pixels:</span>
                              <span className="class-percentage">{fetchedImageData.road_detection.total_pixels.toLocaleString()}</span>
                            </div>
                          </div>
                          <p className="image-details">
                            <strong>Model:</strong> {fetchedImageData.model}
                          </p>
                        </>
                      )}
                    </div>
                  </div>
                )}

                <div className="instructions-box">
                  <h4>Two Ways to Analyze:</h4>
                  <ol>
                    <li><strong>Method 1 - Direct Coordinates:</strong> Enter Lat/Lon and click "Fetch Directly" (creates 2km x 2km area)</li>
                    <li><strong>Method 2 - Draw on Map:</strong> Click rectangle tool, draw custom area, then click "Analyze with AI Model"</li>
                  </ol>
                </div>
              </div>
            </div>
          </>
        )}

        <Button 
          onClick={handleSubmit}
          disabled={processing || fetchStatus === 'fetching' || (useMap ? !selectedBounds : !selectedFile)}
          className={`classify-btn ${processing || fetchStatus === 'fetching' ? 'processing' : ''}`}
        >
          {processing ? 'Analyzing...' : fetchStatus === 'fetching' ? (useMap ? 'Fetching & Analyzing...' : 'Analyzing...') : useMap ? 'Analyze with AI Model' : 'Run Classification'}
        </Button>
      </motion.div>
    </div>
  );
}

export default MapUploadPanel;
