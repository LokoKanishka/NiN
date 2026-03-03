import os
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Ruta del archivo descargado
file_path = '/tmp/metafisica_final_ssl.pdf'
if not os.path.exists(file_path):
    # Fallback al crudo Wget
    file_path = '/tmp/metafisica.pdf'

# Buscamos la llave de servicio de Colmena/Google Drive (usualmente en la raíz o secrets)
key_paths = [
    '/home/lucy-ubuntu/Escritorio/NIN/secrets/google_drive_credentials.json',
    '/home/lucy-ubuntu/Escritorio/NIN/keys/gdrive.json',
    '/home/lucy-ubuntu/.n8n/google_drive.json',
    '/home/lucy-ubuntu/Escritorio/NIN/gdrive_service_account.json'
]

creds_path = None
for p in key_paths:
    if os.path.exists(p):
        creds_path = p
        break

if not creds_path:
    print(f"❌ Error crítico: No se encontraron credenciales Service Account OAuth2 en rutas conocidas.")
    print("Usaremos el plan D final: Un Push vía Webhook asíncrono puro a un WF nuevo de n8n diseñado desde LA INTERFAZ y exportado limpio por nosotros.")
    sys.exit(1)

print(f"✅ Usando credenciales GDrive en: {creds_path}")

SCOPES = ['https://www.googleapis.com/auth/drive.file']
creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
service = build('drive', 'v3', credentials=creds)

folder_id = '1jJ0J3F0r1Ea-iM72o_M6Y_t0S9R19_T5'
file_metadata = {
    'name': 'La_Metafisica_Aristoteles_FINAL.pdf',
    'parents': [folder_id]
}
media = MediaFileUpload(file_path, mimetype='application/pdf')

try:
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"🎉 DRIVE UPLOAD STATUS: OK (Archivo subido a API nativa. ID: {file.get('id')})")
except Exception as e:
    print(f"❌ Error Subiendo: {e}")
