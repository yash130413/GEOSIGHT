import { useState } from 'react';
import ModelSummary from '../components/insights/ModelSummary';
import ConfusionMatrix from '../components/insights/ConfusionMatrix';
import TrainingGraph from '../components/insights/TrainingGraph';
import PerformanceRadar from '../components/insights/PerformanceRadar';
import ClassPerformance from '../components/insights/ClassPerformance';
import FeatureImportance from '../components/insights/FeatureImportance';
import Icon from '../components/common/Icon';
import evaluation from '../data/modelEvaluation.json';
import './ModelInsights.css';

const STATS = {
  classification: [
    { value: '100', label: 'Best Quality Score' },
    { value: '42.5%', label: 'Urban Coverage' },
    { value: '76.2%', label: 'Urban+Rural Score' },
    { value: '70K+', label: 'Training Tiles' },
  ],
  roads: [
    { value: 'smp.Unet', label: 'Architecture' },
    { value: 'ResNet-50', label: 'Encoder' },
    { value: '256×256', label: 'Input Tile Size' },
    { value: '3 RGB', label: 'Input Channels' },
  ],
};

function ModelInsights() {
  const [activeModel, setActiveModel] = useState('classification');
  const hasEvaluation = Boolean(evaluation[activeModel]);
  // Land-cover radar uses the coverage analysis; the road radar needs measured metrics
  const showRadar = activeModel === 'classification' || hasEvaluation;

  return (
    <div className="insights-page">
      <header className="insights-header">
        <div>
          <h1>Model Performance Insights</h1>
          <p>Deep dive into AI-powered geospatial classification analytics</p>
        </div>

        <div className="model-switcher" role="tablist" aria-label="Model">
          <button
            role="tab"
            aria-selected={activeModel === 'classification'}
            className={`switcher-btn ${activeModel === 'classification' ? 'active' : ''}`}
            onClick={() => setActiveModel('classification')}
          >
            <Icon emoji="🌍" /> Land Classification
          </button>
          <button
            role="tab"
            aria-selected={activeModel === 'roads'}
            className={`switcher-btn ${activeModel === 'roads' ? 'active' : ''}`}
            onClick={() => setActiveModel('roads')}
          >
            <Icon emoji="🛣️" /> Road Detection
          </button>
        </div>
      </header>

      <section className="insights-stats" aria-label="Key figures">
        {STATS[activeModel].map((s) => (
          <div key={s.label} className="insights-stat">
            <span className="insights-stat-value">{s.value}</span>
            <span className="insights-stat-label">{s.label}</span>
          </div>
        ))}
      </section>

      <div className="insights-grid">
        <div className="span-2"><ModelSummary model={activeModel} /></div>
        {/* Accuracy panels only appear once Training/evaluate_models.py has produced real numbers */}
        {showRadar && <PerformanceRadar model={activeModel} />}
        <div className={showRadar ? '' : 'span-2'}><TrainingGraph model={activeModel} /></div>
        {hasEvaluation && <ClassPerformance model={activeModel} />}
        {hasEvaluation && <ConfusionMatrix model={activeModel} />}
        <div className="span-2"><FeatureImportance model={activeModel} /></div>
      </div>
    </div>
  );
}

export default ModelInsights;
