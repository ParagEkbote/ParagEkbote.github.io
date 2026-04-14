import Layout from '@theme/Layout';
import AICard from '../components/AICard';

export default function Projects() {
  return (
    <Layout title="Projects">
      <main style={{ padding: '2rem', maxWidth: '900px', margin: 'auto' }}>

        {/* Header */}
        <h1>Projects</h1>
        <p>
          A selection of applied machine learning and systems projects focused on 
          efficient modeling, interpretability, and production-ready AI deployment.
        </p>

        {/* =========================
            Project 1
        ========================== */}
        <section style={{ marginTop: '2rem' }}>
          <h2>⚡ Efficient ML Systems</h2>

          <AICard
            title="Lightweight Transformer for Network Intrusion Detection"
            description="ModernBERT + LoRA for efficient multi-class attack classification"
            link="https://github.com/ParagEkbote"
            aiText={`
This project explores the use of encoder-only transformer architectures for 
network intrusion detection under constrained compute environments.

A ModernBERT-based model is fine-tuned using parameter-efficient techniques 
(LoRA), enabling scalable training without full model updates.

Key focus areas:
- Stability-aware LoRA training under class imbalance
- Stratified batching for controlled data distribution
- Monitoring of training dynamics and calibration
- Efficient inference for real-time security pipelines

The system emphasizes reproducibility and engineering discipline in applied ML.
            `}
          />

        </section>

        {/* =========================
            Project 2
        ========================== */}
        <section style={{ marginTop: '2rem' }}>
          <h2>🧠 Interpretable AI Systems</h2>

          <AICard
            title="Rule Engine with Explanation Layer"
            description="Hybrid AI system combining model predictions with structured reasoning"
            link="https://github.com/ParagEkbote"
            aiText={`
This project implements a hybrid framework that integrates statistical models 
with a deterministic rule engine and an explanation layer.

The goal is to enhance interpretability and trust by augmenting predictions with 
structured reasoning.

Core capabilities:
- Rule-based augmentation of model outputs
- Transparent decision tracing
- Post-hoc reasoning and debugging
- Alignment with domain constraints

The explanation layer converts model behavior into human-readable reasoning 
chains, making the system suitable for high-stakes applications such as security 
and decision support.
            `}
          />

        </section>

        {/* =========================
            Project 3
        ========================== */}
        <section style={{ marginTop: '2rem' }}>
          <h2>🚀 Deployment & Optimization</h2>

          <AICard
            title="Quantized & Containerized Model Deployment"
            description="Production-ready AI using quantization, containers, and CI/CD"
            link="https://github.com/ParagEkbote"
            aiText={`
This project demonstrates how modern optimization and deployment techniques—
including model quantization, containerization, and CI/CD—can be combined to 
build efficient and reproducible AI systems.

Core objective:
To show that high-performance AI deployments can be achieved without sacrificing 
reproducibility, scalability, or hardware efficiency.

Key components:
- Quantized inference pipelines for reduced memory and latency
- Containerized environments for reproducibility across stages
- CI/CD workflows for automated testing and deployment

The system leverages Replicate for GPU-backed execution and Cog for consistent 
container builds, enabling a stable and production-oriented deployment workflow.
            `}
          />

        </section>

      </main>
    </Layout>
  );
}