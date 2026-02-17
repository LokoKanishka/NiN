# Project LUCY: Sovereign AI Automation Protocol

## 📖 Abstract
Este proyecto implementa un sistema de automatización "Zero-Learning" y totalmente soberano, diseñado para investigación académica y filosofía. Utiliza una arquitectura híbrida donde un **LLM Masivo (120B MoE)** actúa como el "Arquitecto" (planificación y razonamiento lógico) y **n8n** actúa como el "Ejecutor" (interconexión y tareas repetitivas).

El objetivo es eliminar la dependencia de servicios en la nube (SaaS), garantizando privacidad total de los datos y aprovechando el hardware local de alto rendimiento.

## 🏗 Arquitectura de Hardware ("LUCY")
El sistema corre íntegramente en infraestructura local (On-Premise):
* **CPU:** AMD Ryzen 9 7950X
* **GPU:** NVIDIA RTX 5090 (32GB VRAM) - *Inferencia Primaria*
* **RAM:** 128GB DDR5 - *Offloading para modelos masivos*
* **Almacenamiento:** NVMe Gen 5

## 🧠 Software Stack

### 1. El Cerebro: LM Studio + GPT-OSS-120B (MoE)
* **Rol:** Razonamiento complejo, análisis de textos filosóficos, y **generación de código JSON para flujos de trabajo**.
* **Modelo:** `gpt-oss-120b` (Mixture of Experts).
* **Configuración:** Cuantización mixta (Q4/Q5) con *GPU Offloading* parcial.
* **Justificación:** Se prioriza la profundidad de razonamiento sobre la velocidad de inferencia. El modelo opera de forma asíncrona.

### 2. El Cuerpo: n8n (Docker)
* **Rol:** Orquestación de tareas, conectividad API, manejo de archivos y ejecución de los planes trazados por la IA.
* **Modo:** Self-hosted (Fair-code).
* **Ventaja:** Sin costos por ejecución, sin límites de pasos.

## ⚙️ Configuración de Conexión (The Bridge)

Para que **n8n** utilice la potencia de **LUCY** sin salir a internet, se configura el nodo de OpenAI compatible apuntando al servidor local de LM Studio.

**En LM Studio:**
1.  Cargar modelo `gpt-oss-120b`.
2.  Iniciar Local Server (Puerto `1234`).

**En n8n (Credential Setup):**
* **Type:** OpenAI Chat Model
* **Base URL:** `http://host.docker.internal:1234/v1` (o la IP local de la máquina: `http://192.168.X.X:1234/v1`)
* **API Key:** `lm-studio` (Placeholder)
* **Model Name:** `gpt-oss-120b`

## 🚀 Flujo de Trabajo "Zero-Learning"

No se escriben flujos manualmente. Se utiliza la IA para diseñarlos:

1.  **Input:** El usuario solicita una tarea en lenguaje natural al modelo de 120B.
    > *"Analiza los PDFs de la carpeta 'Tesis', extrae las citas sobre teleología y guárdalas en un Markdown."*
2.  **Architecting:** El modelo 120B genera la estructura JSON del workflow de n8n necesaria para cumplir la tarea.
3.  **Execution:** Se importa el JSON en n8n y el sistema procesa la tarea de forma autónoma.

## 🛡 Privacidad y Ética
* **Soberanía de Datos:** Ningún dato (correos, borradores de tesis, análisis) sale de la red local.
* **Costos:** Costo operativo marginal (electricidad). Suscripciones SaaS = $0.

## 📂 Estructura del Proyecto
- `docker-compose.yml`: Configuración para desplegar n8n con acceso a la red del host.
- `docs/integration_config.md`: Guía detallada para conectar LM Studio y n8n.
- `prompts/architect_prompt.md`: Prompt del sistema para el "Arquitecto" (GPT-OSS-120B).

---
*Mantenido por Project LUCY - 2026*
