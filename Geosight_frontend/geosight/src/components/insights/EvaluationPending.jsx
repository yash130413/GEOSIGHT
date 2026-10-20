import './EvaluationPending.css';

// Shown when Training/evaluate_models.py has not been run for a model yet,
// so no measured metrics exist to display.
function EvaluationPending({ model }) {
  return (
    <div className="evaluation-pending">
      <p className="pending-title">Not evaluated yet</p>
      <p>
        These metrics are measured against ground-truth masks on the validation tiles.
        They have not been generated for the {model === 'roads' ? 'road detection' : 'land classification'} model yet.
      </p>
      <p>Run:</p>
      <code>python Training/evaluate_models.py {model} --images ... --masks ... --checkpoint ...</code>
    </div>
  );
}

export default EvaluationPending;
