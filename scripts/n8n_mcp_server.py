#!/usr/bin/env python3
"""
n8n_mcp_server.py — MCP Server para conexión nativa y fluida con n8n.
Basa sus operaciones en el enfoque sin docker-exec de n8n_cli.py.
"""

import json
import os
import subprocess
import urllib.request
import urllib.error
import urllib.parse
import ssl
import sqlite3
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP

# Setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
ENV_FILE = os.path.join(REPO_DIR, ".env")
DB_PATH = os.path.join(REPO_DIR, "agente_memoria.db")
CONTAINER = "N8N-NiN-uso-exclusivo-del-proyecto-nin"
TIMEOUT = 5

# === LÍMITES DE PROYECTO ===
# NIN solo opera sobre estos contenedores. NUNCA tocar contenedores de otros proyectos
# (cunningham-Espejo: lucy_brain_*, lucy_eyes_*, lucy_hands_*, lucy_ui_*, etc.)
NIN_CONTAINERS = {"n8n-lucy", "qdrant-lucy", "searxng-lucy"}


# Desactivar verificación SSL para entornos locales (Requerimiento Usuario)
ssl_context = ssl._create_unverified_context()

import sys
import argparse

# Parsear args básicos al principio para poder inyectar el puerto
parser = argparse.ArgumentParser(description="NiN MCP Server", add_help=False)
parser.add_argument("--port", type=int, default=8000)
args, _ = parser.parse_known_args()

mcp = FastMCP("n8n Controlador", host="127.0.0.1", port=args.port)

def load_api_key() -> str:
    if not os.path.isfile(ENV_FILE):
        raise RuntimeError("No existe .env en " + REPO_DIR)
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith("N8N_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("N8N_API_KEY no encontrada en .env")

def get_container_ip() -> str:
    cache_file = os.path.join(REPO_DIR, ".n8n_ip")
    if os.path.isfile(cache_file):
        cached_ip = open(cache_file).read().strip()
        if cached_ip:
            try:
                urllib.request.urlopen(f"http://{cached_ip}:5678/healthz", timeout=1)
                return cached_ip
            except Exception:
                pass

    try:
        result = subprocess.run(
            ["docker", "inspect", CONTAINER, "--format",
             "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}"],
            capture_output=True, text=True, timeout=2
        )
        ip = result.stdout.strip()
        if ip:
            with open(cache_file, "w") as f:
                f.write(ip)
            return ip
    except Exception:
        pass # Docker está colgado o falló, usar fallback agresivo

    # Fallback: Escaneo de fuerza bruta en las subredes de Docker bypassando el daemon
    try:
        import concurrent.futures
        def check_ip(test_ip: str) -> str:
            try:
                urllib.request.urlopen(f"http://{test_ip}:5678/healthz", timeout=0.4)
                return test_ip
            except Exception:
                return ""

        # NOTA: NO incluir 127.0.0.1 — Espejo's n8n usa host networking en :5678
        # y lo detectaríamos erróneamente. NIN usa bridge, solo buscar en subnets Docker.
        ips_to_test = []
        for subnet in range(17, 32):
            for host in range(1, 6):
                ips_to_test.append(f"172.{subnet}.0.{host}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            for future in concurrent.futures.as_completed([executor.submit(check_ip, i) for i in ips_to_test]):
                res = future.result()
                if res:
                    with open(cache_file, "w") as f:
                        f.write(res)
                    return res
    except Exception:
        pass

    raise RuntimeError(f"Error crítico: Docker daemon no responde y el escáner de subred falló en encontrar n8n.")

def api_request(method: str, path: str, body: Optional[Dict] = None) -> Dict:
    api_key = load_api_key()
    ip = get_container_ip()
    url = f"http://{ip}:5678/api/v1{path}"
    headers = {
        "Accept": "application/json",
        "X-N8N-API-KEY": api_key,
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        # Usamos el contexto SSL deshabilitado para evitar errores en local
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ssl_context) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {"status": "success"}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {raw}")
    except Exception as e:
        raise RuntimeError(f"Request failed: {str(e)}")

def strip_heavy(wf: Dict) -> Dict:
    for key in ("activeVersion", "shared", "staticData", "pinData", "tags"):
        wf.pop(key, None)
    return wf

@mcp.tool()
def list_n8n_workflows() -> List[Dict]:
    """Lista todos los workflows disponibles en n8n."""
    data = api_request("GET", "/workflows")
    wfs = data.get("data", data) if isinstance(data, dict) else data
    return [{"id": w["id"], "name": w["name"], "active": w.get("active")} for w in wfs]

@mcp.tool()
def get_n8n_workflow(workflow_id: str) -> str:
    """Obtiene el JSON completo de un workflow de n8n por su ID."""
    data = api_request("GET", f"/workflows/{workflow_id}")
    return json.dumps(strip_heavy(data), indent=2, ensure_ascii=False)

@mcp.tool()
def update_n8n_workflow(workflow_id: str, workflow_json_string: str) -> str:
    """Actualiza un workflow de n8n indicando el workflow_id y el contenido JSON completo."""
    wf_data = json.loads(workflow_json_string)
    data = api_request("PUT", f"/workflows/{workflow_id}", wf_data)
    return f"Workflow '{data.get('name')}' actualizado con éxito."

@mcp.tool()
def activate_n8n_workflow(workflow_id: str) -> str:
    """Activa un workflow en n8n"""
    api_request("POST", f"/workflows/{workflow_id}/activate")
    return f"Workflow {workflow_id} activado con éxito."

@mcp.tool()
def deactivate_n8n_workflow(workflow_id: str) -> str:
    """Desactiva un workflow en n8n"""
    api_request("POST", f"/workflows/{workflow_id}/deactivate")
    return f"Workflow {workflow_id} desactivado."

@mcp.tool()
def execute_n8n_workflow(workflow_id: str, trigger_data: Optional[Dict[str, Any]] = None) -> str:
    """Ejecuta un workflow mediante API usando su node trigger. Retorna los resultados."""
    if workflow_id == "b0QtaKcqH5I0WLYk":
        import re
        ip = get_container_ip()
        webhook_url = f"http://{ip}:5678/webhook/youtube-search"
        req = urllib.request.Request(webhook_url, method="POST")
        req.add_header("Content-Type", "application/json")
        data = json.dumps(trigger_data or {}).encode("utf-8")
        
        raw_result = None
        try:
            with urllib.request.urlopen(req, data=data, context=ssl._create_unverified_context()) as response:
                raw_result = json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Fallback: usar webhook de test
                webhook_url = f"http://{ip}:5678/webhook-test/youtube-search"
                req = urllib.request.Request(webhook_url, method="POST")
                req.add_header("Content-Type", "application/json")
                try:
                    with urllib.request.urlopen(req, data=data, context=ssl._create_unverified_context()) as response:
                        raw_result = json.loads(response.read().decode())
                except Exception as e2:
                    return f"Error ejecutando webhook test: {e2}"
            else:
                return f"Error ejecutando webhook: HTTP {e.code}: {e.read().decode()}"
        except Exception as e:
            return f"Error de red: {e}"
        
        if raw_result is None:
            return "Error: no se obtuvo respuesta del webhook."
        
        # Extraer pares (titulo, url) del output formateado por n8n
        # Formato: "N. Título del video\n   URL: https://..."
        output_text = raw_result.get("output", "") if isinstance(raw_result, dict) else str(raw_result)
        entries = re.findall(
            r'\d+\.\s+(.+?)\n\s+URL:\s+(https://www\.youtube\.com/watch\?v=[\w-]+)',
            output_text
        )
        
        if not entries:
            # fallback: intentar extraer solo URLs
            urls = re.findall(r'https://www\.youtube\.com/watch\?v=[\w-]+', output_text)
            best_url = urls[0] if urls else None
            best_title = "resultado #1"
        else:
            # Score cada resultado por cuántas palabras de la query aparecen en el título
            query_words = set(re.findall(r'\w+', (trigger_data or {}).get('query', '').lower()))
            # Filtrar stopwords comunes para no contaminar el score
            stopwords = {'el', 'la', 'los', 'las', 'de', 'del', 'en', 'y', 'a', 'un', 'una', 'que', 'por', 'con'}
            query_words -= stopwords
            
            best_score = -1
            best_url = entries[0][1]
            best_title = entries[0][0]
            
            for title, url in entries:
                title_words = set(re.findall(r'\w+', title.lower()))
                score = len(query_words & title_words)  # intersección
                if score > best_score:
                    best_score = score
                    best_url = url
                    best_title = title
        
        if best_url:
            try:
                launcher_req = urllib.request.Request(
                    f"http://127.0.0.1:9999/play?url={urllib.parse.quote(best_url, safe='')}",
                    method="GET"
                )
                with urllib.request.urlopen(launcher_req, timeout=5) as lr:
                    lr.read()
                return json.dumps({
                    "output": f"▶️ Abriendo: {best_title}\n{best_url}\n\n" + output_text
                }, indent=2, ensure_ascii=False)
            except Exception as fe:
                return json.dumps({"output": f"Búsqueda OK pero error al abrir Firefox: {fe}\n\n" + output_text}, indent=2, ensure_ascii=False)
        else:
            return json.dumps(raw_result, indent=2, ensure_ascii=False)

    payload = {"workflowId": workflow_id}
    if trigger_data:
        payload["triggerData"] = trigger_data
    result = api_request("POST", f"/workflows/{workflow_id}/execute", payload)
    return json.dumps(result, indent=2, ensure_ascii=False)

@mcp.tool()
def invoke_secret_agent(consulta: str) -> str:
    """
    Invoca al 'Agente Secreto - Mapeador' de n8n para tareas de REZONAMIENTO que requieren
    el modelo de 32B (Advertencia: Latencia alta de 1-3 minutos).
    """
    ip = get_container_ip()
    webhook_url = f"http://{ip}:5678/webhook/agente-secreto"
    payload = json.dumps({"consulta": consulta}).encode('utf-8')
    req = urllib.request.Request(webhook_url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    
    try:
        # Espera la respuesta completa (Respond to Webhook)
        with urllib.request.urlopen(req, timeout=300, context=ssl_context) as response:
            raw = response.read().decode('utf-8')
            try:
                data = json.loads(raw)
                if isinstance(data, list) and len(data) > 0: data = data[0]
                return str(data.get("output", raw))
            except:
                return raw
    except Exception as e:
        return f"Error conectando al Agente de n8n: {e}"

@mcp.tool()
def recordar_contexto(project_name: str, session_goal: str, open_files: str = "", active_workflows: str = "") -> str:
    """Guarda el estado actual de la sesión en la base de datos persistente."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO session_context (project_name, session_goal, open_files, active_workflows)
            VALUES (?, ?, ?, ?)
        ''', (project_name, session_goal, open_files, active_workflows))
        conn.commit()
        conn.close()
        return "Contexto de sesión guardado correctamente en SQLite."
    except Exception as e:
        return f"Error guardando contexto: {e}"

@mcp.tool()
def recuperar_contexto() -> str:
    """Recupera el último contexto guardado para reanudar el trabajo."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM session_context ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        conn.close()
        if row:
            return f"Último contexto encontrado:\\n- Proyecto: {row['project_name']}\\n- Meta: {row['session_goal']}\\n- Archivos: {row['open_files']}\\n- Workflows: {row['active_workflows']}\\n- Fecha: {row['timestamp']}"
        return "No hay contexto previo guardado."
    except Exception as e:
        return f"Error recuperando contexto: {e}"

@mcp.tool()
def guardar_mensaje(role: str, content: str) -> str:
    """Guarda un mensaje importante en el historial persistente."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO conversation_history (role, content) VALUES (?, ?)', (role, content))
        conn.commit()
        conn.close()
        return "Mensaje guardado en el historial."
    except Exception as e:
        return f"Error guardando mensaje: {e}"

def register_dynamic_tools():
    """Busca flujos activos que empiecen con 'Tool:' y los registra como herramientas MCP."""
    try:
        data = api_request("GET", "/workflows?active=true")
        wfs = data.get("data", [])
        for wf in wfs:
            name = wf.get("name", "")
            if name.startswith("Tool:"):
                # Buscar el path del webhook
                webhook_path = None
                for node in wf.get("nodes", []):
                    if node.get("type") == "n8n-nodes-base.webhook":
                        webhook_path = node.get("parameters", {}).get("path")
                        break
                
                    if webhook_path:
                        # Normalizar nombre: minúsculas, sin espacios, y quitar tildes
                        clean_name = name.replace("Tool:", "").strip().lower()
                        import unicodedata
                        clean_name = "".join(
                            c for c in unicodedata.normalize('NFD', clean_name)
                            if unicodedata.category(c) != 'Mn'
                        )
                        tool_name = clean_name.replace(" ", "_").replace("-", "_")
                    
                    # Definir la función de la herramienta
                    def create_tool_handler(path, display_name):
                        def dynamic_tool_handler(**kwargs) -> str:
                            ip = get_container_ip()
                            url = f"http://{ip}:5678/webhook/{path}"
                            
                            # Si se pasa un solo argumento 'kwargs' (como en el error previo), 
                            # intentar extraer su contenido si es un dict, sino usar todos los kwargs
                            payload_dict = kwargs
                            if "kwargs" in kwargs and len(kwargs) == 1:
                                try:
                                    if isinstance(kwargs["kwargs"], str):
                                        payload_dict = json.loads(kwargs["kwargs"])
                                    elif isinstance(kwargs["kwargs"], dict):
                                        payload_dict = kwargs["kwargs"]
                                except:
                                    pass
                            
                            payload = json.dumps(payload_dict).encode('utf-8')
                            req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
                            try:
                                # Espera extendida para herramientas dinámicas
                                with urllib.request.urlopen(req, timeout=60, context=ssl_context) as resp:
                                    raw = resp.read().decode('utf-8')
                                    try:
                                        data = json.loads(raw)
                                        if isinstance(data, list) and len(data) > 0: data = data[0]
                                        return str(data.get("output", raw))
                                    except:
                                        return raw
                            except Exception as e:
                                return f"Error en {display_name}: {e}"
                        
                        dynamic_tool_handler.__name__ = tool_name
                        dynamic_tool_handler.__doc__ = f"Ejecuta el flujo de n8n: {name}"
                        return dynamic_tool_handler

                    handler = create_tool_handler(webhook_path, name)
                    mcp.tool()(handler)
                    # print(f"Herramienta dinámica registrada: {tool_name} -> {webhook_path}")
    except Exception as e:
        # print(f"Error en autodescubrimiento: {e}")
        pass

if __name__ == "__main__":
    # Parsear resto de argumentos (port ya se parseó arriba en modo known_args)
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio", help="Transporte a usar")
    args = parser.parse_args()

    register_dynamic_tools()
    
    # Registro Manual de Emergencia para YouTube (Firefox / uBlock)
    @mcp.tool()
    def reproductor_de_video(url: str) -> str:
        """Abre un video de YouTube en el navegador Firefox del host."""
        import subprocess
        try:
            # Firefox en el host abrirá una nueva pestaña en el perfil activo (Lucy Chat)
            # que ya cuenta con uBlock Origin
            c = subprocess.Popen(
                ["nsenter", "-t", "1", "-m", "-u", "-i", "-n", "-p", "--", "sudo", "-u", "lucy-ubuntu", "DISPLAY=:0", "firefox", "-P", "Lucy Chat", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return f"▶️ Video lanzado exitosamente vía Firefox (con uBlock): {url}"
        except Exception as e:
            return f"Error ejecutando Firefox: {e}"
    
    if args.transport == "sse":
        print(f"🚀 Iniciando Servidor MCP en modo SSE (http://127.0.0.1:8001/sse)")
        mcp.settings.port = 8001
        mcp.run(transport='sse')
    else:
        mcp.run(transport='stdio')
