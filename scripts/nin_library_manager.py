import json
import os
import sqlite3
import shutil
import uuid
from datetime import datetime

# Configuración
BASE_DIR = "/home/lucy-ubuntu/Escritorio/NIN"
LIB_DIR = f"{BASE_DIR}/library"
STORAGE_DIR = f"{BASE_DIR}/runtime/library_storage"
DB_PATH = f"{LIB_DIR}/catalog.db"

class LibraryManager:
    def __init__(self):
        self._ensure_paths()
    
    def _ensure_paths(self):
        for d in ["raw", "curated", "validated", "rejected", "reports"]:
            os.makedirs(f"{STORAGE_DIR}/{d}", exist_ok=True)
            
    def _db_conn(self):
        return sqlite3.connect(DB_PATH)

    def register_manual(self, file_path, name=None, category="uncategorized"):
        """Registra un archivo JSON local en la biblioteca (fase raw)."""
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"Archivo no encontrado: {file_path}"}
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            return {"status": "error", "message": f"Error leyendo JSON: {e}"}

        # Validaciones estáticas mínimas
        is_workflow = isinstance(data, dict) and ("nodes" in data or "id" in data)
        if not is_workflow:
            return {"status": "error", "message": "El archivo no parece ser un workflow de n8n válido."}

        p_id = str(uuid.uuid4())[:8]
        p_name = name or os.path.basename(file_path).replace(".json", "")
        
        # Mover archivo a storage/raw
        target_path = f"{STORAGE_DIR}/raw/{p_id}_{os.path.basename(file_path)}"
        shutil.copy(file_path, target_path)

        # Extraer nodos (básico)
        nodes = data.get("nodes", [])
        nodes_str = ",".join(list(set([n.get("type", "unknown") for n in nodes])))

        # Insertar en DB
        conn = self._db_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO patterns (id, name, category, nodes_list, status, file_path)
            VALUES (?, ?, ?, ?, 'raw', ?)
        ''', (p_id, p_name, category, nodes_str, target_path))
        conn.commit()
        conn.close()

        print(f"📥 [Library] Patrón '{p_name}' registrado en RAW con ID: {p_id}")
        return {"status": "success", "id": p_id, "path": target_path}

    def list_patterns(self):
        conn = self._db_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, category, status FROM patterns')
        rows = cursor.fetchall()
        conn.close()
        return rows

    def static_validate(self, pattern_id):
        """Ejecuta validaciones estáticas básicas y mueve a curated si pasa."""
        conn = self._db_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT name, status, file_path FROM patterns WHERE id = ?', (pattern_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return "Patrón no encontrado."
        
        name, status, path = row
        print(f"🛡️ [Library] Validando estáticamente '{name}' (ID: {pattern_id})...")
        
        with open(path, 'r') as f:
            data = json.load(f)
            
        # 1. Sanitización de credenciales (básica)
        has_creds = False
        raw_text = json.dumps(data)
        if "credentials" in raw_text or "apiKey" in raw_text:
            has_creds = True
            
        # 2. Detección de nodos sensibles
        sensitive_nodes = ["n8n-nodes-base.executeCommand", "n8n-nodes-base.ssh"]
        found_sensitive = [n.get("type") for n in data.get("nodes", []) if n.get("type") in sensitive_nodes]
        
        report = {
            "has_credentials_placeholder": has_creds,
            "sensitive_nodes": found_sensitive,
            "valid_json": True
        }
        
        new_status = "curated"
        new_path = path.replace("/raw/", "/curated/")
        shutil.move(path, new_path)
        
        cursor.execute('''
            UPDATE patterns SET status = ?, file_path = ?, creds_required = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_status, new_path, 1 if has_creds else 0, pattern_id))
        
        cursor.execute('''
            INSERT INTO validations (pattern_id, phase, status, report)
            VALUES (?, 'static', 'passed', ?)
        ''', (pattern_id, json.dumps(report)))
        
        conn.commit()
        conn.close()
        print(f"✅ [Library] '{name}' promovido a CURATED.")
        return report

if __name__ == "__main__":
    lm = LibraryManager()
    # Si se corre directo, podemos probar
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("🛠️ Corriendo prueba de la librería...")
