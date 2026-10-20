import { Link } from 'react-router-dom';
import { ArrowRight, Brain, Satellite, Route } from 'lucide-react';
import satelliteImg from '../../assets/hero-satellite.webp';
import landcoverImg from '../../assets/hero-landcover.webp';
import './HeroSection.css';

const FEATURES = [
  { icon: Brain, title: 'Deep Learning', description: 'U-Net++ + EfficientNet-B4' },
  { icon: Satellite, title: 'Remote Sensing', description: '70K+ Sentinel-2 tiles' },
  { icon: Route, title: 'Road Detection', description: 'U-Net + ResNet-50' },
];

const LEGEND = [
  { name: 'Rural', color: 'var(--rural)' },
  { name: 'Urban', color: 'var(--urban)' },
  { name: 'Water', color: 'var(--water)' },
  { name: 'Background', color: 'var(--background-class)' },
];

function HeroSection() {
  return (
    <section className="hero">
      <div className="hero-inner">
        <div className="hero-copy">
          <h1>GeoSight: AI-Driven Industrial Site Selection Using Satellite Imagery</h1>
          <p className="hero-subtitle">
            Advanced multiclass semantic segmentation for terrain classification and road network detection
          </p>
          <p className="hero-description">
            Comprehensive machine learning pipeline performing multiclass semantic segmentation on high-resolution
            geographical satellite imagery. Identifies and maps terrain into distinct classes: Background, Rural,
            Urban, and Water with specialized road network extraction.
          </p>

          <div className="hero-cta">
            <Link to="/demo" className="gs-btn gs-btn-primary">
              Try the Live Demo <ArrowRight size={16} aria-hidden="true" />
            </Link>
            <Link to="/insights" className="gs-btn gs-btn-secondary">View Model Insights</Link>
          </div>

          <ul className="hero-features">
            {FEATURES.map(({ icon: FeatureIcon, title, description }) => (
              <li key={title}>
                <span className="hero-feature-icon"><FeatureIcon size={18} aria-hidden="true" /></span>
                <span>
                  <strong>{title}</strong>
                  <small>{description}</small>
                </span>
              </li>
            ))}
          </ul>
        </div>

        <figure className="hero-visual">
          <div className="hero-visual-frame">
            <div className="hero-pane">
              <img src={satelliteImg} alt="Sentinel-2 satellite image of a river valley" width="637" height="484" />
              <span className="hero-pane-label">Sentinel-2 input</span>
            </div>
            <div className="hero-pane">
              <img src={landcoverImg} alt="Land-cover map predicted by the model for the same area" width="637" height="484" />
              <span className="hero-pane-label">Model output</span>
            </div>
          </div>
          <figcaption>
            <ul className="hero-legend">
              {LEGEND.map((c) => (
                <li key={c.name}><i style={{ background: c.color }} />{c.name}</li>
              ))}
            </ul>
            <span className="hero-location">Sample result · Goa, India</span>
          </figcaption>
        </figure>
      </div>
    </section>
  );
}

export default HeroSection;
