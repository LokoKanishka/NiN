# NIN | Arquitectura Canónica Actual (SSOT)

**Fecha:** 2026-03-06
**Versión:** 1.0.0
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
| **Búsqueda** | SearXNG | Motor de búsqueda local soberano. | `http://localhost:8080` |
| **Base Vectorial** | Qdrant | Memoria RAG a largo plazo. | `http://localhost:6335` |

## 2. Modelos en Uso
El motor de inferencia oficial es **Ollama**.
- **Demonio 14B (notenin):** `qwen2.5:14b` (Investigación y síntesis).
- **Mapeador (Secret Agent):** `qwen2.5:32b` (Razonamiento complejo).
- **Embedded:** `nomic-embed-text` (Vectores).

> [!WARNING]
> **LM Studio (Puerto 1234) es LEGADO.** No se utiliza en la arquitectura actual. Ignorar cualquier referencia a `gpt-oss-120b`.

## 3. Workflows Core (Producción)
Los flujos de trabajo críticos que mantienen NIN operativo son:
1. **Pilar 1: Doctor System (`mSjsiVaTv5sfb99E`):** Sistema inmunológico (monitorea Docker).
2. **notenin researcher (`6iwgu2R2WDXyUHYN`):** Investigador autónomo con blindaje de red.
3. **NIN Telegram Service (`WrslsGzYsDP8hJZT`):** Puente unificado de comunicación.

## 4. Topología de Red Interna
- Los contenedores se comunican con el Host a través del bridge `host-gateway`.
- El alias oficial para servicios del host (Ollama) es `host.docker.internal`.

## 5. Árbol de Lectura para Agentes (Precedencia)
Cualquier agente que intervenga en NIN debe leer la documentación en este orden exacto:
1. `operating_rules.md` (Cómo comportarse).
2. `docs/ARCHITECTURE_CURRENT.md` (Cómo funciona el sistema HOY).
3. `docker-compose.yml` (Cómo se despliega el sistema).
4. `audit_protocol.md` (Historial de estabilidad reciente).

## 6. Áreas Sensibles y Restricciones
- **No modificar:** El socket de Docker (`/var/run/docker.sock`) ni la configuración de red `extra_hosts` sin aprobación explícita.
- **No duplicar:** La mensajería debe pasar siempre por el servicio unificado de Telegram.
- **Ruido Runtime:** Ignorar carpetas `node_modules`, `data`, `memoria` y archivos `.db`. Son subproductos operativos, no arquitectura.

---
**Certificado por:** Antigravity AI - Agente de Arquitectura NIN
