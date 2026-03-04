# Registro de Memoria: n8n Sync NiN

Este documento mantiene el estado actualizado de los flujos de n8n para evitar perder contexto entre sesiones.

## Estado General (04-03-2026)
- **Instancia**: Local via Docker (`127.0.0.1:5688`)
- **API**: Habilitada y funcionando para control vía MCP.

## Flujos Críticos

### 📧 Envío de CVs (Pilar 1)
- **ID**: `qiN136ZrDDS8Pg2L`
- **Nombre**: `Envío Automático de CV a Colegios`
- **Estado**: ACTIVO (Trigger Webhook)
- **Descripción**: Recibe datos de contacto y envía CV adjunto desde una cuenta Gmail.
- **Configuración Actual**: Vinculado al sistema de script nativo `send_cvs.py` que maneja delays anti-spam y rotación de cuentas.

### 🛠️ Herramientas MCP integradas
- **Memory Search/Upsert/Apply/Feedback**: Activos para el Búnker de Memoria.
- **Tavily Advanced Search**: Activo para investigación.
- **Groq/Groq Fast Processor**: Activos para razonamiento rápido.
- **Research Colmena / Consultar Colmena**: Activos para inteligencia colectiva.

## Observaciones de la Sesión
- Se identificó un límite diario en la cuenta `profesordiegofilosofia@gmail.com`.
- Se re-arquitectó el flujo para usar `profedefilodiego@gmail.com` como cuenta confiable.
- n8n requiere autenticación vía web (`signin` page), pero es accesible totalmente vía API-MCP.
