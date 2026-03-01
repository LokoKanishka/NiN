import json
import os
import glob

# Configuración
DOCS_DIR = "/home/lucy-ubuntu/Escritorio/NIN/docs"
OUTPUT_FILE = "/home/lucy-ubuntu/Escritorio/NIN/entrenamiento/dataset/colmena_core_v1.jsonl"

def prepare_dataset():
    data_pairs = []
    
    # Buscar todos los JSON de workflows
    json_files = glob.glob(os.path.join(DOCS_DIR, "*.json"))
    
    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                workflow_data = json.load(f)
            
            name = workflow_data.get("name", os.path.basename(file_path))
            
            # Limpiar el JSON para el dataset (quitar IDs irrelevantes si es necesario, pero mantener estructura)
            # Para el entrenamiento, queremos que aprenda la estructura de nodos y conexiones.
            minified_json = json.dumps(workflow_data, separators=(',', ':'))
            
            # Crear tripletas Instruct-Response
            instruction = f"Genera el código JSON para el workflow de n8n '{name}' siguiendo el protocolo NiN."
            context = "Eres un asistente experto en n8n y en el protocolo soberano NiN. Los workflows deben usar el bridge de red local 172.24.0.4 cuando sea necesario."
            
            data_pairs.append({
                "instruction": instruction,
                "context": context,
                "response": minified_json
            })
            
            # Variaciones para robustez
            data_pairs.append({
                "instruction": f"¿Cómo implemento la herramienta '{name}' en mi colmena NiN?",
                "context": context,
                "response": f"Para implementar '{name}', utiliza el siguiente JSON en n8n:\n{minified_json}"
            })
            
        except Exception as e:
            print(f"Error procesando {file_path}: {e}")

    # Guardar como JSONL
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for entry in data_pairs:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
    print(f"✅ Dataset generado con {len(data_pairs)} ejemplos en {OUTPUT_FILE}")

if __name__ == "__main__":
    prepare_dataset()
