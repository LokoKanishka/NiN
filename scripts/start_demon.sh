#!/bin/bash
# Lanzador Universal Anti-Hang para Demonios IA (NiN)
# Evita que el agente quede anclado a stdout/stderr de procesos infinitos

if [ -z "$1" ]; then
    echo "❌ Uso: ./start_demon.sh <nombre_del_script.py>"
    echo "Ejemplo: ./start_demon.sh nin_megademon.py"
    exit 1
fi

SCRIPT_NAME=$1
PROJECT_DIR="/home/lucy-ubuntu/Escritorio/NIN"
LOG_FILE="$PROJECT_DIR/runtime/logs/${SCRIPT_NAME%.*}.log"

echo "🛑 [Anti-Hang] Escaneando instancias previas de $SCRIPT_NAME..."
pkill -f "$SCRIPT_NAME" || true
sleep 1

echo "🚀 [Anti-Hang] Lanzando $SCRIPT_NAME en aislamiento total..."
export PYTHONUNBUFFERED=1

# El escudo maestro: nohup + stderr a stdout + cierre de stdin + disown
nohup "$PROJECT_DIR/.venv/bin/python3" "$PROJECT_DIR/scripts/$SCRIPT_NAME" > "$LOG_FILE" 2>&1 < /dev/null &
disown

echo "✅ OK: $SCRIPT_NAME lanzado. Terminal liberada."
echo "📄 Logs encolados en: $LOG_FILE"
