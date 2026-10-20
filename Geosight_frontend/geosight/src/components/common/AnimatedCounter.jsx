import { useEffect, useRef, useState } from 'react';
import { motion, useInView } from 'framer-motion';
import './AnimatedCounter.css';

function AnimatedCounter({ end, suffix = '', duration = 1.5 }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  // Re-run whenever the target value changes, so a reused card never keeps
  // showing the previous number.
  useEffect(() => {
    if (!isInView) return;
    let frame;
    let startTime;
    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / (duration * 1000), 1);
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      setCount(progress < 1 ? Math.floor(easeOutQuart * end) : end);

      if (progress < 1) {
        frame = requestAnimationFrame(animate);
      }
    };
    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [isInView, end, duration]);

  return (
    <motion.span 
      ref={ref}
      className="animated-counter"
      initial={{ opacity: 0 }}
      animate={isInView ? { opacity: 1 } : {}}
    >
      {count}{suffix}
    </motion.span>
  );
}

export default AnimatedCounter;
