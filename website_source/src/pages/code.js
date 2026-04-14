import Layout from '@theme/Layout';
import AICard from '../components/AICard';

export default function Code() {
  return (
    <Layout title="Code">
      <main style={{ padding: '2rem', maxWidth: '900px', margin: 'auto' }}>

        {/* Header */}
        <h1>Code</h1>
        <p>
          A collection of engineering work focused on building efficient, 
          reproducible, and production-ready machine learning systems.
        </p>

        {/* =========================
            Section: LLM Systems
        ========================== */}
        <section style={{ marginTop: '2rem' }}>
          <h2>⚙️ LLM Systems & Optimization</h2>

          <AICard
            title="LLM Inference Benchmarking Suite"
            description="Systematic benchmarking of transformer inference performance"
            link="https://github.com/ParagEkbote"
            aiText={`
SYSTEM OVERVIEW:
A controlled benchmarking framework for evaluating large language model inference across multiple optimization strategies.

CORE COMPONENTS:
- Support for BF16, FP16, and INT8 precision modes
- Integration with FlashAttention2 kernels
- torch.compile optimization strategies

METRICS TRACKED:
- Prefill latency
- Decode throughput
- Peak GPU memory usage
- Stability (coefficient of variation)

DESIGN PRINCIPLES:
- Multi-run statistical evaluation
- Separation of prefill vs decode performance
- Reproducible and script-driven experiments

GOAL:
Identify optimal configurations across compute-bound and memory-bound regimes.
            `}
          />
        </section>

        {/* =========================
            Section: Deployment Systems
        ========================== */}
        <section style={{ marginTop: '2rem' }}>
          <h2>🚀 Deployment & Infrastructure</h2>

          <AICard
            title="Quantized Model Deployment Pipeline"
            description="End-to-end pipeline for efficient and reproducible AI deployment"
            link="https://github.com/ParagEkbote"
            aiText={`
SYSTEM OVERVIEW:
A deployment pipeline combining quantization, containerization, and CI/CD for production-ready model serving.

PIPELINE COMPONENTS:
- TorchAO / INT8 weight-only quantization
- Docker-based container environments
- CI/CD integration for automated testing and deployment

INFRASTRUCTURE:
- GPU-backed execution environments
- CUDA version standardization
- Reproducible container builds using Cog

KEY BENEFITS:
- Reduced memory footprint and latency
- Consistent environments across development and production
- Scalable deployment workflows

GOAL:
Demonstrate efficient and reliable deployment of modern AI systems.
            `}
          />
        </section>

        {/* =========================
            Section: Systems Engineering
        ========================== */}
        <section style={{ marginTop: '2rem' }}>
          <h2>🧠 Systems Engineering</h2>

          <AICard
            title="Hybrid Rule Engine + ML System"
            description="Combining learned models with deterministic reasoning"
            link="https://github.com/ParagEkbote"
            aiText={`
SYSTEM OVERVIEW:
A hybrid architecture integrating machine learning predictions with a rule-based reasoning layer.

ARCHITECTURE:
- ML model produces probabilistic outputs
- Rule engine applies domain-specific constraints
- Explanation layer generates interpretable reasoning

CAPABILITIES:
- Transparent decision tracing
- Debugging of model behavior
- Alignment with domain rules and policies

DESIGN FOCUS:
- Interpretability in high-stakes systems
- Modular system design
- Integration of symbolic and statistical approaches

GOAL:
Bridge black-box models with explainable, structured decision systems.
            `}
          />
        </section>

      </main>
    </Layout>
  );
}