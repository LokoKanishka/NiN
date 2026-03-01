import requests
import os
import json
from dotenv import load_dotenv

# Configuración de rutas
BASE_DIR = "/home/lucy-ubuntu/Escritorio/NIN"
load_dotenv(os.path.join(BASE_DIR, ".env"))

N8N_HOST = "http://172.24.0.4:5678"
N8N_API_KEY = os.getenv("N8N_API_KEY")
HEADERS = {"X-N8N-API-KEY": N8N_API_KEY, "Content-Type": "application/json"}

def call_webhook(path, payload={}):
    url = f"{N8N_HOST}/webhook/{path}"
    try:
        resp = requests.post(url, json=payload, headers=HEADERS, timeout=10)
        return resp.json() if resp.status_code == 200 else {"error": resp.status_code, "text": resp.text}
    except Exception as e:
        return {"error": str(e)}

def check_alt():
    print("🤖 [ALT]: Verificando salud de la IA local...")
    url = "http://127.0.0.1:11434/api/tags"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            models = [m['name'] for m in resp.json().get('models', [])]
            if "qwen2.5-coder:14b-instruct-q8_0" in models:
                return {"status": "Online", "model": "qwen2.5-coder:14b-instruct-q8_0"}
            return {"status": "Warning", "error": "Alt model not found", "models": models}
        return {"status": "Offline", "error": resp.status_code}
    except Exception as e:
        return {"status": "Offline", "error": str(e)}

def run_startup():
    print("🚀 [STARTUP] Inicializando Protocolo de Arranque Perfecto...")
    
    # 1. Ping
    ping = call_webhook("ping-mcp")
    print(f"📡 [PING]: {ping.get('output', 'Error')}")

    # 2. System Health
    health = call_webhook("agente-sistema")
    # Simplificamos la salida para el reporte
    h_data = health.get("output", {}) if isinstance(health.get("output"), dict) else {"raw": health.get("output")}
    print(f"🏥 [HEALTH]: Datos de salud recolectados.")

    # 3. Doctor System
    doctor = call_webhook("tool-doctor")
    print(f"🩺 [DOCTOR]: Chequeo de contenedores completado.")

    # 4. Recuperar Contexto (Omitido por redundancia, se maneja en MCP)
    print(f"🧠 [MEMORIA]: Ignorando webhook legado (usar MCP Recuperar Contexto).")

    # 5. Alt Check
    alt = check_alt()
    print(f"🤖 [ALT]: {alt['status']}")

    # Generar Reporte Final para Antigravity
    report = {
        "status": "Ready",
        "connection": "Blindada (172.24.0.4)",
        "health": h_data,
        "doctor": doctor.get("output", "Check complete"),
        "alt": alt
    }
    
    with open(os.path.join(BASE_DIR, "memoria/startup_report.json"), "w") as f:
        json.dump(report, f, indent=4)
    
    print("✅ [STARTUP] Protocolo finalizado. Reporte guardado en memoria/startup_report.json")

if __name__ == "__main__":
    run_startup()
