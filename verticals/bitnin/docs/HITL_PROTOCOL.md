# BitNin — Protocolo HITL (Human-in-the-Loop)

Este documento describe cómo interactuar con la bandeja de revisión humana de BitNin en su fase shadow.

## 1. La Bandeja de Revisión (`hitl_inbox.md`)
La bandeja se encuentra en: `verticals/bitnin/runtime/observability/history/hitl_inbox.md`.
Es una tabla priorizada de eventos que el sistema considera "dignos de inspección".

## 2. Tipos de Prioridad
- **🔴 HIGH**: Eventos críticos.
  - Señales de alta confianza (`composite_state: HIGH`).
  - Divergencias causales críticas detectadas por el analista.
  - **Acción sugerida**: Revisar el scorecard completo inmediatamente.
- **🟡 MEDIUM**: Eventos de interés analítico o degradación técnica.
  - Caída brusca en cobertura narrativa (`narrative_crash`).
  - Patrón de abstención inusual.
  - **Acción sugerida**: Verificar la salud de los feeds de datos (GDELT/Qdrant).
- **🟢 LOW / Routine**: Ejecuciones nominales.
  - Comportamiento esperado dentro de los márgenes de salud.
  - **Acción sugerida**: Revisión opcional o de muestreo.

## 3. Flujo de Trabajo del Operador
1. **Abrir Inbox**: Revisar las entradas con estado `PENDING`.
2. **Inspección**: Seguir el enlace al `scorecard` correspondiente para entender el contexto analítico.
3. **Validación**: Comparar la señal de BitNin con la realidad del mercado (en modo observación).
4. **Actualización de Estado**: Una vez revisado, el operador puede cambiar manualmente el estado en el `.md` a `REVIEWED`.

## 4. Restricciones Críticas
- **HITL no es trading**: Este protocolo es para **auditoría analítica**.
- No se deben tomar decisiones financieras basadas en el Inbox.
- El sistema sigue operando en `shadow + dry_run` independientemente de la revisión humana.
