import Card from '../common/Card';
import EvaluationPending from './EvaluationPending';
import evaluation from '../../data/modelEvaluation.json';
import './ConfusionMatrix.css';

// Values come from Training/evaluate_models.py (src/data/modelEvaluation.json).
function ConfusionMatrix({ model = 'classification' }) {
  const result = evaluation[model === 'roads' ? 'roads' : 'classification'];

  if (!result) {
    return (
      <Card className="confusion-matrix">
        <h3>Confusion Matrix</h3>
        <EvaluationPending model={model} />
      </Card>
    );
  }

  const labels = result.classes;
  // Show each row as a percentage of that true class's pixels
  const matrix = result.confusion_matrix.map((row) => {
    const total = row.reduce((a, b) => a + b, 0);
    return row.map((v) => (total ? (v / total) * 100 : 0));
  });

  return (
    <Card className="confusion-matrix">
      <h3>Confusion Matrix</h3>
      <p className="matrix-subtitle">
        Rows are the <strong>actual</strong> class, columns the <strong>predicted</strong> class
        (% of each actual class's pixels).
      </p>
      <div className="matrix-container">
        <div className="matrix-grid" style={{ gridTemplateColumns: `auto repeat(${labels.length}, 1fr)` }}>
          <div className="matrix-corner"></div>
          {labels.map((label, i) => (
            <div key={i} className="matrix-header">{label}</div>
          ))}
          {labels.map((rowLabel, i) => (
            <div key={i} className="matrix-row">
              <div className="matrix-label">{rowLabel}</div>
              {matrix[i].map((value, j) => (
                <div key={j} className={`matrix-cell ${i === j ? 'diagonal' : ''}`}>
                  {value.toFixed(1)}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="matrix-observations">
        <p className="obs-title">Evaluation details:</p>
        <ul>
          <li>Checkpoint: {result.checkpoint}</li>
          <li>Validation tiles: {result.num_tiles.toLocaleString()}</li>
          <li>Pixel accuracy: {result.pixel_accuracy}% · Mean IoU: {result.mean_iou}%</li>
          <li>Evaluated on: {result.evaluated_on}</li>
        </ul>
      </div>
    </Card>
  );
}

export default ConfusionMatrix;
