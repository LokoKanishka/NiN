import os
import requests
from dotenv import load_dotenv

load_dotenv("/home/lucy-ubuntu/Escritorio/NIN/.env")
N8N_API_KEY = os.getenv("N8N_API_KEY")

headers = {
    "X-N8N-API-KEY": N8N_API_KEY,
    "Content-Type": "application/json"
}

BASE_URL = "http://172.24.0.4:5678/api/v1/workflows"

def fix_telegram():
    wid = "WrslsGzYsDP8hJZT"
    r = requests.get(f"{BASE_URL}/{wid}", headers=headers, timeout=5)
    wf = r.json()
    for node in wf.get('nodes', []):
        if node['name'] == 'Telegram HTTP':
            for param in node['parameters']['bodyParameters']['parameters']:
                if param['name'] == 'text':
                    param['value'] = '={{ $json.body.message || $json.body.mensaje || $json.kwargs || "Alerta desde NiN" }}'
    res = requests.put(f"{BASE_URL}/{wid}", headers=headers, json=wf, timeout=5)
    print("✅ Telegram arreglado." if res.status_code == 200 else f"Error: {res.text}")

def fix_agente():
    wid = "8RwngQmsa4ObRh2I"
    r = requests.get(f"{BASE_URL}/{wid}", headers=headers, timeout=5)
    wf = r.json()
    for node in wf.get('nodes', []):
        if node['name'] == 'Ollama Chat Model':
            node['parameters']['model'] = 'qwen2.5-coder:14b-instruct-q8_0'
    res = requests.put(f"{BASE_URL}/{wid}", headers=headers, json=wf, timeout=5)
    print("✅ Agente Secreto apuntado a Alt (Qwen 14B)." if res.status_code == 200 else f"Error: {res.text}")

def fix_scraping():
    wid = "IHfBIXELwr3us22J"
    r = requests.get(f"{BASE_URL}/{wid}", headers=headers, timeout=5)
    wf = r.json()
    # Reemplazar el Code node problemático por un httpRequest a jina AI
    for i, node in enumerate(wf.get('nodes', [])):
        if node['name'] == 'Python Scrape':
            wf['nodes'][i] = {
                "parameters": {
                    "url": "={{ 'https://r.jina.ai/' + ($json.body.url || $json.kwargs || '') }}",
                    "options": {}
                },
                "id": node['id'],
                "name": node['name'],
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.1,
                "position": node['position']
            }
    res = requests.put(f"{BASE_URL}/{wid}", headers=headers, json=wf, timeout=5)
    print("✅ Scraping profundo recableado a Jina AI API (Serverless)." if res.status_code == 200 else f"Error: {res.text}")

if __name__ == "__main__":
    fix_telegram()
    fix_agente()
    fix_scraping()
