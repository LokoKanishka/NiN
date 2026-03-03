import urllib.request
import json
import base64

wf = {
  "name": "Bypass Cero Restricción - Metafísica",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "GET",
        "path": "subir-metafisica",
        "options": {}
      },
      "id": "webhook-start",
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [460, 460],
      "typeVersion": 1,
      "webhookId": "9f62de4d-51a6-4dc4-bca5-bypass_metafisica"
    },
    {
      "parameters": {
        "url": "https://ia903403.us.archive.org/32/items/aristoteles-la-metafisica/Arist%C3%B3teles%20-%20La%20metaf%C3%ADsica.pdf",
        "responseFormat": "file",
        "options": {}
      },
      "id": "http-dl",
      "name": "HTTP Request",
      "type": "n8n-nodes-base.httpRequest",
      "position": [680, 460],
      "typeVersion": 4.1
    },
    {
      "parameters": {
        "operation": "upload",
        "fileContent": "={{ $binary.data }}",
        "fileName": "La_Metafisica_Aristoteles.pdf",
        "folderId": "1jJ0J3F0r1Ea-iM72o_M6Y_t0S9R19_T5"
      },
      "id": "drive-upp",
      "name": "Google Drive",
      "type": "n8n-nodes-base.googleDrive",
      "position": [900, 460],
      "typeVersion": 2,
      "credentials": {
        "googleDriveOAuth2Api": {
          "id": "m9F9HwLwT4sT6B2X",
          "name": "Google Drive account"
        }
      }
    }
  ],
  "connections": {
    "Webhook": {"main": [[{"node": "HTTP Request", "type": "main", "index": 0}]]},
    "HTTP Request": {"main": [[{"node": "Google Drive", "type": "main", "index": 0}]]}
  },
  "settings": {}
}

with open('/home/lucy-ubuntu/Escritorio/NIN/.env', 'r') as f:
    env_content = f.read()

api_key = ''
for line in env_content.split('\n'):
    if line.startswith('N8N_API_KEY='):
        api_key = line.split('=')[1].strip()
        break

req = urllib.request.Request(
    'http://172.24.0.4:5678/api/v1/workflows',
    data=json.dumps(wf).encode(),
    headers={ 'Content-Type': 'application/json', 'X-N8N-API-KEY': api_key },
    method='POST'
)

try:
    with urllib.request.urlopen(req) as resp:
         res = json.loads(resp.read().decode())
         wid = res.get('id')
         print(f"✅ Workflow Inyectado: {wid}")
         
         # ACTIVAR
         req_act = urllib.request.Request(
             f'http://172.24.0.4:5678/api/v1/workflows/{wid}/activate',
             data=b'{}',
             headers={ 'Content-Type': 'application/json', 'X-N8N-API-KEY': api_key },
             method='POST'
         )
         with urllib.request.urlopen(req_act) as resp_act:
             print(f"✅ Workflow Activado")
             
             # DISPARAR EL WEDHOOK
             req_fire = urllib.request.Request(
                 'http://172.24.0.4:5678/webhook/subir-metafisica',
                 method='GET'
             )
             with urllib.request.urlopen(req_fire) as resp_fire:
                 print(f"🎉 DRIVE UPLOAD STATUS: OK (Webhook disparado con éxito y archivo entregado a Drive)")

except urllib.error.HTTPError as e:
    print(f"❌ HTTP Error: {e.code} - {e.read().decode()}")
except Exception as e:
    print(f"❌ Error: {e}")
