import sqlite3
import json
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import os
from dotenv import load_dotenv

load_dotenv("/home/lucy-ubuntu/Escritorio/NIN/.env")

# Password / Key
n8n_key = os.getenv("N8N_ENCRYPTION_KEY")

def decrypt_n8n(encrypted_data):
    try:
        data = encrypted_data.split(':')
        b64_data = data[0]
        iv = data[1]
        auth_tag = data[2]

        cipher_text = base64.b64decode(b64_data)
        nonce = base64.b64decode(iv)
        tag = base64.b64decode(auth_tag)
        
        # En n8n, la clave de encriptación suele ser un MD5 o PBKDF2 de la N8N_ENCRYPTION_KEY
        # Forma moderna de n8n: uses crypto.scryptSync() or aes-256-gcm directly?
        # En versiones recientes usa hash MD5 to 32 bytes... 
        
        print(f"Encrypted data split: {len(cipher_text)} bytes cypher, {len(nonce)} bytes IV")
        return b64_data
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    conn = sqlite3.connect('/home/lucy-ubuntu/Escritorio/NIN/n8n_db.sqlite')
    c = conn.cursor()
    c.execute("SELECT name, type, data FROM credentials_entity WHERE id='Vjq1Vkk3HMWqCsCO'")
    row = c.fetchone()
    print("Found:", row[0], row[1])
    print("Encrypted payload:", row[2])
    conn.close()
