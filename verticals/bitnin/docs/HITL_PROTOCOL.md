# BitNin — Protocolo HITL (Human-in-the-Loop)

Este documento describe cómo interactuar con la bandeja de revisión humana de BitNin en su fase shadow.

## 1. Gestión vía Consola HITL (`hitl_ctl.py`)
A partir de la Fase 22, la interacción humana con BitNin se realiza exclusivamente a través de la CLI operativa. Las vistas Markdown son ahora de **solo lectura**.

### Comandos Principales:
- `python3 hitl_ctl.py list`: Muestra los casos pendientes en el inbox.
- `python3 hitl_ctl.py show <run_id>`: Ver detalles, links de evidencia y **timeline** completo de un caso.
- `python3 hitl_ctl.py review <run_id> --note "..."`: Valida una señal y archiva el caso.
- `python3 hitl_ctl.py dismiss <run_id> --note "..."`: Descarta un ítem y lo archiva.
- `python3 hitl_ctl.py escalate <run_id> --note "..."`: Marca un caso para revisión técnica profunda.

## 2. Línea de Tiempo (Timeline) y Trazabilidad
Cada expediente mantiene un historial cronológico de todas las interacciones:
- **detección**: Cuándo el supervisor identificó el caso.
- **review/dismiss/escalate**: Quién y con qué nota cerró el ciclo.
- **reopen**: Si un caso archivado requiere atención nueva.

## 3. Vistas Proyectadas (Solo Lectura)
- **Inbox (`hitl_inbox.md`)**: Refleja casos `PENDING` o `ESCALATED`. No editar manualmente.
- **Archive (`hitl_archive.md`)**: Refleja casos `REVIEWED` o `DISMISSED`.
- **Digest (`hitl_digest.md`)**: Resumen analítico de la salud y el backlog.

> [!IMPORTANT]
> El sistema regenera estas vistas automáticamente tras cada comando de la CLI o ejecución del supervisor. Cualquier edición manual en el Markdown será sobrescrita por el estado canónico de `hitl_state.json`.

## 3. Resumen Ejecutivo (`hitl_digest.md`)
Cada ejecución exitosa genera o actualiza el `hitl_digest.md`. Este archivo es la primera parada para el supervisor:
- **Resumen de Salud**: Estado de infra y métricas críticas.
- **Alertas Rojas**: Enlace directo a los ítems `HIGH PRIORITY`.
- **Patrones**: Detecta anomalías acumuladas.

## 4. Deduplicación y Aging
- **Agrupación**: Si el sistema detecta alertas repetitivas de la misma tipología, el digest las presentará de forma consolidada para evitar la fatiga de alertas.
- **Limpieza**: Ítems en estado `PENDING` con más de 7 días se marcarán visualmente como obsoletos o se archivarán automáticamente.

## 4. Restricciones Críticas
- **HITL no es trading**: Este protocolo es para **auditoría analítica**.
- No se deben tomar decisiones financieras basadas en el Inbox.
- El sistema sigue operando en `shadow + dry_run` independientemente de la revisión humana.
