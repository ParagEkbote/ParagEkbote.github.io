---
hide:
  - navigation
  - toc
---

# **Projects ⚙️**

### 1. [Optimized Models: torchao & Pruna Quantization](https://huggingface.co/collections/AINovice2005/optimized-models-torchao-and-pruna-quantization-6875516b020b9776cc21e591)

A collection of AI models quantized with torchao and Pruna to deliver faster inference and lower deployment cost.

- Built a curated collection of 8 quantized AI models covering text-to-text, image-to-text, audio-to-text, and text-to-image modalities.

- Optimized each model with low-bit precision, enabling efficient inference while preserving strong performance across generative and understanding tasks.

- Reduced compute and memory overhead, making the models more practical for deployment in real-world applications.

**Tech Stack:** `PyTorch`, `torchao`, `transformers`, `diffusers`, `pruna`, `GPU acceleration`, `bitsandbytes`

---

### 2. [Containerized Models: LLMs & Diffusion Models for Fast, Reproducible Inference](https://hub.docker.com/u/paragekbote)

#### Memory-Efficient Small Language Model

- Leverages `Pruna` for model quantization and `torch.compile` for graph-level optimizations.
- Significantly reduces memory usage and boosts inference speed.
- Ideal for memory-constrained or on-premise environments.

#### High-Throughput 4-bit Small Language Model

- Implements 4-bit quantization for minimal RAM/GPU requirements.
- Integrates `Flash Attention 2` and `Triton` fused kernels for high-throughput inference on modern hardware.

**Tech Stack:** `PyTorch`, `transformers`, `diffusers`, `Unsloth`, `LoRA`, `pruna`, `BitsAndBytes`, `Flash Attention 2`, `torch.compile`, `Docker`, `Cog`

### 3. [flux-fast-lora-hotswap](https://replicate.com/paragekbote/flux-fast-lora-hotswap)

Deployed a optimized version of `FLUX.1-dev` with ` LoRA`, a text-to-image model optimized for efficient and flexible serving.

- **Trigger-Based LoRA Hotswapping**: Implemented automatic loading of style-specific LoRA adapters based on keywords in the prompt (e.g., "ghibsky"), enabling seamless style switching.

- **4-bit Quantization (BitsAndBytes)**: Compressed model weights to 4-bit precision, reducing GPU memory usage while maintaining image quality.

- **torch.compile Runtime Acceleration**: Applied PyTorch runtime optimizations to cut down image generation latency and improve responsiveness.

- **Impact**: Achieved faster inference, lower memory footprint for text-to-image generation, thereby lowering overall computational cost.

**Tech Stack:** `PyTorch`, `transformers`, `diffusers`, `LoRA`, `BitsAndBytes`, `torch.compile`, `Cog`