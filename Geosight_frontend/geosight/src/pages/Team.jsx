import { Brain, Database, ScanSearch, Code2 } from 'lucide-react';
import './Team.css';

const team = [
  {
    name: 'Mohvijay Jain',
    role: 'AI Research & Model Development',
    icon: Brain,
    responsibilities: 'Developed the Urban-Rural Morphological Classification model and contributed to the optimization of the Road Extraction pipeline for high-precision infrastructure detection.'
  },
  {
    name: 'Vedansh',
    role: 'Geospatial Data Engineering',
    icon: Database,
    responsibilities: 'Built the end-to-end dataset pipeline (66k+ multispectral samples) and engineered a seamless GIS integration using Leaflet.js and Google Earth Engine for real-time satellite imagery fetching and live model inference.'
  },
  {
    name: 'Rishika',
    role: 'Computer Vision Engineering',
    icon: ScanSearch,
    responsibilities: 'Led the Road Extraction model development, iteratively refining the architecture and implementing post-processing techniques to convert raw predictions into clean infrastructure graphs.'
  },
  {
    name: 'Yash',
    role: 'Full-Stack & API Development',
    icon: Code2,
    responsibilities: 'Designed the complete GeoSight web interface and built a scalable backend API to handle model requests, ensuring smooth data flow between map interactions and AI output visualizations.'
  }
];

const initials = (name) => name.split(' ').map((p) => p[0]).join('').slice(0, 2).toUpperCase();

function Team() {
  return (
    <div className="team-page">
      <header className="team-header">
        <h1>Our Team</h1>
        <p>Meet the researchers and engineers behind GeoSight</p>
      </header>

      <div className="team-grid">
        {team.map(({ name, role, icon: RoleIcon, responsibilities }) => (
          <article key={name} className="team-card">
            <div className="team-card-top">
              <div className="team-avatar" aria-hidden="true">{initials(name)}</div>
              <div>
                <h3>{name}</h3>
                <span className="team-role">
                  <RoleIcon size={14} aria-hidden="true" /> {role}
                </span>
              </div>
            </div>
            <p>{responsibilities}</p>
          </article>
        ))}
      </div>
    </div>
  );
}

export default Team;
