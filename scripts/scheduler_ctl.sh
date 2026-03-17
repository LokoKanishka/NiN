#!/bin/bash
# --- BitNin Scheduler Controller ---
# Automatiza la gestión de systemd --user para BitNin.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR="$HOME/.config/systemd/user"
UNIT_SRC="$PROJECT_ROOT/verticals/bitnin/services/bitnin_observability/systemd"

COMMAND=$1

function usage() {
    echo "Uso: $0 {install|uninstall|status|restart|logs}"
    exit 1
}

if [ -z "$COMMAND" ]; then usage; fi

case "$COMMAND" in
    install)
        echo "--- Instalando Scheduler (systemd --user) ---"
        mkdir -p "$UNIT_DIR"
        cp "$UNIT_SRC"/bitnin-shadow.* "$UNIT_DIR"/
        systemctl --user daemon-reload
        systemctl --user enable --now bitnin-shadow.timer
        echo "[OK] Scheduler instalado y activo."
        ;;
    uninstall)
        echo "--- Desinstalando Scheduler ---"
        systemctl --user disable --now bitnin-shadow.timer || true
        rm -f "$UNIT_DIR"/bitnin-shadow.*
        systemctl --user daemon-reload
        echo "[OK] Scheduler removido."
        ;;
    status)
        echo "--- Estado del Scheduler ---"
        systemctl --user status bitnin-shadow.timer
        ;;
    restart)
        echo "--- Reiniciando Servicio ---"
        systemctl --user restart bitnin-shadow.service
        ;;
    logs)
        echo "--- Logs del Servicio ---"
        journalctl --user -u bitnin-shadow.service -f
        ;;
    *)
        usage
        ;;
esac
