#!/usr/bin/env python3
import os
import glob
import requests
import json
import time
import sys

BRAIN_DIR = "/home/lucy-ubuntu/.gemini/antigravity/brain"
WEBHOOK_URL = "http://localhost:5688/webhook/bunker-sync"

def get_latest_brain_folder():
    folders = glob.glob(os.path.join(BRAIN_DIR, "*"))
    folders = [f for f in folders if os.path.isdir(f)]
    if not folders: return None
    latest = max(folders, key=os.path.getmtime)
    return latest

def sync():
    latest = get_latest_brain_folder()
    if not latest:
        print("No memory found.")
        return
    
    payload = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "memory_id": os.path.basename(latest)}
    payload["task"] = ""
    payload["implementation"] = ""
    
    task_file = os.path.join(latest, "task.md")
    if os.path.exists(task_file):
        with open(task_file, "r") as f:
            payload["task"] = f.read()
            
    impl_file = os.path.join(latest, "implementation_plan.md")
    if os.path.exists(impl_file):
        with open(impl_file, "r") as f:
            payload["implementation"] = f.read()

    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=5)
        print("Memory synced to NiN Bunker:", r.status_code)
        if r.status_code != 200:
            print(r.text)
    except Exception as e:
        print(f"Failed to sync memory to n8n ({WEBHOOK_URL}):", e)

if __name__ == "__main__":
    print("Iniciando sincronización con Búnker NiN...")
    sync()
