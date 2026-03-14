# BitNin Shadow

Servicio local para correr el analista como si operara, sin ejecutar nada.

## Principios

- shadow no es ejecucion
- no usa Telegram ni HITL
- registra intencion, reporte y revision posterior
- toda salida es local, persistida y auditable

## Flujo

1. invoca al analista actual
2. construye una `trade_intent` shadow
3. persiste reporte local
4. opcionalmente revisa la intencion despues de su vigencia

## Estado

- `no_trade` e `insufficient_evidence` tambien generan intentos shadow
- `approved` queda siempre en `false`
- ninguna salida toca fondos ni servicios externos
