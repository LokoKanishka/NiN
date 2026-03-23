#!/bin/bash
# n8n_ctl.sh - Herramienta de control CLI-first para workflows de n8n

CONTAINER_NAME="N8N-NiN-uso-exclusivo-del-proyecto-nin"

show_help() {
    echo "Uso: $0 {list|export|import}"
    echo "Comandos:"
    echo "  list                      - Lista todos los workflows activos (ID y Nombre)"
    echo "  export <id> [output_file] - Exporta un workflow por ID a un archivo JSON local"
    echo "  import <input_file>       - Importa o actualiza un workflow desde un archivo JSON"
}

if [ -z "$1" ]; then
    show_help
    exit 1
fi

case "$1" in
    list)
        echo "Consultando workflows en el contenedor $CONTAINER_NAME..."
        docker exec -t "$CONTAINER_NAME" n8n list:workflow
        ;;
    export)
        if [ -z "$2" ]; then
            echo "Error: Se requiere el ID del workflow."
            echo "Uso: $0 export <id> [output_file]"
            exit 1
        fi
        WORKFLOW_ID="$2"
        # Si no se pasa un archivo destino, usamos uno por defecto con el ID
        OUTPUT_FILE="${3:-"./workflow_${WORKFLOW_ID}.json"}"
        
        echo "Exportando workflow $WORKFLOW_ID desde n8n..."
        docker exec -t "$CONTAINER_NAME" n8n export:workflow --id="$WORKFLOW_ID" --output=/tmp/n8n_export_temp.json
        docker cp "$CONTAINER_NAME":/tmp/n8n_export_temp.json "$OUTPUT_FILE"
        echo "✅ Workflow exportado exitosamente a: $OUTPUT_FILE"
        ;;
    import)
        if [ -z "$2" ]; then
            echo "Error: Se requiere la ruta al archivo JSON."
            echo "Uso: $0 import <input_file>"
            exit 1
        fi
        INPUT_FILE="$2"
        if [ ! -f "$INPUT_FILE" ]; then
            echo "Error: El archivo $INPUT_FILE no existe."
            exit 1
        fi
        
        echo "Importando workflow desde $INPUT_FILE..."
        docker cp "$INPUT_FILE" "$CONTAINER_NAME":/tmp/n8n_import_temp.json
        docker exec -t "$CONTAINER_NAME" n8n import:workflow --input=/tmp/n8n_import_temp.json
        echo "✅ Importación finalizada."
        ;;
    *)
        show_help
        exit 1
        ;;
esac
