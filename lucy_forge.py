#!/usr/bin/env python3
import sys
import json
import os
import requests
from requests.exceptions import RequestException

# Color definitions for Cyberpunk style output
CYAN = '\033[96m'
RED = '\033[91m'
GREEN = '\033[92m'
RESET = '\033[0m'

def print_log(msg, level="INFO"):
    if level == "INFO":
        print(f"[{CYAN}SYSTEM{RESET}] {msg}")
    elif level == "SUCCESS":
        print(f"[{GREEN}SUCCESS{RESET}] {msg}")
    elif level == "ERROR":
        print(f"[{RED}FATAL{RESET}] {msg}", file=sys.stderr)

def load_env(filepath=".env"):
    """Carga variables de entorno desde el archivo local .env."""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

def read_prompt(filepath="prompts/architect_v2_prompt.md"):
    """Lee el prompt base del Arquitecto."""
    if not os.path.exists(filepath):
        print_log(f"Prompt file {filepath} not found.", "ERROR")
        sys.exit(1)
    with open(filepath, 'r') as f:
        return f.read()

def compile_workflow(prompt, user_request, max_retries=3):
    """
    Se comunica con el modelo QwQ-32B local, envía la instrucción de arquitectura, 
    y valida que devuelva un JSON estructurado. Contiene un bucle de auto-retry.
    """
    ollama_url = "http://localhost:11434/api/chat"
    
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_request}
    ]

    for attempt in range(1, max_retries + 1):
        print_log(f"Forging neural pathway... (Attempt {attempt}/{max_retries})")
        payload = {
            "model": "qwq-abliterated:32b",
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.1 # Mantenemos la temperatura baja para rigurosidad estructural
            } 
        }
        
        try:
            # Request connection to local Ollama API
            response = requests.post(ollama_url, json=payload, timeout=180)
            response.raise_for_status()
            data = response.json()
            
            content = data.get("message", {}).get("content", "").strip()
            
            # Defensa contra modelos que usan markdown code blocks a pesar de las instrucciones
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            print_log("Analyzing JSON structure...")
            workflow_json = json.loads(content)
            
            # Validación estructural mínima para n8n
            if "nodes" not in workflow_json or "connections" not in workflow_json:
                raise ValueError("Payload missing vital 'nodes' or 'connections' keys.")
                
            print_log("Structural integrity validated.", "SUCCESS")
            return workflow_json
            
        except json.JSONDecodeError as e:
            print_log(f"JSON Parse Error: {e}", "ERROR")
            if attempt < max_retries:
                # Feedback loop para que el LLM corrija el error
                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user", 
                    "content": f"Error de parseo JSON: {e}. Corrige este error estructural y devuelve SOLO el JSON. CERO texto adicional."
                })
            else:
                print_log("Max auto-retries exhausted. Neural compilation failed.", "ERROR")
                sys.exit(1)
                
        except ValueError as e:
            print_log(f"Structural Validation Error: {e}", "ERROR")
            if attempt < max_retries:
                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user", 
                    "content": f"Error estructural: {e}. Asegúrate de incluir y respetar las claves obligatorias 'nodes' y 'connections'."
                })
            else:
                print_log("Max auto-retries exhausted. Neural compilation failed.", "ERROR")
                sys.exit(1)
                
        except RequestException as e:
            # Errores caídas de docker o timeout de la request en llm grande
            print_log(f"Cognitive interface network failure (Ollama API): {e}", "ERROR")
            sys.exit(1)

def inject_workflow(workflow_json):
    """
    Inyecta el resultado validado como nuevo flujo en la base de n8n mediante REST API.
    """
    n8n_url = "http://localhost:5678/api/v1/workflows"
    api_key = os.environ.get("N8N_API_KEY")
    
    if not api_key:
        print_log("N8N_API_KEY missing in .env configuration. Matrix link severed.", "ERROR")
        sys.exit(1)
        
    headers = {
        "Content-Type": "application/json",
        "X-N8N-API-KEY": api_key
    }
    
    print_log("Injecting workflow into local n8n matrix...")
    try:
        response = requests.post(n8n_url, headers=headers, json=workflow_json, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        workflow_id = result.get("id")
        
        print_log(f"INJECTION SUCCESSFUL. L.U.C.Y FORGE HAS MINTED A NEW NEURAL PATHWAY.", "SUCCESS")
        print_log(f"NEW WORKFLOW ID: {workflow_id} - READY IN DASHBOARD.", "SUCCESS")
        
    except RequestException as e:
        print_log(f"Injection failed (n8n API matrix sync error): {e}", "ERROR")
        if e.response is not None:
            print_log(f"n8n response body: {e.response.text}", "ERROR")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print_log('Usage: python3 lucy_forge.py "<Instrucción para el flujograma>"', "ERROR")
        sys.exit(1)
        
    user_request = sys.argv[1]
    
    # 1. Cargar variables
    load_env()
    
    # 2. Cargar núcleo prompt del Arquitecto
    prompt = read_prompt()
    
    # 3. Ensamblar estructura validada vía la forja LLM
    workflow_json = compile_workflow(prompt, user_request)
    
    # 4. Inyectar entidad en base de n8n
    inject_workflow(workflow_json)

if __name__ == "__main__":
    main()
