# BitNin HITL

Servicio local para approval/reject formal de intenciones shadow, usando el patron canonico de Telegram via webhook.

## Principios

- approval no implica ejecucion
- Telegram entra por webhook, no por polling
- toda decision queda persistida
- expiracion es un estado formal

## Flujo

1. tomar un `trade_intent` shadow
2. generar `approval_request`
3. renderizar mensaje Telegram corto
4. registrar `approved`, `rejected` o `expired`
5. persistir snapshot

## Alcance

- crea artefactos HITL y workflows BitNin listos para revision
- no activa nada en produccion
- no toca fondos ni ordenes reales
