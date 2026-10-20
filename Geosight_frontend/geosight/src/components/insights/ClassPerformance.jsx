import { useState } from 'react';
import { motion } from 'framer-motion';
import Card from '../common/Card';
import EvaluationPending from './EvaluationPending';
import evaluation from '../../data/modelEvaluation.json';
import './ClassPerformance.css';

import Icon from '../common/Icon';
function ClassPerformance({ model = 'classification' }) {
  const [selectedClass, setSelectedClass] = useState(null);
  const [sortBy, setSortBy] = useState('iou');

  // Measured values from Training/evaluate_models.py (src/data/modelEvaluation.json)
  const result = evaluation[model === 'roads' ? 'roads' : 'classification'];
  const style = {
    Background: { color: '#6b7280', icon: '🗺️' },
    Rural: { color: 'var(--rural)', icon: '🌾' },
    Urban: { color: 'var(--urban)', icon: '🏙️' },
    Water: { color: '#3b82f6', icon: '💧' },
    'Non-Road': { color: '#6b7280', icon: '🌿' },
    Road: { color: '#f59e0b', icon: '🛣️' },
  };

  if (!result) {
    return (
      <Card className="class-performance">
        <h3>Class-wise Performance</h3>
        <EvaluationPending model={model} />
      </Card>
    );
  }

  const classesData = result.classes.map((name) => ({
    name,
    ...style[name],
    iou: result.per_class[name].iou,
    precision: result.per_class[name].precision,
    recall: result.per_class[name].recall,
    f1Score: result.per_class[name].f1,
    pixels: result.per_class[name].pixels,
  }));

  const sortedClasses = [...classesData].sort((a, b) => b[sortBy] - a[sortBy]);

  return (
    <Card className="class-performance">
      <div className="class-header-section">
        <h3>Class-wise Performance</h3>
        <select 
          className="sort-select"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
        >
          <option value="iou">Sort by IoU</option>
          <option value="precision">Sort by Precision</option>
          <option value="recall">Sort by Recall</option>
          <option value="f1Score">Sort by F1-Score</option>
        </select>
      </div>
      <div className="class-list">
        {sortedClasses.map((cls, index) => (
          <motion.div
            key={cls.name}
            className={`class-item ${selectedClass === cls.name ? 'selected' : ''}`}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            onClick={() => setSelectedClass(selectedClass === cls.name ? null : cls.name)}
          >
            <div className="class-header">
              <span className="class-icon"><Icon emoji={cls.icon} /></span>
              <span className="class-name">{cls.name}</span>
            </div>
            <div className="class-metrics">
              <div className="metric-bar">
                <div className="metric-info">
                  <span>IoU</span>
                  <span className="metric-value">{cls.iou}%</span>
                </div>
                <div className="bar-container">
                  <motion.div
                    className="bar-fill"
                    style={{ backgroundColor: cls.color }}
                    initial={{ width: 0 }}
                    animate={{ width: `${cls.iou}%` }}
                    transition={{ delay: 0.3 + index * 0.1, duration: 0.8 }}
                  />
                </div>
              </div>
              <div className="metric-bar">
                <div className="metric-info">
                  <span>Precision</span>
                  <span className="metric-value">{cls.precision}%</span>
                </div>
                <div className="bar-container">
                  <motion.div
                    className="bar-fill"
                    style={{ backgroundColor: cls.color, opacity: 0.8 }}
                    initial={{ width: 0 }}
                    animate={{ width: `${cls.precision}%` }}
                    transition={{ delay: 0.4 + index * 0.1, duration: 0.8 }}
                  />
                </div>
              </div>
              <div className="metric-bar">
                <div className="metric-info">
                  <span>Recall</span>
                  <span className="metric-value">{cls.recall}%</span>
                </div>
                <div className="bar-container">
                  <motion.div
                    className="bar-fill"
                    style={{ backgroundColor: cls.color, opacity: 0.6 }}
                    initial={{ width: 0 }}
                    animate={{ width: `${cls.recall}%` }}
                    transition={{ delay: 0.5 + index * 0.1, duration: 0.8 }}
                  />
                </div>
              </div>
            </div>
            
            {selectedClass === cls.name && (
              <motion.div 
                className="class-details"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
              >
                <div className="detail-item">
                  <span>F1-Score:</span>
                  <strong>{cls.f1Score}%</strong>
                </div>
                <div className="detail-item">
                  <span>Validation Pixels:</span>
                  <strong>{cls.pixels.toLocaleString()}</strong>
                </div>
              </motion.div>
            )}
          </motion.div>
        ))}
      </div>
    </Card>
  );
}

export default ClassPerformance;
