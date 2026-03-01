import requests
import os
from dotenv import load_dotenv

BASE_DIR = "/home/lucy-ubuntu/Escritorio/NIN"
load_dotenv(os.path.join(BASE_DIR, ".env"))

N8N_API_URL = "http://172.24.0.4:5678/api/v1"
N8N_API_KEY = os.getenv("N8N_API_KEY")
HEADERS = {"X-N8N-API-KEY": N8N_API_KEY}

def cleanup_workflows():
    print("🧹 Iniciando limpieza de n8n...")
    
    # 1. Obtener todos los workflows
    try:
        resp = requests.get(f"{N8N_API_URL}/workflows", headers=HEADERS)
        if resp.status_code != 200:
            print(f"❌ Error al obtener workflows: {resp.status_code}")
            return
        
        workflows = resp.json().get("data", [])
        print(f"🔍 Encontrados {len(workflows)} workflows.")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    # 2. Identificar duplicados e inactivos
    # Agrupamos por nombre
    by_name = {}
    for wf in workflows:
        name = wf["name"]
        if name not in by_name:
            by_name[name] = []
        by_name[name].append(wf)

    to_delete = []
    
    for name, group in by_name.items():
        if len(group) > 1:
            # Hay duplicados. Mantener el Activo, borrar el resto.
            # Si hay varios activos (raro pero posible), mantenemos el más nuevo.
            actives = [w for w in group if w.get("active")]
            inactives = [w for w in group if not w.get("active")]
            
            if actives:
                # Mantener el activo (o el primero de los activos si hay varios)
                print(f"⚠️ Duplicados en '{name}': manteniendo activo ({actives[0]['id']}).")
                to_delete.extend(inactives)
            else:
                # Si todos están inactivos, borrar todos menos el más nuevo
                group.sort(key=lambda x: x.get("updatedAt", ""), reverse=True)
                print(f"⚠️ Duplicados en '{name}' (todos inactivos): manteniendo más reciente ({group[0]['id']}).")
                to_delete.extend(group[1:])
        elif group[0].get("name").startswith("Copia de") or not group[0].get("active"):
            # Opcional: Borrar inactivos solitarios que parezcan basura
            # Solo si el nombre sugiere que es basura o si es una herramienta que ya probamos y falló
            basura_keywords = ["Copia de", "prueba", "Test", "vacío", "Untitled"]
            if any(k in group[0]["name"] for k in basura_keywords):
                print(f"🗑️ Marcado como basura: '{group[0]['name']}' ({group[0]['id']})")
                to_delete.append(group[0])

    # 3. Ejecutar borrado
    for wf in to_delete:
        id = wf["id"]
        name = wf["name"]
        print(f"🔥 Borrando '{name}' ({id})...")
        try:
            del_resp = requests.delete(f"{N8N_API_URL}/workflows/{id}", headers=HEADERS)
            if del_resp.status_code == 200:
                print(f"✅ Borrado '{name}' exitoso.")
            else:
                print(f"❌ Falló borrado de '{name}': {del_resp.status_code}")
        except Exception as e:
            print(f"❌ Error borrando {id}: {e}")

    print(f"✨ Limpieza terminada. {len(to_delete)} workflows eliminados.")

if __name__ == "__main__":
    cleanup_workflows()
