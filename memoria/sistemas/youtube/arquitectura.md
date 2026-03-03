# Sistema de Integración YouTube (NIN)

Este documento describe la arquitectura y el funcionamiento del subsistema de búsqueda y reproducción automática de YouTube.

## Componentes

1. **`nin_megademon.py` (Cliente Telegram)**
   - Recibe la petición del usuario.
   - Genera una misión `create_mission` con el `workflow_id: b0QtaKcqH5I0WLYk`.
   - Espera confirmación humana (HITL) para ejecutar.

2. **`n8n_mcp_server.py` (Bridge MCP - Puerto 8001)**
   - Intercepta la llamada a `execute_n8n_workflow`.
   - Si el ID es `b0QtaKcqH5I0WLYk`, ejecuta el webhook de n8n.
   - **Lógica Inteligente**: Una vez recibidos los 10 resultados de SearXNG (vía n8n), aplica un algoritmo de *Scoring* por palabras clave para elegir el video más relevante, no solo el primero.
   - Llama al Launcher local para abrir el video.

3. **`youtube_launcher_service.py` (Host Opener - Puerto 9999)**
   - Servicio liviano en el Host que escucha peticiones HTTP GET en `/play?url=...`.
   - Lanza `firefox` con el perfil `Lucy Chat` (con uBlock Origin).
   - Usa `xdotool` para presionar la tecla `k` después de 5 segundos, sorteando las restricciones de AutoPlay.

## Flujo de Datos

1. **Búsqueda**: `n8n` (Node: SearXNG) -> Devuelve JSON con títulos y URLs.
2. **Ranking**: `n8n_mcp_server` -> Compara palabras de la query vs títulos de resultados (ignora stopwords como "el", "la").
3. **Ejecución**: Se envía la URL ganadora al puerto `9999`.
4. **Visualización**: Se abre Firefox en la pantalla principal del host.

## Comandos Útiles

Recargar todo el sistema de YouTube:
```bash
# Matar procesos viejos
kill -9 $(pgrep -f n8n_mcp_server) 2>/dev/null
kill -9 $(pgrep -f youtube_launcher_service) 2>/dev/null

# Levantar Launcher (Host)
nohup python3 scripts/youtube_launcher_service.py > logs/youtube_launcher.log 2>&1 &

# Levantar Servidor MCP (SSE)
nohup python3 scripts/n8n_mcp_server.py --transport sse > logs/n8n_mcp_server_sse.log 2>&1 &
```

## Notas de Desarrollo
- El puerto SSE fue movido de `8000` a `8001` para evitar colisiones con procesos internos de n8n o fantasmas del sistema.
- El perfil de Firefox `Lucy Chat` es crítico para que uBlock salte los anuncios.
