import './HowItWorks.css';

const steps = [
  {
    title: 'Satellite Imagery Input',
    description: 'Select coordinates or upload 6-channel Sentinel-2 satellite imagery (B2, B3, B4, B8, B11, B12) for analysis.'
  },
  {
    title: 'Dual Model Processing',
    description: 'U-Net++ with EfficientNet-B4 performs land classification while U-Net with ResNet-50 extracts road networks.'
  },
  {
    title: 'Terrain Classification & Visualization',
    description: 'Receive multiclass segmentation results: Background, Rural, Urban, Water with road network overlay and confidence scores.'
  }
];

function HowItWorks() {
  return (
    <section className="gs-section how-it-works">
      <div className="gs-container">
        <div className="gs-section-head">
          <h2>How It Works</h2>
          <p>Three-step AI-powered geospatial analysis pipeline</p>
        </div>

        <ol className="steps-container">
          {steps.map((step, index) => (
            <li key={step.title} className="hiw-step gs-card">
              <span className="hiw-step-number">{String(index + 1).padStart(2, '0')}</span>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export default HowItWorks;
