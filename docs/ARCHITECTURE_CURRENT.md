# NIN | Arquitectura Canónica Actual (SSOT)

**Fecha:** 2026-03-06
**Versión:** 1.1.0
**Estado:** DOCUMENTO MAESTRO VIGENTE

> [!IMPORTANT]
> Este archivo es la fuente de verdad definitiva del proyecto NIN. Ante cualquier contradicción con el `README.md`, se considera que este documento y el `docker-compose.yml` representan la realidad operativa actual.

---

## 1. Stack de Infraestructura Real
El sistema NIN opera bajo un modelo de **Soberanía de Datos Local** utilizando Docker en Linux.

| Componente | Tecnología | Rol | Endpoint de Producción |
| :--- | :--- | :--- | :--- |
| **Orquestador** | n8n | Cerebro lógico y disparador de eventos. | `http://localhost:5688` |
| **Inferencia** | Ollama | Motor de IA (notenin, Doctor, Mapeador). | `http://host.docker.internal:11434` |
| **Escucha/Alertas** | Telegram | Canal único de notificaciones. | `/webhook/sirena-telegram` |
| **Búsqueda** | SearXNG | Motor de búsqueda local soberano. | `http://localhost:8080` (searxng-lucy) |
| **Base Vectorial** | Qdrant | Memoria RAG a largo plazo. | `http://localhost:6335` |
| **Bridge MCP** | JS/Node | Conector de infraestructura NiN. | `scripts/nin_mcp_bridge.js` |

> [!WARNING]
> **Contexto de Vecinos:** Este host convive con otros entornos (ej. `Fusion`, `Doctor Lucy`). **NO TOCAR** contenedores como `lucy_fusion_*` o `doctor_lucy_n8n` por error. Solo intervenir en los servicios definidos en el `docker-compose.yml` de este directorio.
> **Puertos Confusos:** Distinguir `searxng-lucy` (8080 - Oficial) de `lucy_eyes_searxng` (8081 - Externo).

## 2. Modelos en Uso
El motor de inferencia oficial y único para la operación de NIN es **Ollama**.
- **Motor Único (notenin / Mapeador / Demonio):** `qwen2.5-coder:14b-instruct-q8_0` (Investigación, síntesis y razonamiento).
- **Embedded:** `nomic-embed-text` (Vectores).

> [!NOTE]
> NIN utiliza exclusivamente la cuantización **Q8** para el modelo 14B para optimizar el equilibrio entre precisión y latencia en hardware local. No se utilizan variantes BF16/FP16 en la operativa estándar.

## 3. Workflows Core (Producción)
Los flujos de trabajo críticos que mantienen NIN operativo son:
1. **Pilar 1: Doctor System (`mSjsiVaTv5sfb99E`):** Sistema inmunológico (monitorea Docker).
2. **notenin researcher (`6iwgu2R2WDXyUHYN`):** Investigador autónomo con blindaje de red.
3. **NIN Telegram Service (`WrslsGzYsDP8hJZT`):** Puente unificado de comunicación.

## 4. Topología de Red y Rutas
- **Comunicación:** Bridge `host-gateway` con alias `host.docker.internal`.
- **Hogar de Datos:** La carpeta `data/` del root es obsoleta. El nuevo hogar de todo el ruido operativo, bases de datos (.sqlite, .db) y estado es la carpeta **`runtime/`**.

## 7. Capacidades Latentes y Periferia
Para entender qué scripts y workflows de la periferia son operativos y cuáles son candidatos a legacy, consultar:
- [CAPABILITIES_MAP.md](file:///home/lucy-ubuntu/Escritorio/NIN/docs/CAPABILITIES_MAP.md)

---

## 8. Árbol de Lectura para Agentes (Precedencia)
Cualquier agente que intervenga en NIN debe leer la documentación en este orden exacto:
1. `operating_rules.md` (Cómo comportarse).
2. `docs/ARCHITECTURE_CURRENT.md` (Cómo funciona el sistema HOY).
3. `docs/CAPABILITIES_MAP.md` (Habilidades latentes y periferia).
4. `docs/ENTRY_POINT.md` (Cómo empezar a trabajar de forma segura).
5. `docker-compose.yml` (Cómo se despliega el sistema).

## 6. Áreas Sensibles y Restricciones
- **No modificar:** El socket de Docker (`/var/run/docker.sock`) ni la configuración de red `extra_hosts`.
- **Categorización de Archivos:**
    - **Core:** `docs/`, `workflows/`, `scripts/`.
    - **Verticales:** `verticals/` (Trading, CV).
    - **Ruido Runtime:** `runtime/`, `node_modules/`. **IGNORAR** en lecturas de arquitectura.
    - **Legado:** `legacy/` (Material histórico). **NO USAR** como base técnica.

---
**Certificado por:** Antigravity AI - Agente de Arquitectura NIN
