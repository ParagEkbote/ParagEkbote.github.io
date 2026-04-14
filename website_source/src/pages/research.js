import Layout from '@theme/Layout';
import AICard from '../components/AICard';

export default function Research() {
  const pageContext = `
This page describes research work focused on:

- Large Language Models (LLMs)
- Inference optimization (latency, throughput, memory)
- Quantization (INT8, BF16 trade-offs)
- Transformer efficiency (FlashAttention, KV cache)
- Reproducible benchmarking systems

Featured work includes:
- IEEE publication on applied ML systems
- Ongoing work on LLM benchmarking frameworks

The focus is on bridging theoretical research with practical, reproducible engineering.
  `;

  const openAI = (url) => window.open(url, '_blank');

  return (
    <Layout title="Research">
      <main style={{ padding: '2rem', maxWidth: '900px', margin: 'auto' }}>
        
        {/* Header */}
        <h1>Research</h1>
        <p>
          My work focuses on Large Language Models (LLMs), optimization, and 
          applied machine learning systems. I aim to bridge theoretical research 
          with practical, reproducible engineering.
        </p>

        {/* =========================
            AI CONTROL (SINGLE BLOCK)
        ========================== */}
        <div style={{ marginTop: '1.5rem', marginBottom: '2rem', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          
          <button
            onClick={() =>
              openAI(`https://claude.ai/new?q=${encodeURIComponent(pageContext)}`)
            }
            style={btnStyle('#f4a261')}
          >
            🤖 Ask Claude
          </button>

          <button
            onClick={() =>
              openAI(`https://chatgpt.com/?q=${encodeURIComponent(pageContext)}`)
            }
            style={btnStyle('#10a37f')}
          >
            🤖 Ask ChatGPT
          </button>

          <button
            onClick={() =>
              openAI(`https://huggingface.co/chat?q=${encodeURIComponent(pageContext)}`)
            }
            style={btnStyle('#ff9d00')}
          >
            🤗 Ask HuggingChat
          </button>
        </div>

        {/* =========================
            Featured Paper
        ========================== */}
        <section style={{ marginTop: '2rem' }}>
          <h2>📄 Featured Publication</h2>

          <AICard
            title="IEEE Publication (2025)"
            description="Peer-reviewed research published on IEEE Xplore."
            link="https://ieeexplore.ieee.org/document/11407267"
            aiText={`
RESEARCH OVERVIEW:
This work explores practical and theoretical aspects of machine learning system design and evaluation, with an emphasis on real-world applicability.

KEY CONTRIBUTIONS:
- Systematic experimentation and evaluation methodology
- Application of modern machine learning techniques
- Strong focus on reproducibility and engineering rigor

IMPACT:
- Bridges research and deployment-oriented ML systems
- Demonstrates practical relevance beyond theoretical benchmarks

PUBLICATION:
Published on IEEE Xplore, indicating peer-reviewed validation and academic rigor.
            `}
          />
        </section>

        {/* =========================
            Research Areas
        ========================== */}
        <section style={{ marginTop: '2rem' }}>
          <h2>🔬 Research Areas</h2>

          <ul>
            <li>LLM Inference Optimization (Latency, Throughput, Memory)</li>
            <li>Quantization (INT8, BF16 trade-offs)</li>
            <li>Transformer Efficiency (FlashAttention, KV Cache)</li>
            <li>Reproducible Benchmarking Systems</li>
            <li>Applied Deep Learning Systems</li>
          </ul>
        </section>

        {/* =========================
            Ongoing Work
        ========================== */}
        <section style={{ marginTop: '2rem' }}>
          <h2>🚧 Ongoing Work</h2>

          <AICard
            title="LLM Benchmarking Framework"
            description="Systematic evaluation of transformer inference efficiency"
            aiText={`
SYSTEM OVERVIEW:
A structured benchmarking framework designed to evaluate transformer inference performance under controlled and reproducible settings.

EVALUATION DIMENSIONS:
- Precision formats (BF16, FP16, INT8)
- Kernel optimizations (FlashAttention2)
- Compile strategies (torch.compile modes)

DESIGN PRINCIPLES:
- Reproducibility across runs and configurations
- Statistical rigor (multi-run evaluation, variance tracking)
- Deployment relevance (realistic sequence lengths and batch sizes)

GOAL:
Provide a reliable foundation for comparing inference optimizations in modern LLM systems.
            `}
          />

        </section>

      </main>
    </Layout>
  );
}

/* =========================
   Button Styling
========================= */
function btnStyle(color) {
  return {
    background: color,
    color: '#fff',
    border: 'none',
    borderRadius: '6px',
    padding: '8px 14px',
    fontSize: '0.8rem',
    fontWeight: 600,
    cursor: 'pointer'
  };
}