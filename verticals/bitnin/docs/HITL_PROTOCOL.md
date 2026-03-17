# BitNin — Protocolo HITL (Human-in-the-Loop)

Este documento describe cómo interactuar con la bandeja de revisión humana de BitNin en su fase shadow.

## Control Operativo: bitnin_ctl.py
A partir de la Fase 23, toda la operación de BitNin se centraliza en la herramienta `bitnin_ctl.py` ubicada en la raíz del proyecto.

### Comandos de Supervisión
- `./bitnin_ctl.py status`: Vista 360° de salud, scheduler y backlog.
- `./bitnin_ctl.py briefing`: Resumen ejecutivo del día y acciones recomendadas.
- `./bitnin_ctl.py scheduler`: (Próximamente unificado) Estado del timer systemd.

### Gestión de Casos (HITL)
- `./bitnin_ctl.py cases list`: Lista casos filtrados por estado (PENDING por defecto).
- `./bitnin_ctl.py cases show <case_id>`: Inspección profunda de un expediente incluyendo su **timeline**.
- `./bitnin_ctl.py cases review <case_id> --note "..."`: Valida y archiva un caso.
- `./bitnin_ctl.py cases dismiss <case_id> --note "..."`: Descarta y archiva un caso.

## Identificadores Canónicos
- **Case ID** (e.g., `CASE-20260317-001`): Identidad humana única del expediente. Es el ID principal para la CLI.
- **Run ID**: Referencia técnica a la corrida analítica.
- **Batch ID**: Identificador del lote de procesamiento.

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
