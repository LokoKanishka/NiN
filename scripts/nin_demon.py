import asyncio
import json
import os
import sys
import aiohttp
import shutil
from datetime import datetime
from typing import List, Dict, Any
from mcp import ClientSession
from mcp.client.sse import sse_client

# === CONFIGURACIÓN ===
SSE_URL = "http://127.0.0.1:8000/sse"
BASE_DIR = "/home/lucy-ubuntu/Escritorio/NIN/demon"
MISSIONS_DIR = f"{BASE_DIR}/misiones"
DONE_DIR = f"{BASE_DIR}/misiones/completadas"
FAIL_DIR = f"{BASE_DIR}/misiones/fallidas"
CHAT_DIR = f"{BASE_DIR}/voz"
CHAT_LOG = f"{CHAT_DIR}/diego_mensajes.log"

# Credenciales Telegram (Detectadas)
TG_TOKEN = "8235094378:AAG-EKXPVUjmXGTZQigDIxyciWqlNMsJ8oA"
DIEGO_ID = 5154360597

async def execute_tool_safe(session: ClientSession, tool_name: str, arguments: Dict[str, Any]):
    try:
        print(f"  [NiN-Demon] -> {tool_name} {arguments}")
        result = await session.call_tool(tool_name, arguments)
        text = result.content[0].text if result.content else "No content"
        return {"tool": tool_name, "status": "success", "result": text}
    except Exception as e:
        print(f"  [NiN-Demon] Error en {tool_name}: {e}")
        return {"tool": tool_name, "status": "error", "error": str(e)}

async def process_mission(mission_file: str):
    basename = os.path.basename(mission_file)
    try:
        with open(mission_file, 'r') as f:
            data = json.load(f)
        
        tasks = data.get("tasks", [])
        mission_id = data.get("id", basename)
        print(f"🚀 [NiN-Demon] Misión detectada: {mission_id}")

        async with sse_client(SSE_URL) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                results = []
                for t in tasks:
                    res = await execute_tool_safe(session, t["tool"], t.get("args", {}))
                    results.append(res)
                
                report_name = f"report_{mission_id}_{datetime.now().strftime('%H%M%S')}.json"
                report_path = os.path.join(DONE_DIR, report_name)
                with open(report_path, 'w') as f:
                    json.dump({"id": mission_id, "timestamp": str(datetime.now()), "results": results}, f, indent=4)
                
                print(f"✅ Misión completada: {report_name}")
                shutil.move(mission_file, os.path.join(DONE_DIR, basename))
    except Exception as e:
        print(f"❌ Fallo en misión {basename}: {e}")
        shutil.move(mission_file, os.path.join(FAIL_DIR, basename))

async def upsert_to_graph(subject: str, predicate: str, obj: str):
    """Guarda una relación en el grafo de Qdrant."""
    url = "http://127.0.0.1:6335/collections/nin_knowledge_graph/points"
    point_id = hash(f"{subject}-{predicate}-{obj}-{datetime.now()}") % (2**63 - 1)
    payload = {
        "points": [{
            "id": point_id,
            "vector": [0.0] * 1024, # Vector dummy por ahora
            "payload": {
                "subject": subject,
                "predicate": predicate,
                "object": obj,
                "text": f"{subject} {predicate} {obj}",
                "timestamp": str(datetime.now())
            }
        }]
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=payload) as resp:
                if resp.status == 200:
                    print(f"🧠 [Grafo] Relación guardada: {subject} -> {predicate} -> {obj}")
                else:
                    text = await resp.text()
                    print(f"⚠️ [Grafo] Error al guardar: {text}")
    except Exception as e:
        print(f"⚠️ [Grafo] Excepción: {e}")

async def telegram_ears_loop():
    print(f"👂 [NiN-Demon] Orejas activas. Escuchando a Diego en Telegram...")
    last_update_id = 0
    
    # Intentar recuperar el último update_id para no repetir
    if os.path.exists(f"{CHAT_DIR}/last_update.id"):
        with open(f"{CHAT_DIR}/last_update.id", "r") as f:
            try: last_update_id = int(f.read().strip())
            except: pass

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates"
                params = {"offset": last_update_id + 1, "timeout": 30}
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for update in data.get("result", []):
                            last_update_id = update["update_id"]
                            with open(f"{CHAT_DIR}/last_update.id", "w") as f: f.write(str(last_update_id))
                            
                            msg = update.get("message", {})
                            chat_id = msg.get("chat", {}).get("id")
                            if chat_id == DIEGO_ID:
                                text = msg.get("text", "")
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                log_entry = f"[{timestamp}] DIEGO: {text}\n"
                                with open(CHAT_LOG, "a") as f: f.write(log_entry)
                                print(f"📩 [NiN-Demon] Nuevo mensaje de Diego: {text}")
                                
                                # Guardar en el grafo
                                await upsert_to_graph("Diego", "dijo_en_telegram", text)
        except Exception as e:
            print(f"⚠️ Error en Orejas: {e}")
        
        await asyncio.sleep(2)

async def mission_watcher_loop():
    print(f"📂 [NiN-Demon] Watcher de misiones activo en {MISSIONS_DIR}")
    while True:
        try:
            target_files = [os.path.join(MISSIONS_DIR, f) for f in os.listdir(MISSIONS_DIR) 
                           if f.endswith(".json") and os.path.isfile(os.path.join(MISSIONS_DIR, f))]
            for f in target_files:
                await process_mission(f)
        except Exception as e:
            print(f"⚠️ Error en Watcher: {e}")
        await asyncio.sleep(2)

async def main():
    # Asegurar directorios
    for d in [DONE_DIR, FAIL_DIR, MISSIONS_DIR, CHAT_DIR]: 
        os.makedirs(d, exist_ok=True)
    
    print(f"👹 NiN-Demon 1.3 - Motores encendidos.")
    
    # Lanzar ambos loops en paralelo
    await asyncio.gather(
        mission_watcher_loop(),
        telegram_ears_loop()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown.")
    except Exception as e:
        print(f"FATAL: {e}")
