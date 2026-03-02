import os
import urllib.request
import json
from dotenv import load_dotenv

load_dotenv("/home/lucy-ubuntu/Escritorio/NIN/.env")
apikey = os.getenv("N8N_API_KEY")

base = "http://172.24.0.4:5678/api/v1/workflows"
headers = {"X-N8N-API-KEY": apikey, "Content-Type": "application/json"}

proxy_handler = urllib.request.ProxyHandler({})
opener = urllib.request.build_opener(proxy_handler)
urllib.request.install_opener(opener)

def clean_wf(wf):
    allowed = {"name", "nodes", "connections", "settings", "staticData", "meta", "pinData", "tags"}
    return {k: v for k, v in wf.items() if k in allowed}

def process():
    # Telegram
    req = urllib.request.Request(f"{base}/WrslsGzYsDP8hJZT", headers=headers)
    wf_tg = json.loads(urllib.request.urlopen(req, timeout=10).read())
    for n in wf_tg.get('nodes', []):
        if n['name'] == 'Telegram HTTP':
            for p in n['parameters']['bodyParameters']['parameters']:
                if p['name'] == 'text':
                    p['value'] = '={{ $json.body.message || $json.body.mensaje || $json.kwargs || "Alerta desde NiN" }}'
    
    with open('/tmp/tg_fixed.json', 'w') as f:
        json.dump(wf_tg, f)

    # Agente
    req = urllib.request.Request(f"{base}/8RwngQmsa4ObRh2I", headers=headers)
    wf_ag = json.loads(urllib.request.urlopen(req, timeout=10).read())
    for n in wf_ag.get('nodes', []):
        if n['name'] == 'Ollama Chat Model':
            n['parameters']['model'] = 'qwen2.5-coder:14b-instruct-q8_0'
            
    with open('/tmp/ag_fixed.json', 'w') as f:
        json.dump(wf_ag, f)

    # Scraping
    req = urllib.request.Request(f"{base}/IHfBIXELwr3us22J", headers=headers)
    wf_sc = json.loads(urllib.request.urlopen(req, timeout=10).read())
    for i, n in enumerate(wf_sc.get('nodes', [])):
        if n['name'] == 'Python Scrape':
            wf_sc['nodes'][i] = {
                "parameters": {
                    "url": "={{ 'https://r.jina.ai/' + ($json.body.url || $json.kwargs || 'https://example.com') }}",
                    "options": {}
                },
                "id": n['id'],
                "name": n['name'],
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.1,
                "position": n['position']
            }
            
    with open('/tmp/sc_fixed.json', 'w') as f:
        json.dump(wf_sc, f)
    
    print("🚀 JSONs exportados a /tmp")

if __name__ == "__main__":
    process()
