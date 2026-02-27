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
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP

# Setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
ENV_FILE = os.path.join(REPO_DIR, ".env")
CONTAINER = "n8n-lucy"
TIMEOUT = 5

mcp = FastMCP("n8n Controlador")

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

        ips_to_test = ["127.0.0.1"]
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
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
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
def execute_n8n_workflow(workflow_id: str, trigger_data: Optional[str] = None) -> str:
    """Ejecuta un workflow mediante API usando su node trigger. Retorna los resultados."""
    payload = {"workflowId": workflow_id}
    if trigger_data:
        payload["triggerData"] = json.loads(trigger_data)
    result = api_request("POST", f"/workflows/{workflow_id}/execute", payload)
    return json.dumps(result, indent=2, ensure_ascii=False)

@mcp.tool()
def leer_archivo_n8n(ruta: str) -> str:
    """Lee un archivo del host usando el nodo nativo de n8n."""
    ip = get_container_ip()
    url = f"http://{ip}:5678/webhook/agente-leer"
    payload = json.dumps({"ruta": ruta}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("contenido", "Archivo vacío o no encontrado.")
    except Exception as e:
        return f"Error leyendo vía n8n: {e}"

@mcp.tool()
def escanear_directorio_nin(ruta: str = "/home/lucy-ubuntu/Escritorio/NIN", profundidad: int = 2) -> str:
    """Escanea el directorio NIN a alta velocidad."""
    try:
        cmd = ["find", ruta, "-maxdepth", str(profundidad), "-not", "-path", "*/.git/*", "-printf", "%y %p\n"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return res.stdout if res.stdout else "Directorio vacío."
    except Exception as e:
        return f"Error escaneando: {e}"

@mcp.tool()
def grep_nin(patron: str) -> str:
    """Busca un patrón en archivos del repositorio NIN usando grep directamente."""
    try:
        cmd = ["grep", "-rn", patron, REPO_DIR, "--include=*.py", "--include=*.md", "--include=*.json", "--exclude-dir=.git"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return res.stdout[:5000] if res.stdout else "No se encontraron resultados."
    except Exception as e:
        return f"Error en grep: {e}"

@mcp.tool()
def estado_sistema_nin() -> str:
    """Obtiene el estado de salud del servidor (CPU, RAM, Docker) en milisegundos."""
    try:
        ram = subprocess.getoutput("free -h | head -2")
        cpu = subprocess.getoutput("top -bn1 | grep 'Cpu(s)'")
        disco = subprocess.getoutput("df -h / | tail -1")
        docker = subprocess.getoutput("docker ps --format '{{.Names}} {{.Status}}' 2>/dev/null")
        return f"--- RAM ---\n{ram}\n\n--- CPU ---\n{cpu}\n\n--- DISCO ---\n{disco}\n\n--- DOCKER ---\n{docker}"
    except Exception as e:
        return f"Error obteniendo estado: {e}"

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
        with urllib.request.urlopen(req, timeout=300) as response:
            result = response.read().decode('utf-8')
            return result
    except Exception as e:
        return f"Error conectando al Agente de n8n: {e}"

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
                    tool_name = name.replace("Tool:", "").strip().lower().replace(" ", "_")
                    
                    # Definir la función de la herramienta
                    def create_tool_handler(path, display_name):
                        def dynamic_tool_handler(**kwargs) -> str:
                            ip = get_container_ip()
                            url = f"http://{ip}:5678/webhook/{path}"
                            payload = json.dumps(kwargs).encode('utf-8')
                            req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
                            try:
                                with urllib.request.urlopen(req, timeout=30) as resp:
                                    return resp.read().decode('utf-8')
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
    register_dynamic_tools()
    mcp.run(transport='stdio')
