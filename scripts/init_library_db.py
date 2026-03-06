import sqlite3
import os
import sys

DB_PATH = "/home/lucy-ubuntu/Escritorio/NIN/library/catalog.db"

def init_db():
    print(f"📦 [Library] Inicializando catálogo en {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabla de Patrones
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patterns (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        source TEXT,
        category TEXT,
        nodes_list TEXT,
        min_n8n_version TEXT,
        creds_required INTEGER DEFAULT 0,
        status TEXT DEFAULT 'raw',
        file_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Tabla de Metadatos Extendidos (Relación 1:1 con sidecars JSON)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pattern_metadata (
        pattern_id TEXT PRIMARY KEY,
        description TEXT,
        ai_score INTEGER,
        tags TEXT,
        FOREIGN KEY (pattern_id) REFERENCES patterns(id)
    )
    ''')
    
    # Tabla de Validaciones
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS validations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pattern_id TEXT,
        phase TEXT,
        status TEXT,
        report TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (pattern_id) REFERENCES patterns(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ [Library] Catálogo inicializado con éxito.")

if __name__ == "__main__":
    init_db()
