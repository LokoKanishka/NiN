# Project LUCY: Sovereign AI Automation Protocol

## 📖 Abstract
Project LUCY is a "Zero-Learning" sovereign automation system designed for academic research, philosophy, and high-complexity task orchestration. It leverages a massive **120B parameter Mixture-of-Experts (MoE)** model as the "Architect" for reasoning and planning, while **n8n** serves as the "Executor" for cross-platform integration and file management.

The core philosophy is **Data Sovereignty**: 100% on-premise execution, $0 SaaS dependency, and total privacy.

---

## 🚀 Quick Start (Gesta de LUCY)

### 1. The Brain: LM Studio Setup
1.  **Download the Model:** Use the `gpt-oss-120b` (GGUF format by Bartowski or Unsloth) for local inference.
2.  **Load:** Load the model in LM Studio with maximum GPU offloading (RTX 5090 / 128GB RAM recommended).
3.  **Local Server:** Start the local server on `http://localhost:1234`.

### 2. The Body: n8n Docker Startup
From the project root:
```bash
docker-compose up -d
```
Access the interface at `http://localhost:5678`.

### 3. The Bridge: Integration
In n8n, create an **OpenAI API** credential:
- **Base URL:** `http://host.docker.internal:1234/v1`
- **Model:** `gpt-oss-120b`

---

## 🏗 Hardware Architecture
Optimization for local inference of massive models:
*   **CPU:** AMD Ryzen 9 7950X
*   **GPU:** NVIDIA RTX 5090 (32GB VRAM) - *Primary Inference*
*   **RAM:** 128GB DDR5 - *Offloading support*
*   **Storage:** Gen 5 NVMe (Ultra-fast model loading)

## 🧠 Software Components

### 1. The Architect (`gpt-oss-120b`)
Generates logical plans and **valid n8n workflow JSON** from natural language. See `prompts/architect_prompt.md` for the core system instructions.

### 2. The Executor (n8n)
Orchestrates file reading (PDFs, CSVs), API calls, and Markdown generation. Operates autonomously based on the Architect's JSON output.

---

## 📂 Project Structure
- `docker-compose.yml`: Sovereign n8n environment.
- `docs/integration_config.md`: Multi-step integration guide.
- `docs/sample_workflow.json`: Example "Zero-Learning" workflow.
- `prompts/architect_prompt.md`: The logical core of the system.
- `models/`: Suggested directory for GGUF model storage.

## 🛡 Security & Ethics
- **Zero Cloud Leak:** All reasoning and data processing happen within your local network.
- **Academic Rigor:** Designed specifically for deep textual analysis and philosophical research.

---
*Mantenido por Project LUCY - 2026*
