import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import MapUploadPanel from '../components/demo/MapUploadPanel';
import EnhancedPredictionCard from '../components/demo/EnhancedPredictionCard';
import ProcessingOverlay from '../components/demo/ProcessingOverlay';
import ModelInfoPanel from '../components/demo/ModelInfoPanel';
import FourPanelVisualization from '../components/demo/FourPanelVisualization';
import RoadVisualization from '../components/demo/RoadVisualization';
import { getFileUrl } from '../services/api';
import './LiveDemo.css';

import Icon, { IconText } from '../components/common/Icon';
function LiveDemo() {
  const [prediction, setPrediction] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [fourPanelUrl, setFourPanelUrl] = useState(null);
  const [showFourPanel, setShowFourPanel] = useState(false);
  const [vizMode, setVizMode] = useState('classification');

  // Called by MapUploadPanel once the backend has returned a real prediction.
  // region: 'roads' for road detection, anything else for land-cover classification
  const handleClassify = async (file, region, predictionData, visualizationFile) => {
    if (!predictionData) return;

    setProcessing(true);
    setPrediction(null);
    setFourPanelUrl(null);
    setShowFourPanel(false);
    setVizMode(region === 'roads' ? 'roads' : 'classification');

    try {
      // Short pause so the processing animation is visible
      await new Promise(resolve => setTimeout(resolve, 500));

      if (region === 'roads') {
        // The road model gives a per-pixel mask, not a calibrated confidence,
        // so the card shows road coverage instead of a confidence score.
        setPrediction({
          category: 'Road Network',
          roadCoverage: predictionData.road_percentage,
          roadPixels: predictionData.road_pixels,
          totalPixels: predictionData.total_pixels,
          isRoadDetection: true
        });
      } else {
        setPrediction({
          category: predictionData.dominant_class,
          // Mean softmax probability of the pixels assigned to the dominant class
          confidence: predictionData.class_distribution[predictionData.dominant_class].confidence,
          classDistribution: predictionData.class_distribution,
          imageSize: predictionData.image_size,
          totalPixels: predictionData.total_pixels,
          isRoadDetection: false
        });
      }

      if (visualizationFile) {
        setFourPanelUrl(`${getFileUrl(visualizationFile)}?t=${Date.now()}`);
      }
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="live-demo">
      <motion.div 
        className="demo-header"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <h1>AI Classification Dashboard</h1>
        <p>Real-time satellite imagery analysis using deep learning</p>
      </motion.div>
      
      <div className="demo-layout">
        <motion.div 
          className="demo-left"
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <MapUploadPanel 
            onClassify={handleClassify} 
            processing={processing}
          />
          
          {processing && <ProcessingOverlay />}
        </motion.div>
        
        <motion.div 
          className="demo-right"
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <AnimatePresence mode="wait">
            {!prediction && !processing && (
              <motion.div 
                key="empty"
                className="empty-state"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.4 }}
              >
                <div className="empty-icon"><Icon emoji="🛰️" /></div>
                <h3>Ready for Analysis</h3>
                <p>Upload a GeoTIFF or select an area on the map to begin.</p>
              </motion.div>
            )}
            
            {prediction && (
              <motion.div
                key="results"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.6 }}
              >
                <EnhancedPredictionCard prediction={prediction} />
                {fourPanelUrl && (
                  <motion.button
                    className="view-4panel-btn"
                    onClick={() => setShowFourPanel(true)}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <IconText text={vizMode === 'roads' ? '🛣️ View Road Detection Visualization' : '🖼️ View 4-Panel Visualization'} />
                  </motion.button>
                )}
                <ModelInfoPanel isRoadDetection={prediction?.isRoadDetection} />
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
      
      <AnimatePresence>
        {showFourPanel && fourPanelUrl && vizMode === 'roads' && (
          <RoadVisualization
            imageUrl={fourPanelUrl}
            onClose={() => setShowFourPanel(false)}
          />
        )}
        {showFourPanel && fourPanelUrl && vizMode === 'classification' && (
          <FourPanelVisualization
            imageUrl={fourPanelUrl}
            onClose={() => setShowFourPanel(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export default LiveDemo;
