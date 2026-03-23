# BitNin Shadow Governance Framework

Este documento define el marco institucional para la supervisión, medición y gobierno de BitNin en su fase **GA Shadow**.

## 1. Pilares de Medición (KPIs)

### 1.1 KPI Operativo (Estabilidad de Plataforma)
- **Scheduler Uptime**: Porcentaje de ticks ejecutados vs. esperados (Meta: >98%).
- **Data Freshness**: Latencia máxima entre el reloj real y el último `health_snapshot` (Meta: < 15 min).
- **Restore Reliability**: Éxito de las pruebas de restauración periódicas (Meta: 100%).
- **Backup Integrity**: Presencia y validez de bundles diarios.

### 1.2 KPI Analítico (Calidad de Señal)
- **Narrative Coverage**: Promedio de eventos narrativos procesados por ventana (Meta: > 0.5 per sample).
- **Composite Signal Strength**: Consistencia de la Señal Compuesta (`v3`).
- **Memory Hit Rate**: Recurrencia de acceso a la Memoria Activa.
- **Divergence Rate**: % de casos con prioridad `HIGH` (Divergencia entre técnica y narrativa).

### 1.3 KPI Humano (Eficiencia HITL)
- **Backlog Volume**: Cantidad de casos pendientes al cierre del día (Meta: < 5).
- **RTTR (Response Time to Review)**: Tiempo promedio desde la creación del caso hasta la decisión humana.
- **Escalation Index**: % de casos que requieren intervención de nivel superior (`ESCALATED`).

## 2. Taxonomía de Incidentes

| Categoría | Descripción | Impacto |
|---|---|---|
| `INFRA` | Problemas de disco, red o sistema operativo base. | Crítico |
| `RUNTIME` | Crash de servicios, locks de archivos o errores de Python. | Crítico |
| `FEED` | Ausencia prolongada o corrupción de datos narrativos/mercado. | Mayor |
| `DRIFT` | Degradación sostenida de la calidad de la señal analítica. | Mayor |
| `HITL` | Inactividad del operador o retraso crítico en toma de decisiones. | Menor |
| `FALSE-POSITIVE` | Generación excesiva de casos de baja relevancia. | Menor |

## 3. Promotion Gate: Rumbo a "Pilot"

Para que BitNin sea considerado para la fase **Pilot** (ejecución simulada con balance no real pero bajo presión real), debe cumplir:
1. **Burndown**: 4 semanas consecutivas sin incidentes `INFRA` o `RUNTIME`.
2. **Disciplina**: Cierre de jornada (`day-close`) con 100% de cumplimiento.
3. **Estabilidad**: Drift Detection dentro de umbrales nominales en el 90% de los lotes.
4. **Resiliencia**: Al menos un `DR Drill` exitoso (completado en Fase 26).

## 4. Ritual de Gobernanza Semanal
1. Ejecutar `./bin/bitnin-ctl weekly-scorecard`.
2. Revisar incidentes clasificados.
3. Validar estado de la señal compuesta contra KPIs analíticos.
4. Emitir veredicto semanal: `STABLE`, `WATCH` o `INVESTIGATE`.

## 5. Historial de Incidentes
- **2026-03-23**: Incidente `FEED` resuelto (Narrative Pipeline Recovery). Ver acta para más detalles.

---
*Nota: La ejecución de este marco comenzó formalmente el 2026-03-17. Ver: [Acta de Inicio: Ventana Real de Gobernanza](file:///home/lucy-ubuntu/Escritorio/NIN/verticals/bitnin/docs/real_governance_window_start.md).*
