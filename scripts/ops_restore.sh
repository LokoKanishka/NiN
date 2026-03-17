#!/bin/bash
# --- BitNin Operational Restore ---
# Restaura el estado operativo desde un respaldo.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_FILE=$1

OBS_HISTORY="$PROJECT_ROOT/verticals/bitnin/runtime/observability/history"

function usage() {
    echo "Uso: $0 <path_al_backup.tar.gz>"
    exit 1
}

if [ -z "$BACKUP_FILE" ]; then usage; fi
if [ ! -f "$BACKUP_FILE" ]; then
    echo "[ERROR] El archivo de respaldo no existe: $BACKUP_FILE"
    exit 1
fi

echo "--- ♻️ Restaurando Respaldo Operativo ---"
echo "⚠️ ADVERTENCIA: Esto sobrescribirá el estado actual en $OBS_HISTORY"
read -p "¿Desea continuar? (s/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "[ABORTADO] Operación cancelada por el usuario."
    exit 0
fi

# Create a temporary directory for extraction
TMP_DIR=$(mktemp -d)

echo "Extrayendo respaldo..."
tar -xzf "$BACKUP_FILE" -C "$TMP_DIR"

# Restore files
echo "Restaurando archivos e historia..."
mkdir -p "$OBS_HISTORY"
cp -r "$TMP_DIR/history/"* "$OBS_HISTORY/"

echo "[OK] Restauración completada con éxito."
echo "Se recomienda ejecutar './bin/bitnin-ctl doctor' para validar."

# Cleanup
rm -rf "$TMP_DIR"
echo "---------------------------------------"
