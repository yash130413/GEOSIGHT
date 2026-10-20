import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import AnimatedCounter from '../common/AnimatedCounter';
import './EnhancedPredictionCard.css';

function EnhancedPredictionCard({ prediction }) {
  const [showBars, setShowBars] = useState(false);

  useEffect(() => {
    if (prediction) {
      const timer = setTimeout(() => setShowBars(true), 800);
      return () => clearTimeout(timer);
    }
  }, [prediction]);

  if (!prediction) return null;

  const { category, confidence, classDistribution, imageSize, totalPixels, isRoadDetection, roadCoverage, roadPixels } = prediction;
  
  // Every value below comes straight from the backend response.
  const features = isRoadDetection ? [
    { label: 'Road Coverage', value: roadCoverage, confidence: null, color: '#D97706' },
    { label: 'Non-Road Area', value: 100 - roadCoverage, confidence: null, color: 'var(--background-class)' }
  ] : Object.entries(classDistribution || {}).map(([name, stats]) => ({
      label: name,
      value: stats.percentage,
      confidence: stats.confidence,
      color: name === 'Urban' ? 'var(--urban)' : name === 'Rural' ? 'var(--rural)' : name === 'Water' ? 'var(--water)' : 'var(--background-class)'
    }));

  // Ring: mean model confidence for land cover; for roads there is no
  // calibrated confidence, so the ring shows road coverage instead.
  const ringValue = Math.min(Math.max((isRoadDetection ? roadCoverage / 100 : confidence) || 0, 0), 1);
  const ringLabel = isRoadDetection ? 'Road Coverage' : 'Mean Confidence';

  return (
    <motion.div 
      className="enhanced-prediction-card"
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.6 }}
      whileHover={{ y: -4 }}
    >
      <div className="prediction-header">
        <motion.div 
          className={`category-badge category-${category.toLowerCase().replace(/\s+/g, '-')}`}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.5, delay: 0.2, type: 'spring' }}
        >
          {category}
        </motion.div>
        
        <div className="confidence-section">
          <div className="confidence-ring">
            <motion.div 
              className="ring-progress"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: ringValue }}
              transition={{ duration: 1.2, delay: 0.4, ease: 'easeOut' }}
            >
              <svg viewBox="0 0 100 100">
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="var(--accent-soft)"
                  strokeWidth="8"
                />
                <motion.circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="var(--accent)"
                  strokeWidth="8"
                  strokeLinecap="round"
                  strokeDasharray={`${2 * Math.PI * 45}`}
                  strokeDashoffset={`${2 * Math.PI * 45 * (1 - ringValue)}`}
                  transform="rotate(-90 50 50)"
                  initial={{ strokeDashoffset: `${2 * Math.PI * 45}` }}
                  animate={{ strokeDashoffset: `${2 * Math.PI * 45 * (1 - ringValue)}` }}
                  transition={{ duration: 1.2, delay: 0.4, ease: 'easeOut' }}
                />
              </svg>
            </motion.div>
            <div className="confidence-value">
              <AnimatedCounter end={Math.round(ringValue * 100)} suffix="%" />
            </div>
          </div>
          <p className="confidence-label">{ringLabel}</p>
        </div>
      </div>

      <div className="features-breakdown">
        <h4>Feature Analysis</h4>
        <div className="feature-bars">
          {features.map((feature, index) => (
            <div key={index} className="feature-item">
              <div className="feature-header">
                <span className="feature-label">{feature.label}</span>
                <div className="feature-stats">
                  <span className="feature-value">{Math.round(feature.value)}%</span>
                  {feature.confidence !== null && feature.confidence !== undefined && (
                    <span className="feature-confidence">
                      ({(feature.confidence * 100).toFixed(1)}% conf)
                    </span>
                  )}
                </div>
              </div>
              <div className="feature-bar-container">
                <motion.div 
                  className="feature-bar"
                  style={{ backgroundColor: feature.color }}
                  initial={{ width: 0 }}
                  animate={{ width: showBars ? `${feature.value}%` : 0 }}
                  transition={{ duration: 0.8, delay: 0.6 + index * 0.1, ease: 'easeOut' }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="inference-info">
        <div className="info-item">
          <span className="info-label">Model</span>
          <span className="info-value">{isRoadDetection ? 'RoadExpert' : 'Epoch 11'}</span>
        </div>
        {imageSize && (
          <div className="info-item">
            <span className="info-label">Image Size</span>
            <span className="info-value">{imageSize.width}x{imageSize.height}</span>
          </div>
        )}
        {totalPixels && (
          <div className="info-item">
            <span className="info-label">Total Pixels</span>
            <span className="info-value">{(totalPixels / 1000000).toFixed(2)}M</span>
          </div>
        )}
        {isRoadDetection && roadPixels && (
          <div className="info-item">
            <span className="info-label">Road Pixels</span>
            <span className="info-value">{(roadPixels / 1000).toFixed(1)}K</span>
          </div>
        )}
      </div>
    </motion.div>
  );
}

export default EnhancedPredictionCard;