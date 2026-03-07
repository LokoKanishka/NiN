# NiN: Gobernanza del Ecosistema n8n 🌊🔧

Este documento establece las reglas obligatorias para la creación, modificación y mantenimiento de workflows en la instancia de n8n del proyecto NiN.

## 1. El Catálogo Vivo (`catalog.db`)
La fuente de verdad (SoT) de qué workflows están activos y qué función cumplen es la tabla `live_workflows` en `library/catalog.db`. 

**Regla de Oro:** Ningún workflow debe ser invocado por un script de Python si no está registrado en el catálogo.

## 2. Clasificación de Workflows
Todo workflow debe pertenecer a una de estas categorías:
- **CORE**: Herramientas críticas del sistema (MCP, Memoria, File Ops).
- **VERTICAL**: Servicios de negocio o misiones complejas (Investigación, Doctor, Telegram).
- **TEST**: Pruebas temporales o sandboxing. Deben ser eliminados o migrados tras validación.
- **LEGACY**: Workflows de proyectos anteriores o versiones obsoletas marcadas para depuración.

## 3. Autoridad Funcional
- Solo puede existir **un (1) workflow** con `authority=1` por cada vertical funcional.
- Las tareas de Python deben buscar el `workflow_id` resolviendo el `slug` o la función en el catálogo, no mediante hardcodeo (Objetivo NiN 1.1).

## 4. Convención de Nomenclatura (n8n)
Para mantener el orden visual, los nombres en n8n deben seguir este prefijo:
- `NIN | [Nombre]` para CORE/VERTICAL activos.
- `Tool: [Nombre]` para herramientas expuestas al MCP.
- `TEST | [Nombre]` para pruebas.

## 5. Gestión de Dependencias
Al crear un workflow que será llamado por un script, se debe registrar el nombre del script en el campo `dependencies` (formato JSON list) del catálogo.

---
**Cierre de Fase:** Esta normativa entra en vigor con la implementación del Catálogo Vivo MVP (7 de marzo de 2026).
