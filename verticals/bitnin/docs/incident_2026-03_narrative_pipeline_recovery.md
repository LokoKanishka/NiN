# Incident Report: Narrative Pipeline Recovery (29R)

**Date of incident resolution:** 2026-03-23
**Context:** Phase 29R (GA Shadow Certified)

## Síntoma Inicial
El dataset narrativo utilizado por el analista en la sombra mostraba una antigüedad estática (última modificación el 2026-03-16). A pesar de que los *ticks* del orquestador se ejecutaban exitosamente, la métrica de cobertura narrativa arrojaba consistentemente `0.0`.

## Diagnóstico Correcto
Se descartó que el publicador de narrativas fuese n8n/notenin, corrigiendo el mapa mental previo. El publicador real del dataset narrativo es `bitnin_narrative_builder`.
El pipeline de shadow (`run_shadow_pipeline.py`) ejecutaba el *tick* diario del analista leyendo el `narrative-v1-robust.jsonl` como baseline estático, **pero omitía reconstruir o refrescar la narrativa previamente**. No hubo fallo por error, sino por omisión arquitectónica/desconexión del paso GDELT.

## Fix Estructural Aplicado
Se realizó un cambio mínimo y directo en `scripts/run_shadow_pipeline.py`: se inyectó una ejecución `pre-step` invocando vía subprocess a `bitnin_narrative_builder` con los parámetros correspondientes (`--timespan 1d`, `--dataset-version narrative-v1-robust`, `--mode full`).

## Evidencia Final
El dataset narrativo ahora se actualiza en el directorio `raw` y se normaliza en `normalized` justo antes del *tick*.
**Estado final:** BitNin vuelve a observación pura (read-only) metodológicamente sana para continuar acumulando evidencia en la ventana 29R hasta la evaluación S1.
