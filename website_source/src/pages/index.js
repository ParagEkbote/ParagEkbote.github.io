import React, { useState } from 'react';
import clsx from 'clsx';
import Layout from '@theme/Layout';
import styles from './index.module.css';

const CARDS = [
  {
    tag: '01',
    title: 'Research Focus',
    description: 'Transformer inference, optimization, and evaluation systems',
    body: `Examines how transformer models behave under different inference configurations — precision formats (BF16, FP16, INT8), kernel optimizations, and compilation strategies. Emphasis is on runtime characteristics: latency, throughput, memory, and stability rather than architectural novelty.`,
  },
  {
    tag: '02',
    title: 'Systems & Implementation',
    description: 'Training and inference pipelines with enforced constraints',
    body: `Structured pipelines for transformer models with parameter-efficient fine-tuning (LoRA). Monitoring mechanisms track adapter norms, gradient behavior, and activation drift to reduce instability during training.`,
  },
  {
    tag: '03',
    title: 'Benchmarking Methodology',
    description: 'Multi-metric evaluation of inference performance',
    body: `Benchmarking separates prefill latency and decode throughput, tracking GPU memory alongside stability metrics like coefficient of variation. Experiments use warmup phases and statistical aggregation for result reliability.`,
  },
  {
    tag: '04',
    title: 'IEEE Publication',
    description: 'Peer-reviewed work on IEEE Xplore',
    body: `Applied ML work with emphasis on implementation and evaluation — empirical contribution focused on system-level analysis rather than proposing new theoretical models.`,
    link: 'https://ieeexplore.ieee.org/document/11407267',
    linkLabel: 'View on IEEE Xplore →',
  },
];

function HeroSection() {
  return (
    <header className={styles.hero}>
      <div className={styles.heroInner}>
        <div className={styles.heroLeft}>
          <span className={styles.heroEyebrow}>ML / AI Researcher</span>
          <h1 className={styles.heroTitle}>Parag<br />Ekbote</h1>
          <p className={styles.heroSubtitle}>
            Empirical evaluation of transformer-based systems — inference
            behavior, optimization trade-offs, and reproducible benchmarking.
          </p>
          <div className={styles.heroActions}>
            <a href="/research" className={styles.btnPrimary}>Research</a>
            <a href="https://github.com/ParagEkbote" className={styles.btnGhost} target="_blank" rel="noopener noreferrer">GitHub ↗</a>
          </div>
        </div>

        <div className={styles.heroRight}>
          <div className={styles.statGrid}>
            <div className={styles.statItem}>
              <span className={styles.statNum}>1</span>
              <span className={styles.statDesc}>IEEE Publication</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statNum}>LLM</span>
              <span className={styles.statDesc}>Inference Focus</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statNum}>PyTorch</span>
              <span className={styles.statDesc}>Primary Stack</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statNum}>LoRA</span>
              <span className={styles.statDesc}>Fine-tuning Method</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

function ResearchCard({ tag, title, description, body, link, linkLabel }) {
  const [open, setOpen] = useState(false);

  return (
    <div className={clsx(styles.card, open && styles.cardOpen)}>
      <div className={styles.cardHeader} onClick={() => setOpen(o => !o)} role="button" tabIndex={0} onKeyDown={e => e.key === 'Enter' && setOpen(o => !o)}>
        <span className={styles.cardTag}>{tag}</span>
        <div className={styles.cardMeta}>
          <h3 className={styles.cardTitle}>{title}</h3>
          <p className={styles.cardDesc}>{description}</p>
        </div>
        <span className={clsx(styles.cardChevron, open && styles.cardChevronOpen)}>↓</span>
      </div>

      {open && (
        <div className={styles.cardBody}>
          <p>{body}</p>
          {link && (
            <a href={link} className={styles.cardLink} target="_blank" rel="noopener noreferrer">
              {linkLabel}
            </a>
          )}
        </div>
      )}
    </div>
  );
}

export default function Home() {
  return (
    <Layout title="Parag Ekbote" description="LLM systems research, benchmarking, and optimization">
      <HeroSection />

      <main className={styles.main}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionLabel}>Areas</span>
          <h2 className={styles.sectionTitle}>Research Overview</h2>
        </div>

        <div className={styles.cardList}>
          {CARDS.map(card => (
            <ResearchCard key={card.tag} {...card} />
          ))}
        </div>
      </main>
    </Layout>
  );
}