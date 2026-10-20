import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import './FinalCTASection.css';

function FinalCTASection() {
  return (
    <section className="final-cta">
      <div className="gs-container">
        <div className="cta-panel">
          <div>
            <h2>Ready to Classify Your Region?</h2>
            <p>Experience the power of AI-driven geospatial analysis</p>
          </div>
          <div className="cta-buttons">
            <Link to="/demo" className="gs-btn cta-primary">
              Launch Live Demo <ArrowRight size={16} aria-hidden="true" />
            </Link>
            <Link to="/insights" className="gs-btn cta-secondary">View Model Insights</Link>
          </div>
        </div>
      </div>
    </section>
  );
}

export default FinalCTASection;
