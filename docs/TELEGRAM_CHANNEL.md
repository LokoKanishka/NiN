# NIN | Canal Telegram — Arquitectura Oficial

**Estado:** VIGENTE
**Fecha:** 2026-03-10

---

## Canal Canónico de Entrada

**n8n Telegram Trigger (webhook)** es el único mecanismo oficial de ingreso de mensajes Telegram.

| Aspecto | Decisión |
|:---|:---|
| **Entrada** | n8n Telegram Trigger (webhook automático) |
| **Salida (scripts)** | Permitida via `TG_TOKEN` desde `.env` |
| **Long polling** | PROHIBIDO con el mismo bot si webhook está activo |

## Motivo

Telegram no permite usar `getUpdates` (long polling) mientras haya un webhook configurado para el mismo bot. El nodo Telegram Trigger de n8n registra un webhook al activarse. Usar polling en paralelo causa conflicto de mensajes.

## Consecuencias

1. **`nin_demon.py`** y **`nin_megademon.py`** ya NO deben ejecutar `telegram_ears_loop()` con `getUpdates` mientras el webhook de n8n esté activo.
2. Ambos scripts conservan su función de **envío** de mensajes via `send_telegram_message()` (eso es salida, no colisiona).
3. El nuevo workflow **`nin_bibliotecario.json`** usa Telegram Trigger como trigger oficial.

## Variables de Entorno

Todos los scripts usan variables de `.env`:

```
TG_TOKEN=<token del bot>
TG_CHAT_ID=<chat_id autorizado>
```

No quedan tokens hardcodeados en código activo.

## Diagrama

```
Telegram → webhook → n8n (Telegram Trigger) → Router → Bibliotecario / Servicios
                                                     ↘ Scripts (solo envío)
```

---
**Certificado por:** Antigravity AI (Marzo 2026)
