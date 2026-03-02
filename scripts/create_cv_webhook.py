import os
import requests
from dotenv import load_dotenv

load_dotenv("/home/lucy-ubuntu/Escritorio/NIN/.env")
KEY = os.getenv("N8N_API_KEY")
HEADERS = {"X-N8N-API-KEY": KEY, "Content-Type": "application/json"}
URL = "http://172.24.0.4:5678/api/v1/workflows"

wf = {
  "name": "Webhook: Enviar CV Escolar Individual",
  "active": True,
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "send-cv-api",
        "responseMode": "lastNode",
        "options": {}
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [0, 0]
    },
    {
      "parameters": {
        "fileSelector": "/home/lucy-ubuntu/Escritorio/NIN/gmail_cv/data/Mi_Curriculum.pdf",
        "dataPropertyName": "adjunto_cv"
      },
      "name": "Cargar CV Local",
      "type": "n8n-nodes-base.readBinaryFiles",
      "typeVersion": 1,
      "position": [200, 0]
    },
    {
      "parameters": {
        "fromEmail": "chatjepetex4@gmail.com",
        "toEmail": "={{ $node['Webhook'].json['body']['to'] }}",
        "subject": "Postulación docente - Diego Leonardo Succi",
        "text": "={{ $node['Webhook'].json['body']['text'] }}",
        "html": "={{ $node['Webhook'].json['body']['html'] }}",
        "options": {
          "appendAttachements": false,
          "attachments": "adjunto_cv"
        }
      },
      "name": "Enviar Correo SMTP",
      "type": "n8n-nodes-base.emailSend",
      "typeVersion": 2,
      "position": [400, 0],
      "credentials": {
        "smtp": {
          "id": "Vjq1Vkk3HMWqCsCO",
          "name": "SMTP account"
        }
      }
    }
  ],
  "connections": {
    "Webhook": {
      "main": [ [ {"node": "Cargar CV Local", "type": "main", "index": 0} ] ]
    },
    "Cargar CV Local": {
      "main": [ [ {"node": "Enviar Correo SMTP", "type": "main", "index": 0} ] ]
    }
  }
}

r = requests.post(URL, json=wf, headers=HEADERS)
if r.status_code == 200:
    print("✅ Workflow creado con éxito.")
else:
    print(f"❌ Error al crear workflow: {r.status_code} - {r.text}")
