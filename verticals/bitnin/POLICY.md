# BitNin Policy

Estado: obligatorio para Fase 0-1

## Guardrails iniciales

1. No ejecucion financiera en v1.
   - Ningun workflow, script o schema de BitNin habilita compra, venta o custodia real.
2. No scraping masivo de medios con restricciones.
   - Se permite discovery, metadata, links y resumen local propio.
   - No se debe persistir texto completo de medios restrictivos a escala.
3. No polling Telegram si existe webhook activo.
   - BitNin hereda la politica oficial de `docs/TELEGRAM_CHANNEL.md`.
4. No usar el n8n privilegiado actual para ejecucion real.
   - El `n8n` existente puede servir como plano de control o shadow, no como runtime financiero real en v1.
5. Todo artefacto persistido debe quedar en UTC.
   - Logs, datasets, approvals, analisis y records.
6. No usar vectores dummy en Qdrant.
   - Todo indexado debe usar embeddings reales y metadata trazable.
7. No asumir dimension de embeddings.
   - La dimension debe declararse por config o metadata del lote.
8. `no_trade` e `insufficient_evidence` son salidas validas del analista.
   - Nunca deben tratarse como fallas del sistema.
9. Shadow y simulacion son los unicos modos validos en v1.
   - Cualquier `execution_record` de v1 debe reflejar `simulation` o `shadow`.
10. Ninguna credencial financiera, seed, wallet o bridge real entra en esta vertical durante Fase 0-1.
11. Telegram HITL usa webhook canonico, no polling.
   - Una aprobacion humana no implica ejecucion.
   - No se permite `getUpdates` paralelo para BitNin.

## Regla operativa

Si una decision futura contradice esta policy, prevalece esta policy hasta que exista una revision explicita de la vertical.
