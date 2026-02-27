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
def invoke_secret_agent(consulta: str) -> str:
    """
    Invoca al 'Agente Secreto - Mapeador' de n8n para realizar tareas complejas de lectura
    de archivos grandes, resúmenes de contexto o mapeo del repositorio NIN.
    """
    ip = get_container_ip()
    webhook_url = f"http://{ip}:5678/webhook/agente-secreto"
    payload = json.dumps({"consulta": consulta}).encode('utf-8')
    req = urllib.request.Request(webhook_url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    
    try:
        # Tarda unos minutos por el tamaño del modelo de 32B
        with urllib.request.urlopen(req, timeout=300) as response:
            result = response.read().decode('utf-8')
            return result
    except urllib.error.HTTPError as e:
        return f"Error HTTP del Agente de n8n: {e.code} {e.reason} - {e.read().decode('utf-8')}"
    except Exception as e:
        return f"Error conectando al Agente de n8n: {e}"

if __name__ == "__main__":
    mcp.run(transport='stdio')
