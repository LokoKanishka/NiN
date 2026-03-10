import os
import time
import requests
from bs4 import BeautifulSoup
import urllib.parse
from dotenv import load_dotenv

BASE_DIR = "/home/lucy-ubuntu/Escritorio/NIN"
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Credenciales Telegram (desde .env)
TG_TOKEN = os.getenv("TG_TOKEN")
DIEGO_ID = int(os.getenv("TG_CHAT_ID", "0"))

if not TG_TOKEN:
    print("❌ FATAL: TG_TOKEN no está definido en .env. Abortando.")
    import sys; sys.exit(1)

LIBGEN_SEARCH_URL = "https://libgen.is/search.php?req={query}&open=0&res=25&view=simple&phrase=1&column=def"

def search_libgen(query):
    encoded_query = urllib.parse.quote_plus(query)
    url = LIBGEN_SEARCH_URL.format(query=encoded_query)
    print(f"Buscando en LibGen: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        table = soup.find("table", class_="c")
        if not table:
            return None
            
        rows = table.find_all("tr")[1:] # Skip header
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 10:
                id_val = cols[0].text.strip()
                author = cols[1].text.strip()
                title_col = cols[2]
                title = title_col.text.strip().split('\n')[0].strip() # Clean up extras
                publisher = cols[3].text.strip()
                year = cols[4].text.strip()
                lang = cols[6].text.strip()
                ext = cols[8].text.strip()
                
                # Enlace de descarga (espejo 1)
                mirror_td = cols[9]
                mirror_link = mirror_td.find("a")
                if mirror_link:
                    link = mirror_link["href"]
                    if lang.lower() == "spanish" or lang.lower() == "es":
                        return {"id": id_val, "author": author, "title": title, "ext": ext, "link": link}
                        
        # Repetir sin filtro de idioma por si no está marcado
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 10:
                mirror_td = cols[9]
                mirror_link = mirror_td.find("a")
                if mirror_link:
                    return {"id": cols[0].text.strip(), "title": cols[2].text.strip(), "ext": cols[8].text.strip(), "link": mirror_link["href"]}
                    
    except Exception as e:
        print(f"Error buscando {query}: {e}")
    return None

def get_direct_download(mirror_url):
    print(f"Obteniendo enlace directo desde: {mirror_url}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        response = requests.get(mirror_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        h2 = soup.find('h2')
        if h2 and h2.find('a'):
            return h2.find('a')['href']
    except Exception as e:
        print(f"Error scraping mirror: {e}")
    return None

def download_book(url, filename):
    print(f"Descargando {filename} desde {url}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=60)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Descarga completada.")
        return True
    except Exception as e:
        print(f"Fallo la descarga: {e}")
        return False

def send_to_telegram(filepath, caption=""):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument"
    print(f"Enviando {filepath} a Telegram...")
    try:
        with open(filepath, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': DIEGO_ID, 'caption': caption}
            response = requests.post(url, files=files, data=data, timeout=120)
            if response.status_code == 200:
                print("Enviado exitosamente a Telegram.")
                return True
            else:
                print(f"Error de Telegram: {response.text}")
    except Exception as e:
        print(f"Error enviando telegram: {e}")
    return False

def send_msg(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": DIEGO_ID, "text": text}
    try: requests.post(url, json=payload, timeout=10)
    except: pass

def procesar_libro(query_search, filename_base):
    send_msg(f"🔍 [NiN] Buscando libro: {query_search}...")
    book = search_libgen(query_search)
    if not book:
        print(f"No encontrado: {query_search}")
        send_msg(f"❌ [NiN] No pude encontrar '{filename_base}' en Library Genesis de forma automatizada.")
        return
        
    print(f"Encontrado: {book['title']} ({book['ext']})")
    send_msg(f"✔️ Encontré una versión de {filename_base}. Extrayendo binarios...")
    
    download_url = get_direct_download(book['link'])
    if not download_url:
        print("No se encontró link directo.")
        send_msg(f"❌ Error extrayendo link directo para '{filename_base}'.")
        return
        
    filepath = os.path.join(BASE_DIR, f"{filename_base}.{book['ext']}")
    if download_book(download_url, filepath):
        send_to_telegram(filepath, f"📖 Aquí está: {filename_base}")
        # Limpiar
        os.remove(filepath)
    else:
        send_msg(f"❌ Falló la descarga de '{filename_base}'.")

if __name__ == "__main__":
    import sys
    # Se instalará bs4 si falta
    procesar_libro("Lipman Suki", "Suki - Matthew Lipman")
    time.sleep(2)
    procesar_libro("Lipman Sharp Escribir", "Escribir, como y por que - Lipman Sharp")
