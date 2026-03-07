# NIN | Mapa de Capacidades Latentes 🛡️🔍

Este documento cataloga los artefactos (scripts y workflows) que residen en la periferia del sistema pero que cumplen funciones reales, estratégicas o están en hibernación técnica, diferenciándolos del ruido o material puramente legado.

---

## 0. Autoridad Funcional (Regla de la Capa Superior) ⚖️
Para evitar ambigüedad operativa en NIN, se aplica el siguiente criterio de precedencia:
1.  **VERTICAL:** Si existe una carpeta en `verticals/` para una tarea, esa es la **AUTORIDAD MÁXIMA**.
2.  **WORKFLOW CORE:** Si no hay vertical, el workflow en n8n es la autoridad lógica.
3.  **SCRIBIT/UTILITY:** Los archivos en `scripts/` son herramientas de apoyo, fallbacks o patrones históricos, NO la autoridad de decisión.

---

## 1. Clasificación por Capas

| Clase | Descripción | Elementos |
| :--- | :--- | :--- |
| **CORE** | Funciones críticas para la operación o razonamiento. | `agente_secreto_mapeador`, `youtube_launcher_service.py` |
| **CORE LATENTE** | Infraestructura de soporte y diagnóstico. | `youtube_watchdog.py`, `agente_estado_...` |
| **VERTICAL** | Lógica específica de una línea de negocio/acción. | `book_fetcher.py`, `telegram_book_sender.py` |
| **HIBERNACIÓN** | Prototipos funcionales no activos hoy. | `agente_leer_...` |
| **CANDIDATO LEGACY** | Material redundante o sin uso previsto. | `scrape_templates.py`, `tool_notebook` |

---

## 2. Inventario Detallado

### A. Capa de Video y Host (YouTube)
*   **`scripts/youtube_launcher_service.py`**
    - **Función:** Abre el navegador en el host (Puerto 9999) para visualización de contenido.
    - **Estado:** **VIVO**. Referenciado en `runtime/memoria/sistemas/youtube/`.
    - **Dependencia:** Acceso a X11/Display del host.
*   **`scripts/youtube_watchdog.py`**
    - **Función:** Asegura que el servicio de lanzamiento esté arriba.
    - **Estado:** **LATENTE**. Soporte de resiliencia.

### B. Capa de Conocimiento (Libros)
*   **`scripts/book_fetcher.py`**
    - **Función:** Motor de búsqueda de bibliografía externa.
    - **Estado:** **VIVO**. Usado por el Demonio (`nin_demon.py`) para misiones de investigación.
*   **`scripts/telegram_book_sender.py`**
    - **Función:** Envía archivos a dispositivos Kindle/Telegram.
    - **Estado:** **VERTICAL**. Parte de la automatización de biblioteca personal.

### C. Capa de Orquestación (Agentes)
*   **`workflows/agente_secreto_mapeador`**
    - **Función:** Orquestador de razonamiento complejo (DeepSeek-32B).
    - **Estado:** **CORE**. Indispensable para misiones de análisis profundo.
*   **`workflows/agente_estado_...`**
    - **Función:** Diagnóstico de salud de servicios y contenedores.
    - **Estado:** **LATENTE**. Herramienta de auditoría bajo demanda.
*   **`workflows/agente_leer_...`**
    - **Función:** Interfaz de ingesta de documentos para otros agentes.
    - **Estado:** **HIBERNACIÓN**. Útil para futuras misiones de lectura masiva.

---

## 3. Resoluciones de Autoridad (Fase 2.5)

### Caso 1: Automatización de CVs 📧
- **Autoridad:** **`verticals/gmail_cv/`** (Vertical estructurada).
- **Estatus de `scripts/send_cvs.py`:** **LEGACY-PATTERN / APOYO**. No debe usarse como punto de entrada operativo. Su lógica de filtrado es referencia para la vertical.

### Caso 2: Búsqueda OSINT / Tavily 🔍
- **Autoridad:** **Workflow n8n** (Capa de orquestación y misiones).
- **Estatus de `scripts/tavily_search.py`:** **UTILITY / FALLBACK**. Herramienta de consulta rápida para el demonio o terminal, sin peso en la lógica de decisión.

---

## 4. Zona de Pre-Legacy (Próxima Poda)
Artefactos que no han demostrado valor operativo en el stack actual y serán movidos a `legacy/` en la Fase 2:
- `scrape_templates.py`: Superado por la curaduría manual de la Biblioteca.
- `tool_notebook`: Redundante con el sistema de memoria persistente de Antigravity.

---

**Nota para Agentes:** NO considerar estos archivos como ruido. Antes de intervenir, consultar este mapa para evitar roturas de capacidades latentes. 🛡️
