import asyncio
import os
import json
import sys

# Añadir el path para importar nin_demon
sys.path.append("/home/lucy-ubuntu/Escritorio/NIN/scripts")
from nin_demon import ask_alt

async def test_alt_n8n():
    prompt = "Hola Alt. Sos el asistente del proyecto NiN. Necesito verificar que todo funcione. Generá una misión en formato JSON con 'id': 'test_integracion_alt' y una lista de 'tasks'. La primera task debe usar 'mcp_n8n-control_ping' y la segunda 'mcp_n8n-control_system_health'. Devolvé ÚNICAMENTE el código JSON puro, sin explicaciones ni markdown."
    
    print("\n🛰️  Enviando consulta a Alt (Qwen 14B)...")
    response = await ask_alt(prompt)
    
    print("-" * 30)
    print(f"🤖 Alt respondió:\n{response}")
    print("-" * 30)
    
    try:
        # Limpiar si hay markdown
        raw_json = response.strip()
        if "```json" in raw_json:
            raw_json = raw_json.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_json:
            raw_json = raw_json.split("```")[1].split("```")[0].strip()
        
        mission_data = json.loads(raw_json)
        mission_path = "/home/lucy-ubuntu/Escritorio/NIN/demon/misiones/test_integracion_alt.json"
        
        # Asegurar directorios
        os.makedirs(os.path.dirname(mission_path), exist_ok=True)
        
        with open(mission_path, "w") as f:
            json.dump(mission_data, f, indent=4)
        
        print(f"✅ Misión autogenerada por Alt guardada en: {mission_path}")
        print("\nPróximo paso: El NiN-Demon procesará este archivo usando n8n.")
        
    except Exception as e:
        print(f"❌ Error al parsear la respuesta de Alt: {e}")
        print(f"Contenido crudo: {response}")

if __name__ == "__main__":
    asyncio.run(test_alt_n8n())
