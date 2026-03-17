#!/bin/bash
# --- BitNin Operational Backup ---
# Exporta el estado operativo crítico para continuidad.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="bitnin_ops_backup_$TIMESTAMP.tar.gz"

OBS_HISTORY="$PROJECT_ROOT/verticals/bitnin/runtime/observability/history"

echo "--- 📦 Creando Respaldo Operativo ---"

if [ ! -d "$OBS_HISTORY" ]; then
    echo "[ERROR] No se encontró el directorio de historia operativa."
    exit 1
fi

# Create a temporary directory for grouping
TMP_DIR=$(mktemp -d)
mkdir -p "$TMP_DIR/history"

# Essential files for continuity
FILES=(
    "hitl_state.json"
    "operational_state.json"
    "hitl_briefing.md"
    "operator_journal.md"
    "health_snapshot.json"
)

echo "Empacando archivos de SSOT y estados..."
for file in "${FILES[@]}"; do
    if [ -f "$OBS_HISTORY/$file" ]; then
        cp "$OBS_HISTORY/$file" "$TMP_DIR/history/"
    fi
done

# Daily Bundles (last 7 days to keep it light)
if [ -d "$OBS_HISTORY/daily_bundles" ]; then
    echo "Agregando bundles diarios recientes..."
    cp -r "$OBS_HISTORY/daily_bundles" "$TMP_DIR/history/"
fi

# Final compression
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/$BACKUP_NAME" -C "$TMP_DIR" .

echo "[OK] Respaldo generado con éxito: "
echo "     backups/$BACKUP_NAME"

# Cleanup
rm -rf "$TMP_DIR"
echo "-----------------------------------"
