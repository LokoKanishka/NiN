#!/bin/bash
export PYTHONUNBUFFERED=1

echo "Deteniendo instancias previas de NiN..."
pkill -f "nin_demon.py" || true
pkill -f "nin_megademon.py" || true
sleep 1

echo "Lanzando Megademon-MCP de forma segura en el fondo..."
nohup python3 /home/lucy-ubuntu/Escritorio/NIN/scripts/nin_megademon.py > /home/lucy-ubuntu/Escritorio/NIN/logs/nin_megademon_output.log 2>&1 < /dev/null &
disown

echo "OK: Proceso lanzado y terminal liberada correctamente."
