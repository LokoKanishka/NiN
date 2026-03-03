import asyncio
import json
import logging
from typing import List, Dict
import aiohttp
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(level=logging.ERROR)

OLLAMA_MODEL = "qwen2.5-coder:14b-instruct-q8_0"
OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"

async def test_agentic_loop(user_text: str):
    print("Levantando MCP Sequential Thinking...")
    server_params = StdioServerParameters(command="npx", args=["-y", "@modelcontextprotocol/server-sequential-thinking"])
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_session:
            await mcp_session.initialize()
            tools_response = await mcp_session.list_tools()
            
            # Preparar Tools
            ollama_tools = []
            for t in tools_response.tools:
                ollama_tools.append({
                    "type": "function", 
                    "function": {
                        "name": t.name, 
                        "description": t.description, 
                        "parameters": t.inputSchema
                    }
                })
            
            ollama_tools.append({
                "type": "function", "function": {
                    "name": "create_mission", 
                    "description": "Crea una mision para accionar comandos complejos o herramientas externas al finalizar de pensar.",
                    "parameters": {"type": "object", "properties": {"tasks": {"type": "array"}}, "required": ["tasks"]}
                }
            })

            messages = [
                {"role": "system", "content": "Sos NiN, el sistema operativo de asistencia.\n"
                 "IMPORTANTE: Tienes acceso a herramientas (tools). Si necesitas usarlas, DEBES "
                 "devolver una 'tool_call' según la estructura de la API. NUNCA respondas con el JSON crudo en el texto.\n"
                 "Usa 'sequentialthinking' para pensar paso a paso antes de tu respuesta final."},
                {"role": "user", "content": user_text}
            ]

            print(f"\n[Usuario dice]: {user_text}")
            
            for loop_count in range(5):
                payload = {
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False,
                    "tools": ollama_tools
                }
                
                async with aiohttp.ClientSession() as http_session:
                    async with http_session.post(OLLAMA_CHAT_URL, json=payload) as resp:
                        data = await resp.json()
                        msg = data.get("message", {})
                        
                        if not msg.get("tool_calls"):
                            # Workaround para Qwen 14B: Si escupe JSON puro asumiendo que es tool_call.
                            texto = msg.get("content", "").strip()
                            if texto.startswith("```json") and "sequentialthinking" in texto:
                                try:
                                    raw_json = texto.replace("```json", "").replace("```", "").strip()
                                    tc_data = json.loads(raw_json)
                                    msg["tool_calls"] = [{"function": {"name": tc_data.get("name"), "arguments": tc_data.get("arguments", {})}}]
                                except Exception:
                                    pass
                            
                            if not msg.get("tool_calls"):
                                print(f"\n🤖 [NiN Respuesta Final]:\n{msg.get('content', '')}")
                                return
                            
                        messages.append(msg)
                        
                        for tc in msg.get("tool_calls", []):
                            t_name = tc["function"]["name"]
                            t_args = tc.get("function", {}).get("arguments", {})
                            
                            if t_name == "sequentialthinking":
                                print(f"🧠 [Pensamiento {t_args.get('thoughtNumber', '?')}/{t_args.get('totalThoughts', '?')}]: {t_args.get('thought')}")
                                try:
                                    result = await mcp_session.call_tool(t_name, arguments=t_args)
                                    messages.append({"role": "tool", "name": t_name, "content": result.content[0].text if result.content else "OK"})
                                except Exception as e:
                                    print(f"Error MCP: {e}")
                                    messages.append({"role": "tool", "name": t_name, "content": "Error interno al pensar."})
                            else:
                                print(f"🛠️ [Llamó Tool Nativa FINAL]: {t_name} con {t_args}")
                                return

print("\n--- PRUEBA DIRECTA DE QWEN 14B + SECUENCIAL MCP ---")
asyncio.run(test_agentic_loop("hola que hora es maestro?"))
