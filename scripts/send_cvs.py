# --- NIN STATUS: STABILIZED ---
# Authority: scripts/send_cvs.py (Current Operational Authority)
# This script handles the daily CV mailing with persistence, locking, and safety.

import os
import sys
import time
import json
import random
import datetime
import threading
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dotenv import load_dotenv

# --- CONFIGURACIÓN DE RUTA Y AMBIENTE ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
load_dotenv(os.path.join(BASE_DIR, ".env"))

# --- CONSTANTES OPERATIVAS ---
EXCEL_PATH = os.path.join(BASE_DIR, "verticals/gmail_cv/data/lista_produccion_colegios.xlsx")
CV_PATH = os.path.join(BASE_DIR, "verticals/gmail_cv/data/CV.PROF.FILOSOFIA.pdf")
HISTORY_PATH = os.path.join(BASE_DIR, "runtime/cv_sent_history.json")
LOCK_FILE = "/tmp/send_cvs.lock"

# --- SEGURIDAD Y CREDENCIALES ---
DRY_RUN = False  # Cambiar a True para simular sin enviar mails
SMTP_USER = os.getenv("SMTP_USER_DIEGO", "profedefilodiego@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS_DIEGO") # Tomado de .env

CUENTAS_SMTP = [
    {"user": SMTP_USER, "pass": SMTP_PASS},
]

# Credenciales Telegram NiN (desde .env)
TG_TOKEN = os.getenv("TG_TOKEN")
DIEGO_ID = os.getenv("TG_CHAT_ID", "0")
SIRENA_URL = "http://127.0.0.1:5678/webhook/sirena-telegram"

# --- UTILIDADES DE PERSISTENCIA Y LOCK ---

def acquire_lock():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0) # Verifica si el proceso existe
            return False, pid
        except (ValueError, ProcessLookupError, OSError):
            pass # El PID no es válido o el proceso murió
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    return True, os.getpid()

def release_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

def load_history():
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_to_history(colegio, email, status):
    history = load_history()
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "colegio": colegio,
        "colegio_norm": normalize_name(colegio),
        "email": email,
        "status": status
    }
    history.append(entry)
    # Crear carpeta runtime si no existe
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def normalize_name(name):
    import unicodedata
    if not isinstance(name, str): return ""
    # Normalizar a minúsculas, quitar espacios y acentos
    s = name.lower().strip()
    s = "".join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return s

# --- NOTIFICACIONES ---

def notify_telegram_sync(message):
    """Envío vía Sirena NiN con fallback directo (best-effort)."""
    # 1. Intentar vía Sirena (n8n Webhook)
    try:
        import requests
        r = requests.post(SIRENA_URL, json={"mensaje": message}, timeout=3)
        if r.ok:
            return
    except Exception:
        pass
    
    # 2. Fallback Directo
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": DIEGO_ID, "text": f"NiN-Alert: {message}"}
    try:
        import requests
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass

def notify_telegram(message):
    """Notificación no bloqueante."""
    t = threading.Thread(target=notify_telegram_sync, args=(message,), daemon=True)
    t.start()

def w_log(msg):
    full_msg = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(full_msg)

def armar_textos(colegio):
    # Texto Plano
    texto_plano = (
        f"A las autoridades de la institución {colegio}:\n\n"
        "Me dirijo a ustedes para poner a disposición mi currículum vitae, a fin de que lo tengan en cuenta ante futuras oportunidades en la institución. Cuento con título habilitante, experiencia en el manejo de grupos y amplia disponibilidad horaria.\n\n"
        "Atentamente:\n"
        "Prof. Diego Leonardo Succi"
    )
    
    # HTML
    texto_html = (
        f"A las autoridades de la institución <b>{colegio}</b>:<br><br>"
        "Me dirijo a ustedes para poner a disposición mi currículum vitae, a fin de que lo tengan en cuenta ante futuras oportunidades en la institución. Cuento con título habilitante, experiencia en el manejo de grupos y amplia disponibilidad horaria.<br><br>"
        "Atentamente:<br>"
        "Prof. Diego Leonardo Succi"
    )
    return texto_plano, texto_html

def parse_emails(email_raw):
    """Parsea una celda que puede tener múltiples emails separados por / ; Y etc."""
    import re
    # Normalizar separadores comunes
    normalized = email_raw.replace(' Y ', ';').replace(' y ', ';')
    normalized = normalized.replace(' / ', ';').replace('/', ';')
    normalized = normalized.replace(', ', ';').replace(',', ';')
    parts = [e.strip() for e in normalized.split(';') if e.strip()]
    # Filtrar solo lo que parece un email válido
    valid = [e for e in parts if '@' in e and '.' in e]
    return valid

def enviar_correo(origen_user, origen_pass, destino, colegio):
    txt, html = armar_textos(colegio)
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "CV.PROF.FILOSOFÍA"
    msg['From'] = origen_user
    msg['To'] = destino

    # Partes de texto
    part1 = MIMEText(txt, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)
    
    # Adjuntar PDF
    try:
        with open(CV_PATH, "rb") as f:
            part3 = MIMEApplication(f.read(), Name="CV.PROF.FILOSOFIA.pdf")
            part3['Content-Disposition'] = 'attachment; filename="CV.PROF.FILOSOFIA.pdf"'
            msg.attach(part3)
            w_log(f"📎 CV adjuntado correctamente: {CV_PATH}")
    except Exception as e:
        w_log(f"❌ Error al adjuntar CV: {e}")
        return "ERROR_ARCHIVO"
        
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(origen_user, origen_pass)
        server.sendmail(origen_user, [destino], msg.as_string())
        server.quit()
        return "OK"
    except smtplib.SMTPAuthenticationError as e:
        w_log(f"❌ Autenticación fallida o bloqueo para {origen_user}: {e}")
        return "AUTH_ERROR"
    except Exception as e:
        w_log(f"❌ Error SMTP en envío: {e}")
        return str(e)

TARGET_TIME = None # Cambiar a un objeto time (ej. datetime.time(6, 15)) para programar

def principal():
    # 0. Check Lock
    success, pid = acquire_lock()
    if not success:
        print(f"❌ ERROR: El script ya está corriendo (PID: {pid}). Abortando para evitar duplicados.")
        sys.exit(1)
    
    try:
        w_log("🚀 Iniciando Script de Envío de CVs (NiN Stabilized)...")
        if DRY_RUN: w_log("🧪 MODO DRY-RUN ACTIVADO: No se enviarán correos reales.")

        if not SMTP_PASS and not DRY_RUN:
            w_log("❌ ERROR: No se encontró SMTP_PASS_DIEGO en el ambiente (.env). Abortando.")
            sys.exit(1)

        # 1. Programación o Inmediato
        if TARGET_TIME is not None:
            w_log(f"⏰ Programado para las {TARGET_TIME.strftime('%H:%M')}.")
            # ... (lógica de espera simplificada) ...
            ahora = datetime.datetime.now()
            target_dt = datetime.datetime.combine(ahora.date(), TARGET_TIME)
            if ahora > target_dt: target_dt += datetime.timedelta(days=1)
            wait_seconds = (target_dt - ahora).total_seconds()
            w_log(f"⏳ Esperando {wait_seconds:.0f} segundos...")
            time.sleep(wait_seconds)
        
        # 2. Leer Datos e Historial
        try:
            df = pd.read_excel(EXCEL_PATH, header=None)
        except Exception as e:
            w_log(f"❌ Error leyendo Excel: {e}")
            return

        history = load_history()
        # Crear conjuntos de comparación rápida
        sent_names = {entry['colegio_norm'] for entry in history}
        sent_combos = {(entry['colegio_norm'], entry['email'].lower()) for entry in history}
        
        colegios_lista = df.to_dict(orient='records')
        total = len(colegios_lista)
        w_log(f"📚 {total} registros cargados de {os.path.basename(EXCEL_PATH)}")

        cuentas_activas = CUENTAS_SMTP.copy()
        stats = {"sent": 0, "skipped": 0, "failed": 0}
        current_session_sent = set()

        # 3. Iterar y Enviar
        for i, fila in enumerate(colegios_lista):
            if not cuentas_activas and not DRY_RUN:
                w_log("❌ Sin cuentas SMTP disponibles. Abortando.")
                break

            nombre = str(fila.get(0, '')).strip()
            email_raw = str(fila.get(1, '')).strip()
            nombre_norm = normalize_name(nombre)

            if not nombre or not email_raw or email_raw.lower() == 'nan':
                continue

            # --- DEDUPLICACIÓN ---
            # 1. Contra el historial persistente
            if nombre_norm in sent_names:
                w_log(f"⏭️  [Deduplicado-Historial] {nombre}")
                stats["skipped"] += 1
                continue
            
            # 2. Contra la sesión actual (duplicados en el mismo Excel)
            if nombre_norm in current_session_sent:
                w_log(f"⏭️  [Deduplicado-Sesión] {nombre}")
                stats["skipped"] += 1
                continue

            emails_to_send = parse_emails(email_raw)
            valid_emails = [e for e in emails_to_send if (nombre_norm, e.lower()) not in sent_combos]
            
            if not valid_emails:
                w_log(f"⏭️  [Deduplicado-Email Historial] {nombre}")
                stats["skipped"] += 1
                continue

            # --- ENVÍO ---
            cuenta = cuentas_activas[stats["sent"] % len(cuentas_activas)]
            
            success_at_least_one = False
            for destino in valid_emails:
                w_log(f"✉️  [{i+1}/{total}] Enviando a {nombre} ({destino})...")
                
                if DRY_RUN:
                    resultado = "OK"
                    time.sleep(0.1)
                else:
                    resultado = enviar_correo(cuenta['user'], cuenta['pass'], destino, nombre)
                
                if resultado == "OK":
                    success_at_least_one = True
                    w_log(f"✅ Éxito.")
                    if not DRY_RUN: save_to_history(nombre, destino, "OK")
                else:
                    w_log(f"❌ Fallo: {resultado}")
                    if "Daily user sending limit exceeded" in str(resultado):
                        cuentas_activas.remove(cuenta)
                        break

            if success_at_least_one:
                stats["sent"] += 1
                current_session_sent.add(nombre_norm)
                notify_telegram(f"✅ Enviado: {nombre}")
                # Pausa Anti-Spam
                if i < total - 1:
                    delay = random.randint(50, 110)
                    w_log(f"⏳ Pausa de {delay}s...")
                    time.sleep(delay)
            else:
                stats["failed"] += 1

        w_log(f"🏁 FIN DE MISIÓN. Resumen: Enviados: {stats['sent']}, Saltados: {stats['skipped']}, Fallidos: {stats['failed']}")
        notify_telegram(f"🏁 Tanda finalizada. Enviados: {stats['sent']}, Saltados: {stats['skipped']}")

    finally:
        release_lock()

if __name__ == "__main__":
    principal()
