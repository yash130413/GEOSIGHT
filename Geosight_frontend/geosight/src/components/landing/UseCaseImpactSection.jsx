import AnimatedCounter from '../common/AnimatedCounter';
import Icon from '../common/Icon';
import './UseCaseImpactSection.css';

const useCases = [
  {
    title: 'Urban Planning & Development',
    description: 'Analyze urban expansion patterns and infrastructure density for smart city planning and development strategies',
    stat: { value: 76, suffix: '%', label: 'Urban+Rural Coverage' },
    icon: '🏙️'
  },
  {
    title: 'Industrial Site Selection',
    description: 'Identify optimal locations for industrial development based on terrain classification and road connectivity',
    stat: { value: 70, suffix: 'K+', label: 'Training Tiles' },
    icon: '🏭'
  },
  {
    title: 'Road Network Analysis',
    description: 'Extract and analyze road infrastructure for connectivity assessment and transportation planning',
    // Sentinel-2 ground resolution (the road model has no measured detection rate yet)
    stat: { value: 10, suffix: ' m', label: 'Pixel Resolution' },
    icon: '🛣️'
  },
  {
    title: 'Land Use Classification',
    description: 'Multi-class terrain segmentation for environmental monitoring and resource management',
    stat: { value: 5, suffix: ' States', label: 'Coverage Area' },
    icon: '🌍'
  }
];

function UseCaseImpactSection() {
  return (
    <section className="gs-section use-case-impact">
      <div className="gs-container">
        <div className="gs-section-head">
          <h2>Real-World Applications</h2>
          <p>Transforming geospatial decision making across sectors</p>
        </div>

        <div className="use-cases-grid">
          {useCases.map((useCase) => (
            <article key={useCase.title} className="use-case-card gs-card">
              <span className="use-case-icon"><Icon emoji={useCase.icon} /></span>
              <div className="use-case-body">
                <h3>{useCase.title}</h3>
                <p>{useCase.description}</p>
              </div>
              <div className="use-case-stat">
                <span className="stat-value">
                  <AnimatedCounter end={useCase.stat.value} suffix={useCase.stat.suffix} />
                </span>
                <span className="stat-label">{useCase.stat.label}</span>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export default UseCaseImpactSection;
