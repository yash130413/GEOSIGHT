import {
  Atom, BarChart3, Bot, Brain, Briefcase, Building2, CalendarDays, CheckCircle2, ClipboardList,
  Cloud, Construction, Dices, Download, Droplets, ExternalLink, Eye, Factory, FlaskConical, Flame,
  FolderOpen, Github, Globe, GraduationCap, Grid3x3, Image, Info, Landmark, Laptop, Leaf, LineChart,
  Mail, Map, MapPin, Microscope, Network, Package, RefreshCw, Repeat, Rocket, Route, Satellite,
  Scale, Search, Settings, Sparkles, Sprout, Target, Timer, TrendingUp, Trophy, UploadCloud, User, Users, Wheat,
  Wrench, XCircle, Zap,
} from 'lucide-react';
import './Icon.css';

// One consistent line-icon set instead of emojis (which render differently on
// every OS). Content keeps its emoji markers; they are mapped to icons here.
const ICONS = {
  '🛣️': Route, '🛰️': Satellite, '📊': BarChart3, '🎯': Target, '🌍': Globe, '🌎': Globe,
  '🌐': Globe, '🧠': Brain, '🗺️': Map, '⚡': Zap, '📈': TrendingUp, '🏭': Factory,
  '⚙️': Settings, '📉': LineChart, '🏙️': Building2, '🔄': RefreshCw, '🔍': Search,
  '🔗': ExternalLink, '🏛️': Landmark, '🖼️': Image, '🤖': Bot, '🌿': Leaf, '🔥': Flame,
  '🔬': Microscope, '🔢': Grid3x3, '💻': Laptop, '❌': XCircle, '📍': MapPin,
  '📋': ClipboardList, '🏆': Trophy, '📦': Package, '🔁': Repeat, '🏗️': Construction,
  '🌱': Sprout, '🎓': GraduationCap, '📥': Download, '🚀': Rocket, '👨‍💻': User, '👩‍💻': User,
  '👩‍🔬': User, '👨‍🎨': User, '🕸️': Network, '👥': Users, '📬': Mail, '📧': Mail,
  '💼': Briefcase, '🐙': Github, '🎲': Dices, '⚛️': Atom, '🌶️': FlaskConical, '👁️': Eye,
  '☁️': Cloud, '🔧': Wrench, '✨': Sparkles, '⚖️': Scale, '📁': FolderOpen, '📡': UploadCloud,
  '✅': CheckCircle2, '🌾': Wheat, '💧': Droplets, '📅': CalendarDays, 'ℹ️': Info,
  '⏱️': Timer,
};

const EMOJI_RUN = /(?:[\u{1F300}-\u{1FAFF}\u23E9-\u23FF\u2600-\u27BF\u2139\u2705\u274C][\uFE0F\u200D]?)+/gu;

function normalise(emoji) {
  if (ICONS[emoji]) return emoji;
  // Allow a missing/extra variation selector (U+FE0F)
  const bare = emoji.replace(/\uFE0F/g, '');
  return Object.keys(ICONS).find((k) => k.replace(/\uFE0F/g, '') === bare);
}

/** Renders the icon for an emoji; falls back to the emoji itself if unmapped. */
function Icon({ emoji, className = '', label }) {
  const key = emoji && normalise(emoji.trim());
  const Component = key && ICONS[key];
  if (!Component) return emoji ? <span className={className}>{emoji}</span> : null;
  return (
    <Component
      className={`gs-icon ${className}`.trim()}
      aria-hidden={label ? undefined : true}
      aria-label={label}
      strokeWidth={1.75}
    />
  );
}

/** Renders a string such as "📊 Model Summary" with its emojis swapped for icons. */
export function IconText({ text }) {
  if (typeof text !== 'string') return text ?? null;
  const parts = [];
  let last = 0;
  for (const match of text.matchAll(EMOJI_RUN)) {
    if (match.index > last) parts.push(text.slice(last, match.index));
    parts.push(<Icon key={match.index} emoji={match[0]} />);
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return <>{parts}</>;
}

export default Icon;
