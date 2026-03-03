#!/bin/bash

# Script de reinicio rápido para el Subsistema de YouTube (NIN)
# Propósito: Asegurar que el Launcher del Host y el Servidor MCP SSE estén sincronizados.

echo "--- [REINICIANDO SUBSISTEMA YOUTUBE] ---"

# 1. Matar procesos anteriores
echo "[-] Limpiando procesos antiguos..."
kill -9 $(pgrep -f n8n_mcp_server) 2>/dev/null
kill -9 $(pgrep -f youtube_launcher_service) 2>/dev/null
sleep 1

# 2. Iniciar Launcher (Puerto 9999) - Es el que abre Firefox
echo "[+] Iniciando Youtube Launcher Service (Host)..."
nohup python3 /home/lucy-ubuntu/Escritorio/NIN/scripts/youtube_launcher_service.py > /home/lucy-ubuntu/Escritorio/NIN/logs/youtube_launcher.log 2>&1 &
sleep 2

# 3. Iniciar Servidor MCP SSE (Puerto 8001) - Es el puente con n8n
echo "[+] Iniciando n8n MCP Server (SSE)..."
nohup python3 /home/lucy-ubuntu/Escritorio/NIN/scripts/n8n_mcp_server.py --transport sse > /home/lucy-ubuntu/Escritorio/NIN/logs/n8n_mcp_server_sse.log 2>&1 &
sleep 2

# 4. Verificar salud
echo "--- [ESTADO FINAL] ---"
pgrep -f youtube_launcher_service && echo "[OK] Launcher Activo" || echo "[ERR] Launcher Falló"
pgrep -f n8n_mcp_server && echo "[OK] MCP Server Activo" || echo "[ERR] MCP Server Falló"

echo "Todo listo. Podés probar desde Telegram ahora."
