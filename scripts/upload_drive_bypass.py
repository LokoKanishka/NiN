import sys
import os
import io
import json
import urllib.request
import urllib.error

print("🔍 Extrayendo Metafísica de Aristóteles (Versión Universia/Cervantes)...")
public_url = "https://biblioteca.org.ar/libros/133604.pdf" 

try:
    req = urllib.request.Request(public_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as response:
        pdf_data = response.read()
        print(f"✅ Libro Descargado: {len(pdf_data) / 1024 / 1024:.2f} MB")
except Exception as e:
    print(f"❌ Error descargando PDF principal: {e}")
    # Fallback ultra-seguro
    public_url = "https://www.imprentanacional.go.cr/editorialdigital/libros/literatura%20universal/la_metafisica_edincr.pdf"
    print(f"🔄 Intentando Fallback: {public_url}")
    try:
        req = urllib.request.Request(public_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            pdf_data = response.read()
            print(f"✅ Libro Descargado (Fallback): {len(pdf_data) / 1024 / 1024:.2f} MB")
    except Exception as e2:
        print(f"❌ Fallback fallido: {e2}")
        sys.exit(1)

tmp_path = "/tmp/metafisica_aristoteles.pdf"
with open(tmp_path, "wb") as f:
    f.write(pdf_data)

print(f"🚀 Creando workflow síncrono para inyectar {tmp_path} a Drive...")

with open('/home/lucy-ubuntu/Escritorio/NIN/.env', 'r') as f:
    env_content = f.read()

api_key = ''
for line in env_content.split('\n'):
    if line.startswith('N8N_API_KEY='):
        api_key = line.split('=')[1].strip()
        break

wf = {
  "name": "Bypass: Subir Libro PDF",
  "nodes": [
    {
      "parameters": {},
      "id": "start-node-1",
      "name": "On clicking 'execute'",
      "type": "n8n-nodes-base.manualTrigger",
      "typeVersion": 1,
      "position": [240, 240]
    },
    {
      "parameters": {
        "command": "cat /tmp/metafisica_aristoteles.pdf | base64 -w 0"
      },
      "id": "read-pdf-base64",
      "name": "Leer PDF (Base64)",
      "type": "n8n-nodes-base.executeCommand",
      "typeVersion": 1,
      "position": [460, 240]
    },
    {
       "parameters": {
          "mode": "jsonToBinary",
          "convertAllData": False,
          "sourceKey": "stdout",
          "destinationKey": "data",
          "options": {
             "fileName": "Aristoteles_Metafisica.pdf",
             "mimeType": "application/pdf"
          }
       },
       "id": "binary-node",
       "name": "Convert To Binary",
       "type": "n8n-nodes-base.binaryData",
       "typeVersion": 1,
       "position": [680, 240]
    },
    {
      "parameters": {
        "operation": "upload",
        "fileContent": "={{ $binary.data }}",
        "fileName": "Aristoteles_Metafisica.pdf",
        "folderId": "1jJ0J3F0r1Ea-iM72o_M6Y_t0S9R19_T5"
      },
      "id": "drive-node",
      "name": "Google Drive",
      "type": "n8n-nodes-base.googleDrive",
      "typeVersion": 2,
      "position": [900, 240],
      "credentials": {
        "googleDriveOAuth2Api": {
          "id": "m9F9HwLwT4sT6B2X",
          "name": "Google Drive account"
        }
      }
    }
  ],
  "connections": {
    "On clicking 'execute'": {"main": [[{"node": "Leer PDF (Base64)", "type": "main", "index": 0}]]},
    "Leer PDF (Base64)": {"main": [[{"node": "Convert To Binary", "type": "main", "index": 0}]]},
    "Convert To Binary": {"main": [[{"node": "Google Drive", "type": "main", "index": 0}]]}
  },
  "active": False
}

req_upload = urllib.request.Request(
    'http://172.24.0.4:5678/api/v1/workflows',
    data=json.dumps(wf).encode(),
    headers={'Content-Type': 'application/json', 'X-N8N-API-KEY': api_key},
    method='POST'
)

try:
    with urllib.request.urlopen(req_upload) as resp:
         res = json.loads(resp.read().decode())
         wid = res.get('id')
         print(f"✅ Workflow creado: {wid}")
         
         print(f"Ejecutando Workflow {wid}...")
         req_exec = urllib.request.Request(
             f'http://172.24.0.4:5678/api/v1/workflows/{wid}/execute',
             data=b'{}',
             headers={'Content-Type': 'application/json', 'X-N8N-API-KEY': api_key},
             method='POST'
         )
         with urllib.request.urlopen(req_exec) as resp_exec:
             exec_res = json.loads(resp_exec.read().decode())
             print(f"🎉 ¡Libro Enviado a Google Drive! Status: {exec_res.get('finished')}")
except Exception as e:
    print(f"❌ Error fatal: {e}")
