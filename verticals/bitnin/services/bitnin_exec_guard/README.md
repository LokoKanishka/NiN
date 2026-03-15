# bitnin-exec-guard

Este servicio implementa el ejecutor local para la vertical BitNin.

## Advertencia de Fase 10

**ESTE SERVICIO NO EJECUTA INTENCIONES FINANCIERAS REALES.**
En esta fase (Fase 10), el `bitnin-exec-guard` opera **exclusivamente en dry_run**. 
No interactúa con exchanges, ni mueve fondos locales o wallets reales. Su único propósito es:
1. Recibir una intención (`trade_intent`) aprobada.
2. Validar precondiciones y guardrails duros.
3. Decidir si la ejecución pasaría o sería rechazada.
4. Generar trazabilidad total (`execution_record`) en `runtime/execution/`.

`approved` NO implica ejecución automática ni movimiento de fondos. Las intenciones aprobadas son únicamente candidatos a validación por este servicio. El plano analítico está estrictamente separado del plano ejecutor.
