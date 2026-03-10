# NiN — Network in Network
> **Sovereign AI Automation | Zero Cloud Leak | $0 SaaS**

## 📖 Visión General
NiN es un ecosistema de automatización soberana diseñado para la orquestación de tareas complejas sin dependencia de la nube. Utiliza un modelo de inteligencia artificial local como motor lógico y **n8n** como motor de ejecución.

---

## 🏗️ Arquitectura Canónica Actual (SSOT)
El sistema NiN está consolidado bajo el siguiente estándar tecnológico:

- **Motor de Inferencia:** [Ollama](https://ollama.com/)
- **Modelo Operativo Único:** `qwen2.5-coder:14b-instruct-q8_0`
- **Orquestador:** n8n (Local Docker)
- **Memoria RAG:** Qdrant (Base vectorial local)
- **Privacidad:** Zero Cloud Leak (100% On-Premise)

---

## 🚀 Inicio Rápido

### 1. Requisitos
- Docker y Docker Compose instalados.
- Ollama corriendo en el host con el modelo `qwen2.5-coder:14b`.

### 2. Despliegue
Cualquier acción debe ser precedida por la lectura de las reglas operativas:
```bash
# Leer reglas obligatorias
cat .agents/workflows/operating_rules.md

# Levantar infraestructura NiN
docker-compose up -d
```

---

## 📚 Documentación de Referencia
Para agentes y desarrolladores, el orden de lectura para entender el estado actual es:

1. [operating_rules.md](file:///home/lucy-ubuntu/Escritorio/NIN/.agents/workflows/operating_rules.md) — Reglas de comportamiento.
2. [docs/ARCHITECTURE_CURRENT.md](file:///home/lucy-ubuntu/Escritorio/NIN/docs/ARCHITECTURE_CURRENT.md) — Fuente de Verdad Técnica.
3. [docs/ENTRY_POINT.md](file:///home/lucy-ubuntu/Escritorio/NIN/docs/ENTRY_POINT.md) — Guía de primer contacto y verificación.

---

## 🏺 Material Histórico
Si encuentras referencias a modelos MoE de 120B o LM Studio, consulta la carpeta `legacy/`. No utilices dicha documentación para configurar servicios activos.

---
*NiN — Soberanía Digital y Automatización Local (2026)*
