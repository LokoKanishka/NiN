# BitNin — Protocolo HITL (Human-in-the-Loop)

Este documento describe cómo interactuar con la bandeja de revisión humana de BitNin en su fase shadow.

## 1. La Gestión de Casos (Expedientes)
BitNin ya no genera simples alertas, sino **Casos** estructurados. Cada caso es una unidad de revisión auditable que agrupa evidencia técnica y decisiones humanas.

### Ubicaciones Clave:
- **Bandeja de Entrada Activa (`hitl_inbox.md`)**: Solo contiene casos en estado `PENDING` o `ESCALATED`. Es tu espacio de trabajo diario.
- **Archivo Histórico (`hitl_archive.md`)**: Registro de todos los casos cerrados (`REVIEWED`, `DISMISSED`). Es tu historial de auditoría.
- **Fuente de Verdad (`hitl_state.json`)**: Registro canónico estructurado que garantiza la integridad de los datos.

## 2. Flujo de Trabajo del Operador (Workflow)
El sistema utiliza estados para gestionar el ciclo de vida de cada expediente:
- **PENDING**: Caso nuevo detectado por el supervisor. Requiere inspección.
- **REVIEWED**: El operador ha validado la señal y adjuntado sus notas. El caso se mueve al archivo.
- **DISMISSED**: El operador considera el ítem irrelevante. Se archiva con motivo de descarte.
- **ESCALATED**: El caso requiere revisión técnica profunda. Permanece en el inbox.

### Protocolo de Cierre Documental:
1. **Inspección**: Abrir el link al `Scorecard` desde el inbox.
2. **Juicio**: Evaluar si la señal de BitNin es consistente con el baseline y el mercado.
3. **Registro**: Editar la columna `Status` (cambiar `PENDING` por `REVIEWED` o `DISMISSED`) y añadir una nota breve en `Operator Notes`.
4. **Sincronización**: En la siguiente corrida del sistema (o vía manual), BitNin detectará tu cambio, actualizará el JSON y moverá el expediente al archivo histórico.

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
