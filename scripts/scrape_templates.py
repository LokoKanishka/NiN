import os
import requests
import json
import base64
from typing import List

# Configuración
REPOS = [
    {"owner": "Zie619", "repo": "n8n-workflows", "path": ""},
    {"owner": "enescingoz", "repo": "awesome-n8n-templates", "path": ""}
]
BASE_OUTPUT_DIR = "/home/lucy-ubuntu/Escritorio/NIN/workflows/reservoir/"

def get_files_from_github(owner: str, repo: str, path: str = "") -> List[dict]:
    """Obtiene la lista de archivos de un repo de GitHub recursivamente."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error accediendo a {url}: {response.status_code}")
        return []
    
    files = []
    items = response.json()
    for item in items:
        if item["type"] == "file" and item["name"].endswith(".json"):
            files.append(item)
        elif item["type"] == "dir":
            files.extend(get_files_from_github(owner, repo, item["path"]))
    return files

def download_file(url: str, output_path: str):
    """Descarga un archivo JSON desde una URL raw."""
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        return True
    return False

def main():
    if not os.path.exists(BASE_OUTPUT_DIR):
        os.makedirs(BASE_OUTPUT_DIR)

    for config in REPOS:
        owner = config["owner"]
        repo = config["repo"]
        print(f"Explorando {owner}/{repo}...")
        
        repo_dir = os.path.join(BASE_OUTPUT_DIR, f"{owner}_{repo}")
        if not os.path.exists(repo_dir):
            os.makedirs(repo_dir)
            
        files = get_files_from_github(owner, repo)
        print(f"Encontrados {len(files)} flujos .json en {repo}")
        
        count = 0
        for file in files:
            file_name = file["name"]
            # Sanitizar nombre de archivo si es necesario
            download_url = file["download_url"]
            dest_path = os.path.join(repo_dir, file_name)
            
            if download_file(download_url, dest_path):
                print(f"Descargado: {file_name}")
                count += 1
                if count >= 50: # Límite por batch para no saturar
                    print("Batch completado (50 archivos).")
                    break
        print(f"Total descargado de {repo}: {count}")

if __name__ == "__main__":
    main()
