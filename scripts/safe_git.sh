#!/bin/bash
# Escudo Anti-Hang para Guardados en Git (Repositorio NiN)
# Previene congelamientos por TTY interactivos (nano/vim/ssh prompts)

PROJECT_DIR="/home/lucy-ubuntu/Escritorio/NIN"
cd "$PROJECT_DIR" || exit 1

# 1. Escudo de Prompt: Si git pide contraseña o usuario, falla inmediatamente en lugar de colgarse.
export GIT_TERMINAL_PROMPT=0

# Argumento opcional para el mensaje
COMMIT_MSG=${1:-"Respaldo automático del agente (Anti-Hang Protocol)"}

echo "🛡️ [SafeGit] Iniciando secuencia de guardado seguro..."

# 2. Agregar cambios (Solo los ya rastreados para evitar fugas de secretos accidentales)
# El usuario o el agente deben hacer 'git add' de archivos nuevos antes de llamar a este script.
git add -u

# 3. Commit con timeout de 10s (evita hooks locales largos)
timeout 10s git commit -m "$COMMIT_MSG"
COMMIT_STATUS=$?

if [ $COMMIT_STATUS -eq 124 ]; then
    echo "⚠️ [SafeGit] El commit excedió el timeout de 10s."
    exit 1
elif [ $COMMIT_STATUS -ne 0 ] && [ $COMMIT_STATUS -ne 1 ]; then
    echo "ℹ️ [SafeGit] Commit retornó estado $COMMIT_STATUS (Posiblemente no hay cambios)."
fi

# 4. Push con timeout de 30s (evita cuelgues de red o SSH trabado)
echo "☁️ [SafeGit] Empujando a remoto..."
timeout 30s git push
PUSH_STATUS=$?

if [ $PUSH_STATUS -eq 124 ]; then
    echo "❌ [SafeGit] CRITICO: El push excedió el timeout de 30s (Problema de red o credenciales)."
    exit 1
elif [ $PUSH_STATUS -eq 0 ]; then
    echo "✅ [SafeGit] Guardado completado con éxito."
else
    echo "❌ [SafeGit] Fallo en el push (Código: $PUSH_STATUS). Revisa credenciales o upstream."
    exit 1
fi
