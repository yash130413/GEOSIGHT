import { Fragment } from 'react';
import { ChevronRight } from 'lucide-react';
import Icon from '../common/Icon';
import './ArchitectureFlowSection.css';

const flowSteps = [
  { title: 'Sentinel-2 Input', icon: '🛰️', description: '6-channel multispectral imagery (256×256)' },
  { title: 'U-Net++ Encoder', icon: '🧠', description: 'EfficientNet-B4 feature extraction' },
  { title: 'Semantic Segmentation', icon: '🎯', description: '4-class terrain classification' },
  { title: 'Road Detection', icon: '🛣️', description: 'U-Net + ResNet-50 binary segmentation' },
  { title: 'Output Visualization', icon: '📊', description: 'RGB overlay with confidence scores' },
];

function ArchitectureFlowSection() {
  return (
    <section className="gs-section gs-section-alt architecture-flow">
      <div className="gs-container">
        <div className="gs-section-head">
          <h2>Architecture Flow</h2>
        </div>

        <ol className="arc-pipeline">
          {flowSteps.map((step, i) => (
            <Fragment key={step.title}>
              <li className="arc-step">
                <span className="arc-step-icon"><Icon emoji={step.icon} /></span>
                <p className="arc-title">{step.title}</p>
                <p className="arc-desc">{step.description}</p>
              </li>
              {i < flowSteps.length - 1 && (
                <li className="arc-arrow" aria-hidden="true"><ChevronRight size={18} /></li>
              )}
            </Fragment>
          ))}
        </ol>
      </div>
    </section>
  );
}

export default ArchitectureFlowSection;
