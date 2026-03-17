# BitNin — Protocolo HITL (Human-in-the-Loop)

Este documento describe cómo interactuar con la bandeja de revisión humana de BitNin en su fase shadow.

## 1. La Bandeja de Revisión (`hitl_inbox.md`)
La bandeja se encuentra en: `verticals/bitnin/runtime/observability/history/hitl_inbox.md`.
Es una tabla priorizada de eventos que el sistema considera "dignos de inspección".

## 2. Flujo de Trabajo del Operador (Workflow)
El sistema utiliza estados para gestionar el ciclo de vida de cada alerta:
- **PENDING**: Ítem nuevo. Requiere atención.
- **REVIEWED**: El humano ha inspeccionado el ítem y validado la señal.
- **DISMISSED**: El ítem se considera ruido o no relevante (ej. degradación técnica conocida).
- **ESCALATED**: El ítem requiere una investigación profunda o ajuste del sistema.

### ¿Cómo actualizar estados?
Actualmente, el operador puede editar manualmente el archivo `hitl_inbox.md`, cambiando la columna `Status` y agregando una nota en `Decision/Note`. El sistema respeta los cambios realizados manualmente.

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
