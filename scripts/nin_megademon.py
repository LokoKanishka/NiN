import asyncio
import json
import os
import sys
import aiohttp
import shutil
from datetime import datetime
from typing import List, Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

# === CONFIGURACIÓN ===
SSE_URL = "http://127.0.0.1:8000/sse"
BASE_DIR = "/home/lucy-ubuntu/Escritorio/NIN/demon"
MISSIONS_DIR = f"{BASE_DIR}/misiones"
DONE_DIR = f"{BASE_DIR}/misiones/completadas"
FAIL_DIR = f"{BASE_DIR}/misiones/fallidas"
CHAT_DIR = f"{BASE_DIR}/voz"
CHAT_LOG = f"{CHAT_DIR}/diego_mensajes.log"

OLLAMA_MODEL = "qwen2.5-coder:14b-instruct-q8_0"
OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"

TG_TOKEN = "8235094378:AAG-EKXPVUjmXGTZQigDIxyciWqlNMsJ8oA"
DIEGO_ID = 5154360597

async def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": DIEGO_ID, "text": text}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    print(f"🗨️ [NiN-Demon] Mensaje enviado: {text[:50]}...")
                else:
                    print(f"⚠️ [NiN-Demon] Error Telegram: {resp.status}")
    except Exception as e:
        print(f"⚠️ [NiN-Demon] Excepción Telegram: {e}")

async def upsert_to_graph(subject: str, predicate: str, obj: str):
    url = "http://127.0.0.1:6335/collections/nin_knowledge_graph/points"
    point_id = hash(f"{subject}-{predicate}-{obj}-{datetime.now()}") % (2**63 - 1)
    payload = {
        "points": [{
            "id": point_id,
            "vector": [0.0] * 1024,
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
                pass
    except Exception:
        pass

async def execute_tool_safe(session: ClientSession, tool_name: str, arguments: Dict[str, Any]):
    try:
        print(f"  [NiN-Demon] -> Ejecutando webhook/tool: {tool_name}")
        result = await session.call_tool(tool_name, arguments)
        text = result.content[0].text if result.content else "OK"
        return {"tool": tool_name, "status": "success", "result": text}
    except Exception as e:
        print(f"  [NiN-Demon] Error en n8n tool {tool_name}: {e}")
        return {"tool": tool_name, "status": "error", "error": str(e)}

async def process_mission(mission_file: str):
    basename = os.path.basename(mission_file)
    try:
        with open(mission_file, 'r') as f:
            data = json.load(f)
        
        tasks = data.get("tasks", [])
        mission_id = data.get("id", basename)
        print(f"🚀 [NiN-Demon] Misión en progreso: {mission_id}")

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
                    json.dump({"id": mission_id, "results": results}, f, indent=4)
                
                shutil.move(mission_file, os.path.join(DONE_DIR, basename))
                # await send_telegram_message(f"✅ Misión '{mission_id}' completada.")
    except Exception as e:
        print(f"❌ Fallo en {basename}: {e}")
        shutil.move(mission_file, os.path.join(FAIL_DIR, basename))

# --- BUCLE DE HERRAMIENTAS Y PENSAMIENTO MCP ---
async def agentic_tool_loop(user_text: str, mcp_session: ClientSession, mcp_tools: List[Dict]):
    # Combinar herramientas de Pensamiento con nuestras herramientas nativas
    ollama_tools = []
    
    # 1. Herramientas MCP (Pensamiento)
    for t in mcp_tools:
        ollama_tools.append({
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.inputSchema
            }
        })
        
    # 2. Herramienta nativa: Crear Misión
    ollama_tools.append({
        "type": "function",
        "function": {
            "name": "create_mission",
            "description": "Crea una misión JSON para interactuar con n8n, buscar libros, descargar en la colmena, etc. Úsala CUANDO HAYAS TERMINADO DE PENSAR y vayas a ejecutar una acción.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tasks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "tool": {"type": "string", "description": "mcp_n8n-control_execute_n8n_workflow"},
                                "args": {
                                    "type": "object", 
                                    "properties": {
                                        "workflow_id": {"type": "string", "description": "ID del workflow. Ej: L3u6POxhaS2TTjIu para Bypass LIBROS"}
                                    }
                                }
                            }
                        }
                    },
                    "message_for_user": {
                        "type": "string",
                        "description": "Mensaje amable a Diego avisando que generaste la misión."
                    }
                },
                "required": ["tasks", "message_for_user"]
            }
        }
    })

    system_prompt = """Sos NiN (Node in Network), el sistema operativo táctico de Diego.
Reglas estrictas:
1. Siempre puedes usar 'sequentialthinking' si necesitas planear paso a paso antes de actuar.
2. Si Diego pide ACCIÓN (descargar libros, buscar datos), usa 'create_mission'.
3. Si Diego solicita LIBROS a Telegram/Drive, el workflow_id para Bypass Descarga es 'L3u6POxhaS2TTjIu'.
4. Si es pura charla, asístelo amablemente sin usar tools de misión."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text}
    ]

    loop_count = 0
    max_loops = 10 # Guardarraíl: Máximo 10 iteraciones de herramientas (pensamiento)

    while loop_count < max_loops:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "tools": ollama_tools
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as http_session:
                async with http_session.post(OLLAMA_CHAT_URL, json=payload) as resp:
                    if resp.status != 200:
                        return f"Error HTTP de Alt: {resp.status}"
                    
                    data = await resp.json()
                    msg = data.get("message", {})
                    
                    if not msg.get("tool_calls"):
                        # No usó herramientas -> Respuesta final
                        return msg.get("content", "")
                        
                    messages.append(msg)
                    
                    # Iterar Tool Calls
                    for tc in msg.get("tool_calls", []):
                        func = tc.get("function", {})
                        t_name = func.get("name")
                        t_args = func.get("arguments", {})
                        
                        if t_name == "sequentialthinking":
                            print(f"🧠 [NiN Pensando] Paso {t_args.get('thoughtNumber', '?')}: {t_args.get('thought', '')[:40]}...")
                            try:
                                result = await mcp_session.call_tool(t_name, arguments=t_args)
                                res_text = result.content[0].text if result.content else "Pensamiento registrado."
                            except Exception as e:
                                res_text = f"Error al usar herramienta de pensamiento: {e}"
                                
                            messages.append({
                                "role": "tool",
                                "name": t_name,
                                "content": res_text
                            })
                            
                        elif t_name == "create_mission":
                            # Creación real de la misión JSON
                            try:
                                m_id = f"tg_{datetime.now().strftime('%H%M%S')}"
                                mission_data = {
                                    "id": m_id,
                                    "tasks": t_args.get("tasks", [])
                                }
                                m_path = f"{MISSIONS_DIR}/{m_id}.json"
                                with open(m_path, "w") as f:
                                    json.dump(mission_data, f, indent=4)
                                
                                user_msg = t_args.get("message_for_user", "He generado tu misión en el backend.")
                                return user_msg # Devolvemos el texto final para Telegram
                            except Exception as e:
                                messages.append({
                                    "role": "tool",
                                    "name": t_name,
                                    "content": f"Fallo creando misión: {e}"
                                })

            # Compactación de Contexto Simple (Si hay muchos mensajes, borramos pensamientos viejos para liberar RAM)
            if len(messages) > 15:
                # Mantener system, user original, y últimos 5 mensajes
                messages = [messages[0], messages[1]] + messages[-5:]
                
        except Exception as e:
            return f"Error en bucle agéntico: {e}"
            
        loop_count += 1

    return "Límite de razonamiento alcanzado (Circuit Breaker). Por favor, simplifica tu tarea."

async def telegram_ears_loop():
    print(f"👂 [Megademon] Orejas activas (Con Cliente MCP de Pensamiento Secuencial)")
    last_update_id = 0
    if os.path.exists(f"{CHAT_DIR}/last_update.id"):
        with open(f"{CHAT_DIR}/last_update.id", "r") as f:
            try: last_update_id = int(f.read().strip())
            except: pass

    # Iniciar el servidor MCP Local por stdio
    server_params = StdioServerParameters(command="npx", args=["-y", "@modelcontextprotocol/server-sequential-thinking"])
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_session:
            await mcp_session.initialize()
            print("🧠 [Megademon] Conectado al Pensamiento Secuencial (MCP)")
            tools_response = await mcp_session.list_tools()
            mcp_tools = tools_response.tools

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
                                        with open(CHAT_LOG, "a") as f: f.write(f"[{timestamp}] DIEGO: {text}\n")
                                        print(f"📩 [Megademon] Mensaje: {text}")
                                        
                                        await upsert_to_graph("Diego", "dijo_en_telegram", text)

                                        # BUCLE DE RAZONAMIENTO Y HERRAMIENTAS
                                        response = await agentic_tool_loop(text, mcp_session, mcp_tools)
                                        if response:
                                            await send_telegram_message(response)

                except Exception as e:
                    print(f"⚠️ Error en Orejas: {e}")
                
                await asyncio.sleep(2)

async def mission_watcher_loop():
    print(f"📂 [Megademon] Watcher de misiones activo")
    while True:
        try:
            target_files = [os.path.join(MISSIONS_DIR, f) for f in os.listdir(MISSIONS_DIR) 
                           if f.endswith(".json") and os.path.isfile(os.path.join(MISSIONS_DIR, f))]
            for f in target_files:
                await process_mission(f)
        except Exception:
            pass
        await asyncio.sleep(2)

async def main():
    for d in [DONE_DIR, FAIL_DIR, MISSIONS_DIR, CHAT_DIR]: 
        os.makedirs(d, exist_ok=True)
    
    print(f"👹 Megademon 2.0 (CoT Enable) - Motores encendidos.")
    await asyncio.gather(
        mission_watcher_loop(),
        telegram_ears_loop()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown.")
