import { Satellite, Flame, Globe, Brain } from 'lucide-react';
import './TrustSection.css';

const partners = [
  { name: 'Sentinel-2', detail: 'Multispectral imagery', icon: Satellite },
  { name: 'PyTorch', detail: 'Model training', icon: Flame },
  { name: 'Google Earth Engine', detail: 'Image fetching', icon: Globe },
  { name: 'EfficientNet-B4', detail: 'Encoder backbone', icon: Brain },
];

function TrustSection() {
  return (
    <section className="trust-section">
      <div className="gs-container">
        <h3 className="trust-title">Built With Industry-Grade Technology</h3>
        <ul className="trust-grid">
          {partners.map(({ name, detail, icon: TechIcon }) => (
            <li key={name} className="trust-item">
              <span className="trust-logo"><TechIcon size={20} aria-hidden="true" /></span>
              <span className="trust-text">
                <span className="trust-name">{name}</span>
                <span className="trust-detail">{detail}</span>
              </span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export default TrustSection;
