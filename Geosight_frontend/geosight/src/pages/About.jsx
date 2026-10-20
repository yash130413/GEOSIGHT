import { Link } from 'react-router-dom';
import { ArrowRight, Satellite, Layers, Cpu, Map as MapIcon, Route, Brain } from 'lucide-react';
import satelliteImg from '../assets/hero-satellite.webp';
import landcoverImg from '../assets/hero-landcover.webp';
import './About.css';

const KEY_FIGURES = [
  { value: '70K+', label: 'Satellite tiles' },
  { value: '5', label: 'Indian states' },
  { value: '4', label: 'Land-cover classes' },
  { value: '2', label: 'Deep learning models' },
];

const CLASSES = [
  { name: 'Rural', color: 'var(--rural)', text: 'Agricultural fields, vegetation and rural settlements' },
  { name: 'Urban', color: 'var(--urban)', text: 'Built-up areas, cities and dense infrastructure' },
  { name: 'Water', color: 'var(--water)', text: 'Rivers, lakes, reservoirs and water bodies' },
  { name: 'Background', color: 'var(--background-class)', text: 'Barren land and unclassified terrain' },
];

const BANDS = [
  { band: 'B2', name: 'Blue' },
  { band: 'B3', name: 'Green' },
  { band: 'B4', name: 'Red' },
  { band: 'B8', name: 'Near-infrared' },
  { band: 'B11', name: 'SWIR 1' },
  { band: 'B12', name: 'SWIR 2' },
];

const PIPELINE = [
  { icon: Satellite, title: 'Fetch', text: 'Sentinel-2 imagery from Google Earth Engine' },
  { icon: Layers, title: 'Prepare', text: '6 bands, scaled and tiled at 10 m' },
  { icon: Cpu, title: 'Segment', text: 'Every pixel classified by the models' },
  { icon: MapIcon, title: 'Visualize', text: 'Class maps, road overlay and statistics' },
];

const MODELS = [
  {
    icon: Brain,
    name: 'Land classification',
    arch: 'U-Net++ · EfficientNet-B4',
    specs: [
      ['Input', '6 Sentinel-2 bands'],
      ['Output', '4 classes per pixel'],
      ['Loss', 'Dice + Focal'],
      ['Selected checkpoint', 'Epoch 11 of 30'],
    ],
  },
  {
    icon: Route,
    name: 'Road detection',
    arch: 'U-Net · ResNet-50',
    specs: [
      ['Input', 'RGB (B4, B3, B2)'],
      ['Output', 'Road / non-road mask'],
      ['Loss', 'Dice + BCE'],
      ['Tile size', '256 × 256 px'],
    ],
  },
];

// Predicted class shares at the selected checkpoint (all_epochs_results.csv, epoch 11)
const COVERAGE = [
  { name: 'Urban', value: 42.5, color: 'var(--urban)' },
  { name: 'Rural', value: 33.7, color: 'var(--rural)' },
  { name: 'Water', value: 19.3, color: 'var(--water)' },
  { name: 'Background', value: 4.4, color: 'var(--background-class)' },
];

const TIMELINE = [
  { when: 'Month 1–2', title: 'Research & Planning' },
  { when: 'Month 2–3', title: 'Data Collection' },
  { when: 'Month 3–4', title: 'Model Development' },
  { when: 'Month 4–5', title: 'Training & Validation' },
  { when: 'Month 5–6', title: 'Deployment' },
];

const TECH = [
  'PyTorch', 'Segmentation Models PyTorch', 'Sentinel-2', 'Google Earth Engine', 'Rasterio',
  'Albumentations', 'OpenCV', 'NumPy', 'Flask', 'React', 'Leaflet',
];

function About() {
  return (
    <div className="about-page">
      {/* Intro */}
      <section className="about-intro">
        <div className="gs-container">
          <h1>About GeoSight</h1>
          <p className="about-lead">
            GeoSight turns Sentinel-2 satellite imagery into land-use maps. Two deep learning models label every
            10 m pixel as rural, urban, water or background and trace road networks, giving the land-use
            picture needed for industrial site selection.
          </p>
          <dl className="about-figures">
            {KEY_FIGURES.map((f) => (
              <div key={f.label}>
                <dt>{f.label}</dt>
                <dd>{f.value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* What it does */}
      <section className="gs-section">
        <div className="gs-container about-split">
          <div>
            <span className="gs-eyebrow">What it does</span>
            <h2>From raw imagery to a land-use map</h2>
            <p>The land classification model assigns each pixel to one of four classes:</p>
            <ul className="about-classes">
              {CLASSES.map((c) => (
                <li key={c.name}>
                  <i style={{ background: c.color }} />
                  <span><strong>{c.name}</strong> — {c.text}</span>
                </li>
              ))}
            </ul>
            <p>A second model extracts the road network for connectivity analysis.</p>
          </div>
          <figure className="about-figure">
            <div className="about-figure-pair">
              <img src={satelliteImg} alt="Sentinel-2 satellite image" width="637" height="484" />
              <img src={landcoverImg} alt="Land-cover map predicted by GeoSight" width="637" height="484" />
            </div>
            <figcaption>Sentinel-2 input and model output · Goa, India</figcaption>
          </figure>
        </div>
      </section>

      {/* Data */}
      <section className="gs-section gs-section-alt">
        <div className="gs-container about-split about-split-reverse">
          <div>
            <span className="gs-eyebrow">The data</span>
            <h2>70,000+ multispectral tiles</h2>
            <p>
              Sentinel-2 tiles from Delhi, Haryana, Uttar Pradesh, Sikkim and Uttarakhand, each covering
              2.56 × 2.56 km at 10 m per pixel. Six spectral bands give the model information the human eye
              can't see, such as near-infrared for vegetation and short-wave infrared for built-up areas.
            </p>
          </div>
          <ul className="about-bands">
            {BANDS.map((b) => (
              <li key={b.band}>
                <span className="band-code">{b.band}</span>
                <span className="band-name">{b.name}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Pipeline */}
      <section className="gs-section">
        <div className="gs-container">
          <div className="gs-section-head">
            <span className="gs-eyebrow">How it works</span>
            <h2>Four steps, fully automated</h2>
          </div>
          <ol className="about-pipeline">
            {PIPELINE.map(({ icon: StepIcon, title, text }, i) => (
              <li key={title}>
                <span className="pipeline-icon"><StepIcon size={20} aria-hidden="true" /></span>
                <span className="pipeline-step">Step {i + 1}</span>
                <h3>{title}</h3>
                <p>{text}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Models */}
      <section className="gs-section gs-section-alt">
        <div className="gs-container">
          <div className="gs-section-head">
            <span className="gs-eyebrow">The models</span>
            <h2>Two specialised networks</h2>
          </div>
          <div className="about-models">
            {MODELS.map(({ icon: ModelIcon, name, arch, specs }) => (
              <article key={name} className="about-model">
                <div className="about-model-head">
                  <span className="pipeline-icon"><ModelIcon size={20} aria-hidden="true" /></span>
                  <div>
                    <h3>{name}</h3>
                    <p>{arch}</p>
                  </div>
                </div>
                <dl>
                  {specs.map(([k, v]) => (
                    <div key={k}><dt>{k}</dt><dd>{v}</dd></div>
                  ))}
                </dl>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Results */}
      <section className="gs-section">
        <div className="gs-container about-results">
          <div>
            <span className="gs-eyebrow">Checkpoint selection</span>
            <h2>Epoch 11 gave the best balance</h2>
            <p>
              The 28 saved training epochs were compared on test tiles. Epoch 11 scored highest on the project's
              quality score (100/100), with 76.2% of pixels classified as urban or rural.
            </p>
          </div>
          <div className="coverage">
            <div className="coverage-bar" role="img" aria-label="Predicted class shares at epoch 11">
              {COVERAGE.map((c) => (
                <span key={c.name} style={{ width: `${c.value}%`, background: c.color }} />
              ))}
            </div>
            <ul className="coverage-legend">
              {COVERAGE.map((c) => (
                <li key={c.name}>
                  <i style={{ background: c.color }} />
                  <span>{c.name}</span>
                  <strong>{c.value}%</strong>
                </li>
              ))}
            </ul>
            <p className="coverage-note">Share of pixels predicted per class at epoch 11.</p>
          </div>
        </div>
      </section>

      {/* Timeline + tech */}
      <section className="gs-section gs-section-alt">
        <div className="gs-container">
          <div className="gs-section-head">
            <span className="gs-eyebrow">The journey</span>
            <h2>From concept to deployment in 6 months</h2>
          </div>
          <ol className="about-timeline">
            {TIMELINE.map((t) => (
              <li key={t.title}>
                <span className="timeline-dot" />
                <span className="timeline-when">{t.when}</span>
                <span className="timeline-title">{t.title}</span>
              </li>
            ))}
          </ol>

          <div className="about-tech">
            <h3>Built with</h3>
            <ul>
              {TECH.map((t) => <li key={t}>{t}</li>)}
            </ul>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="gs-section about-cta">
        <div className="gs-container">
          <h2>See it in action</h2>
          <p>Pick any area in India and get a land-use map in seconds.</p>
          <div className="about-cta-buttons">
            <Link to="/demo" className="gs-btn gs-btn-primary">Try the Live Demo <ArrowRight size={16} aria-hidden="true" /></Link>
            <Link to="/team" className="gs-btn gs-btn-secondary">Meet the Team</Link>
          </div>
        </div>
      </section>
    </div>
  );
}

export default About;
