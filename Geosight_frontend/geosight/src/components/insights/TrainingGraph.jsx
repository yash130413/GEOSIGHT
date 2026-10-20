import Card from '../common/Card';
import './TrainingGraph.css';

function TrainingGraph({ model = 'classification' }) {
  const isRoad = model === 'roads';
  // Real quality scores from all_epochs_results.csv
  const epochs =       [1,  2,  3,  4,  5,  6,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 26, 27, 28, 29, 30];
  const qualityScore = [85, 80, 85, 95, 80, 85, 50, 85, 70,100, 85, 95, 85, 75, 95, 85, 75, 95, 50, 50, 85, 85, 85, 80, 85, 85, 85, 70];
  const urbanRural =   [68.8,67.4,68.5,74.5,64.2,73.3,52.5,70.9,62.4,76.2,71.2,73.7,66.4,66.1,76.1,71.5,65.4,72.4,56.1,51.1,67.6,68.6,69.6,65.6,67.4,72.2,68.2,63.9];

  const W = 560, H = 260, PAD = 40;

  // Classification graph
  const xScale  = (i, len) => PAD + (i / (len - 1)) * (W - PAD * 2);
  const yScaleQ = (v) => H - PAD - ((v - 40) / 65) * (H - PAD * 2);
  const yScaleU = (v) => H - PAD - ((v - 40) / 45) * (H - PAD * 2);

  const qPoints = qualityScore.map((v, i) => `${xScale(i, epochs.length)},${yScaleQ(v)}`).join(' ');
  const uPoints = urbanRural.map((v, i)   => `${xScale(i, epochs.length)},${yScaleU(v)}`).join(' ');

  // Epochs 7 and 25 have no saved checkpoint, so look up epoch 11's position
  const bestX = xScale(epochs.indexOf(11), epochs.length);

  if (isRoad) {
    // The road model's per-epoch logs were not saved, so there is no real curve to plot.
    return (
      <Card className="training-graph">
        <h3>Road Model Training</h3>
        <p className="training-note">
          Trained for 10 epochs (batch size 8, Adam, lr 1e-4, Dice + BCE loss) on 256×256 RGB tiles,
          keeping the checkpoint with the lowest validation loss
          (see <code>Scripts/Training/Kaggle_Road_Test.py</code>).
          Per-epoch metrics were not logged, so no training curve is shown.
        </p>
      </Card>
    );
  }

  return (
    <Card className="training-graph">
      <h3>Training Progress (30 Epochs)</h3>
      <p className="training-note">Scores for the 28 saved epochs (from all_epochs_results.csv). Epoch 11 achieved the best quality score of 100 with 76.2% Urban+Rural coverage.</p>
      <div className="graph-container">
        <div className="graph-legend">
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: 'var(--accent)' }}></span>
            Quality Score (0–100)
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: 'var(--urban)' }}></span>
            Urban+Rural % Coverage
          </div>
        </div>
        <div className="graph">
          <svg viewBox={`0 0 ${W} ${H}`} className="graph-svg">
            {/* Grid lines */}
            {[50,60,70,80,90,100].map(v => (
              <line key={v} x1={PAD} y1={yScaleQ(v)} x2={W-PAD} y2={yScaleQ(v)}
                stroke="rgba(11, 110, 153,0.08)" strokeWidth="1" strokeDasharray="4,4" />
            ))}
            {/* Epoch 11 highlight */}
            <line x1={bestX} y1={PAD} x2={bestX} y2={H-PAD}
              stroke="rgba(11, 110, 153,0.3)" strokeWidth="1" strokeDasharray="4,4" />
            <text x={bestX+4} y={PAD+12} fill="var(--accent)" fontSize="10">Best (E11)</text>
            {/* Quality score line */}
            <polyline points={qPoints} fill="none" stroke="var(--accent)" strokeWidth="2.5" strokeLinejoin="round" />
            {/* Urban+Rural line */}
            <polyline points={uPoints} fill="none" stroke="var(--urban)" strokeWidth="2" strokeLinejoin="round" strokeDasharray="6,3" />
            {/* Epoch 11 dot */}
            <circle cx={bestX} cy={yScaleQ(100)} r="5" fill="var(--accent)" />
          </svg>
        </div>
      </div>
    </Card>
  );
}

export default TrainingGraph;
