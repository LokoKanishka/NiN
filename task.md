# Ticket: Reconectar build narrativo al ciclo shadow antes del analyst tick

## Tareas
- [x] 1. Identificar el punto exacto de inserción y parámetros de `bitnin_narrative_builder`
- [x] 2. Diseñar el cambio mínimo en `run_shadow_pipeline.py` o `supervisor.py`
- [x] 3. Implementar la reconexión (invocar builder, actualizar RAW y NORMALIZED)
- [x] 4. Validar end-to-end con una corrida controlada
- [x] 5. Generar entregables obligatorios (diff, git status, etc.)
