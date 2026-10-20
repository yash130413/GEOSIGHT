import { Link } from 'react-router-dom';
import { Github } from 'lucide-react';
import './Footer.css';

const NAV_LINKS = [
  { name: 'Live Demo', to: '/demo' },
  { name: 'Model Insights', to: '/insights' },
  { name: 'About the Project', to: '/about' },
  { name: 'Team', to: '/team' },
];

const TECH = ['U-Net++', 'EfficientNet-B4', 'Sentinel-2', 'PyTorch', 'React', 'Flask'];

function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <Link to="/" className="footer-logo">GeoSight</Link>
          <p>
            AI-Driven Industrial Site Selection Using Satellite Imagery. Advanced multiclass semantic
            segmentation on high-resolution geographical satellite imagery for terrain classification
            and road network detection.
          </p>
          <a
            className="footer-github"
            href="https://github.com/mohvijayjain/GeoSight"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Github size={16} aria-hidden="true" /> Source Code (GitHub)
          </a>
        </div>

        <nav className="footer-col" aria-label="Footer">
          <h4>Quick Links</h4>
          <ul>
            {NAV_LINKS.map((link) => (
              <li key={link.to}>
                <Link to={link.to}>{link.name}</Link>
              </li>
            ))}
          </ul>
        </nav>

        <div className="footer-col">
          <h4>Powered by</h4>
          <ul className="footer-tech">
            {TECH.map((t) => <li key={t}>{t}</li>)}
          </ul>
        </div>
      </div>

      <div className="footer-bottom">
        <div className="footer-bottom-inner">
          <span>&copy; {currentYear} GeoSight. All rights reserved.</span>
          <span className="footer-facts">70K+ Training Tiles · 5 Indian States · Deep Learning Powered</span>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
