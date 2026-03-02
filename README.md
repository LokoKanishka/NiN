# Project LUCY: Sovereign AI Automation Protocol
> **NiN — Network in Network | Zero Cloud Leak | $0 SaaS**

## 📖 Abstract
Project LUCY is a sovereign automation system designed for academic research, philosophy, and high-complexity task orchestration. It leverages a massive **120B parameter Mixture-of-Experts (MoE)** model as the "Architect" for reasoning and planning, while **n8n** serves as the "Executor" for cross-platform integration and file management.

The core philosophy is **Data Sovereignty**: 100% on-premise execution, $0 SaaS dependency, and total privacy.

---

## 🚀 Quick Start

### 1. The Brain: LM Studio Setup
1. **Download the Model:** Run the setup script to download `gpt-oss-120b` (GGUF format):
   ```bash
   python3 scripts/download_model.py
   ```
2. **Load:** Open LM Studio and load the model with maximum GPU offloading.
3. **Local Server:** Start the local server on `http://localhost:1234`.

### 2. The Body: n8n Docker Startup
From the **project root** (`~/Escritorio/NIN`):
```bash
docker-compose up -d
```
Access the interface at `http://localhost:5688/home/workflows`.

> **Tip:** Use the **NIN** desktop shortcut to open the workflows panel directly with one click.

### 3. The Bridge: Integration
In n8n, create an **OpenAI API** credential:
- **Base URL:** `http://host.docker.internal:1234/v1`
- **Model:** `gpt-oss-120b`

---

## 🔧 Troubleshooting

### UI doesn't load after system reboot or Docker restart
After a `sudo systemctl restart docker`, existing containers may lose their port mappings. Fix with:
```bash
cd ~/Escritorio/NIN
docker-compose down && docker-compose up -d --force-recreate
```
Verify connectivity:
```bash
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5688
# Expected: 200
```

### DNS errors in n8n logs (`EAI_AGAIN`)
Errors contacting `telemetry.n8n.io` or `posthog.com` are **expected and harmless** — the system operates in Zero Cloud Leak mode and these telemetry hosts are intentionally unreachable.

---

## 🏗 Hardware Architecture
| Component | Spec |
|-----------|------|
| CPU | AMD Ryzen 9 7950X |
| GPU | NVIDIA RTX 5090 (32GB VRAM) — Primary Inference |
| RAM | 128GB DDR5 — Offloading support |
| Storage | Gen 5 NVMe — Ultra-fast model loading |

---

## 🧠 Software Components & Agent Swarm

El Proyecto LUCY opera como un enjambre de agentes (Agent Swarm).

### 1. The Architect (Antigravity / Mission Control)
Responsable de la toma de decisiones, asimilación del usuario y orquestación del servidor/agentes.

### 2. The Engineer (n8n Engineer)
Un agente especializado para el control total del ecosistema n8n mediante el servidor `mcp-n8n`.
Regido estrictamente por el protocolo de **Research-Plan-Implement (RPI)**. 

### 3. The Local Executor (Alt - Qwen 14B)
Modelo local Open Source blindado. Opera con 0 dependencias Cloud y actúa como el "Músculo" del cluster NiN.

### 4. The Cloud Brains
- **Groq LPU (Llama 3.3 70B)**: Para velocidad y código de cero-latencia.
- **Sistema Colmena**: Delegación a plataformas Drive para ingesta masiva (RAG asíncrono).

### 5. The Nervous System (n8n)
Orchestrates file reading, external API endpoints, and webhooks. Reparado a prueba de fallos 500.

---

## 📂 Project Structure
```
NIN/
├── docker-compose.yml       # Sovereign n8n environment
├── data/                    # Shared input/output folder (mounted to /data in n8n)
├── docs/
│   ├── integration_config.md
│   └── sample_workflow.json
├── prompts/
│   └── architect_prompt.md  # Logical core of the system
├── models/                  # GGUF model storage
├── find_models.py
└── nin_client.py            # Remote workflow activation via webhooks
```

## 🛡 Security & Ethics
- **Zero Cloud Leak:** All reasoning and data processing stay within your local network.
- **Zero SaaS Cost:** No OpenAI, no Zapier, no cloud dependencies.
- **Academic Rigor:** Designed for deep textual analysis and philosophical research.

---
*Mantenido por Project LUCY — 2026*
