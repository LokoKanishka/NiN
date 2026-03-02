import os
import sys
import requests
import json
from dotenv import load_dotenv

load_dotenv("/home/lucy-ubuntu/Escritorio/NIN/.env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def ask_groq(prompt, model="llama-3.3-70b-versatile"):
    """
    Se conecta a la IA a través del hardware LPU de Groq.
    Velocidad absurda y razonamiento de 70B de parámetros.
    Usamos REST puro al estilo cyberpunk.
    """
    if not GROQ_API_KEY:
        return "Error: GROQ_API_KEY no encontrada en .env"

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # API compatible con formato OpenAI
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            try:
                # Extraer respuesta y métricas de velocidad
                text = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                time_sec = usage.get("total_time")
                tok_per_sec = usage.get("prompt_tokens") / time_sec if time_sec else 0
                return f"{text}\n\n[MÉTRICAS DEL MOTOR LPUs: T={time_sec}s]"
            except (KeyError, IndexError):
                return f"Error parseando estructura Groq: {json.dumps(data)}"
        else:
            return f"Error en Groq (HTTP {response.status_code}): {response.text}"

    except requests.exceptions.Timeout:
        return "Error: Timeout. El cerebro no respondió en tiempo."
    except Exception as e:
        return f"Excepción crítica: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2 and sys.stdin.isatty():
        print("Uso 1: python3 groq_titan.py 'tu comando' [--file ruta.txt]")
        print("Uso 2: cat ruta.txt | python3 groq_titan.py 'tu comando'")
        sys.exit(1)

    prompt = sys.argv[1] if len(sys.argv) > 1 else "Analiza el siguiente texto:"
    
    # Manejo de entrada estándar (Pipes)
    if not sys.stdin.isatty():
        contexto_pipe = sys.stdin.read()
        if contexto_pipe.strip():
            prompt = f"{prompt}\n\n[CONTEXTO PIPELINE]:\n{contexto_pipe}"
            
    # Manejo de modo de archivo explícito
    elif len(sys.argv) > 3 and sys.argv[2] == "--file":
        filepath = sys.argv[3]
        if os.path.isfile(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                contexto_archivo = f.read()
            prompt = f"{prompt}\n\n[CONTEXTO DEL ARCHIVO]:\n{contexto_archivo}"
        else:
            print(f"Error: No se encontró el archivo {filepath}")
            sys.exit(1)
            
    res = ask_groq(prompt)
    print("\n=== RESPUESTA DEL TITÁN (Llama 3.3 70B) ===")
    print(res)
    print("============================================\n")


