#!/bin/bash
# --- BitNin Operational Bootstrap ---
# This script prepares the runtime environment and entrypoints.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "--- 🚀 BitNin Bootstrap ---"

# 1. Validation
echo "[1/4] Validando entorno..."
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 no encontrado."
    exit 1
fi

# 2. Runtime Directories
echo "[2/4] Configurando estructura de runtime..."
DIRS=(
    "verticals/bitnin/runtime/observability/history/daily_bundles"
    "verticals/bitnin/runtime/observability/batches"
    "verticals/bitnin/runtime/observability/scorecards"
    "verticals/bitnin/runtime/shadow"
    "backups"
    "bin"
    "scripts"
)

for dir in "${DIRS[@]}"; do
    mkdir -p "$dir"
done

# 3. Permissions & Entrypoints
echo "[3/4] Asegurando permisos de ejecución..."
chmod +x bitnin_ctl.py
if [ -f "bin/bitnin-ctl" ]; then
    chmod +x bin/bitnin-ctl
fi

# Ensure scripts are executable
find scripts/ -name "*.sh" -exec chmod +x {} +

# 4. Success Check
echo "[4/4] Finalizando..."
echo "BitNin Bootstrap completado con éxito."
echo "Entrypoint sugerido: ./bin/bitnin-ctl"
echo "---------------------------"
