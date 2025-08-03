---
hide:
  - navigation
  - toc
---

# **Projects ⚙️**

## 1. HF × Docker: Scalable Inference with Quantized AI Models

### 🔗 [Optimized Models: torchao & Pruna Quantization](https://huggingface.co/collections/AINovice2005/optimized-models-torchao-and-pruna-quantization-6875516b020b9776cc21e591)

1. Created a curated collection of 8 quantized AI models spanning **text-to-text**, **image-to-text**, **audio-to-text**, and **text-to-image** modalities.

2. Each model is optimized for **efficient inference** using **low-bit precision**, while maintaining strong performance across diverse generative and understanding tasks.

**Tech Stack:**  
`PyTorch`, `torchao`, `transformers`, `diffusers`, `pruna`, `GPU acceleration`

---

### 🔗 [Containerized Models: LLMs & Diffusion Models for Fast, Reproducible Inference](https://hub.docker.com/u/paragekbote)

#### 1. FLUX.1-dev Model Serving

- **Trigger-Based LoRA Hotswapping**  
  Dynamically loads style-specific LoRA adapters based on prompt keywords (e.g., `"ghibsky"`).

- **4-bit Quantization (`BitsAndBytes`)**  
  Maintains output quality while drastically reducing memory usage.

- **`torch.compile` Acceleration**  
  Reduces image generation latency via runtime graph optimization.

#### 2. Memory-Efficient Small Language Model

- Leverages `Pruna` for model quantization and `torch.compile` for graph-level optimizations.
- Significantly reduces memory usage and boosts inference speed.
- Ideal for memory-constrained or on-premise environments.

#### 3. High-Throughput 4-bit Small Language Model

- Implements 4-bit quantization for minimal RAM/GPU requirements.
- Integrates `Flash Attention 2` and `Triton` fused kernels for high-throughput inference on modern hardware.

**Tech Stack:**  
`PyTorch`, `transformers`, `diffusers`, `Unsloth`, `LoRA`, `pruna`, `BitsAndBytes`, `Flash Attention 2`, `torch.compile`, `Docker`, `Cog`
