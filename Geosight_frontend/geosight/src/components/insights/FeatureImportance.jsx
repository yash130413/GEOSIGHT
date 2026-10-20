import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Card from '../common/Card';
import './FeatureImportance.css';

import Icon from '../common/Icon';
function FeatureImportance({ model = 'classification' }) {
  const [selectedFeature, setSelectedFeature] = useState(null);

  const classificationFeatures = [
    { name: 'B8 — NIR (Near Infrared)', color: '#22c55e', impact: 'Most discriminative band. High NIR = dense vegetation (Rural). Low NIR = built-up (Urban). Critical for NDVI computation.', usage: 'Primary' },
    { name: 'B11 — SWIR1',             color: '#f59e0b', impact: 'SWIR1 separates built-up from bare soil. Used in NDBI = (SWIR1 - NIR) / (SWIR1 + NIR). Key for Urban detection.', usage: 'Primary' },
    { name: 'B4 — Red',                color: '#ef4444', impact: 'Red band used in NDVI = (NIR - Red) / (NIR + Red). Vegetation absorbs red light strongly.', usage: 'Primary' },
    { name: 'B12 — SWIR2',             color: '#0E8BB5', impact: 'SWIR2 enhances discrimination of dry vegetation vs urban surfaces. Complements B11 for built-up index.', usage: 'Primary' },
    { name: 'B2 — Blue',               color: '#3b82f6', impact: 'Blue band helps detect water bodies (high reflectance). Used in RGB composite for visual context.', usage: 'Secondary' },
    { name: 'B3 — Green',              color: '#10b981', impact: 'Green band used in NDWI = (Green - NIR) / (Green + NIR) for water detection. Supports RGB visualization.', usage: 'Secondary' },
  ];

  const roadFeatures = [
    { name: 'B4 — Red Channel',   color: '#ef4444', impact: 'Roads appear as bright linear features in red channel. High contrast against vegetation.', usage: 'Primary' },
    { name: 'B3 — Green Channel', color: '#10b981', impact: 'Green channel captures road surface texture and distinguishes asphalt from soil.', usage: 'Primary' },
    { name: 'B2 — Blue Channel',  color: '#3b82f6', impact: 'Blue channel completes RGB input. Helps distinguish water channels from roads.', usage: 'Primary' },
    { name: 'ImageNet Norm',       color: '#0E8BB5', impact: 'ImageNet mean/std normalization critical — model trained on normalized RGB, not raw DN values.', usage: 'Primary' },
    { name: 'Morphological Skel.', color: '#f59e0b', impact: 'Post-processing skeleton thins road predictions to single-pixel width for clean network visualization.', usage: 'Post-Process' },
    { name: 'cv2 Normalize',       color: '#0B6E99', impact: 'cv2.NORM_MINMAX scales raw Sentinel-2 DN values to 0-255 before ImageNet normalization.', usage: 'Pre-Process' },
  ];

  const features = model === 'roads' ? roadFeatures : classificationFeatures;

  return (
    <Card className="feature-importance">
      <div className="feature-header">
        <div>
          <h3>{model === 'roads' ? 'Road Model Input Features' : 'Sentinel-2 Input Bands'}</h3>
          <p className="feature-subtitle">{model === 'roads' ? 'RGB bands + preprocessing pipeline for RoadExpert (ResNet-50)' : '6 spectral bands used as input to the UNet++ land classification model'}</p>
        </div>
      </div>
      <div className="features-list">
        {features.map((feature, index) => (
          <motion.div
            key={feature.name}
            className={`feature-card ${selectedFeature === feature.name ? 'selected' : ''}`}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05 }}
            whileHover={{ scale: 1.05 }}
            onClick={() => setSelectedFeature(selectedFeature === feature.name ? null : feature.name)}
          >
            <div className="feature-icon" style={{ background: `linear-gradient(135deg, ${feature.color}, ${feature.color}dd)` }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
              </svg>
            </div>
            <div className="feature-content">
              <div className="feature-name">{feature.name}</div>
              <span className={`usage-badge ${feature.usage.toLowerCase()}`}>{feature.usage}</span>
            </div>
            <AnimatePresence mode="wait">
              {selectedFeature === feature.name && (
                <motion.div 
                  key="details"
                  className="feature-details"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="detail-row">
                    <span><Icon emoji="🎯" /> Impact:</span>
                    <span>{feature.impact}</span>
                  </div>
                  <div className="detail-row">
                    <span><Icon emoji="📊" /> Usage:</span>
                    <span className={`usage-badge ${feature.usage.toLowerCase()}`}>{feature.usage}</span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
    </Card>
  );
}

export default FeatureImportance;
