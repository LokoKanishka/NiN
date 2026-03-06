import os
import time
import requests
import random
import datetime
import pandas as pd
from dotenv import load_dotenv

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Cargar variables si existen
load_dotenv("/home/lucy-ubuntu/Escritorio/NIN/.env")

EXCEL_PATH = "/home/lucy-ubuntu/Escritorio/NIN/verticals/gmail_cv/data/1 3 14.xltx"
CV_PATH = "/home/lucy-ubuntu/Escritorio/NIN/verticals/gmail_cv/data/CV.PROF.FILOSOFIA.pdf"
# Cuenta fija solicitada por el usuario
CUENTAS_SMTP = [
    {"user": "profedefilodiego@gmail.com", "pass": "kwnwqhdtkqlopsac"},
]

# Instituciones ya enviadas exitosamente según logs previos (para evitar duplicados hoy)
ALREADY_SENT = {
    "INST. MATER DOLOROSA", 
    "INSTITUTO SCHILLER", 
    "CENTRO EDUCATIVO BUENOS AIRES", 
    "INST NUESTRA SRA DE LA MISERICORDIA",
    "INSTITUTO GRIEGO ATENÁGORAS I",
    "INSTITUTO CAROLINA ESTRADA DE MARTINEZ",
    "COLEGIO BUENOS AIRES S.R.L",
    "INSTITUTO PRIVADO REGINA VIRGINUM",
    "ESCUELA SCHOLEM ALEIJEM",
    "INSTITUTO ECOS ESCUELA SECUNDARIA",
    "COLEGIO PAIDEIA",
    "INSTITUTO SAN ROQUE",
    "INSTITUTO COMUNICACIONES",
    "INSTITUTO PRIVADO DAVID WOLFSOHN",
    "BACH. POP. DE JOVENES Y ADULTOS LA DIGNIDAD",
    "BACH. POP. DE JOVENES Y ADULTOS VILLA CRESPO-NUESTRAMERICA",
    "CFP DE LA ESC. TECSON SRL",
    "EAG (ESCUELA DE ARTE GASTRONOMICO)",
    "CENTRO DE FORMACIÓN PROFESIONAL ESCUELA ARGENTINA DE SOCORRISMO Y SALVAMENTO ACUATICO S.A  (EASSA)",
    "COLEGIO OLIVOS DEL SOL",
    "COLEGIO SAN ANTONIO",
    "INSTITUTO JOSÉ MANUEL ESTRADA",
    "COLEGIO SAN NICOLAS",
    "ESCUELA SAN GABRIEL",
    "COLEGIO SAN GABRIEL",
    "COLEGIO LOS MOLINOS",
    "ESCUELA JESUS EN EL HUERTO DE LOS OLIVOS",
    "INSTITUTO JESUS EN EL H. DE LOS OLIVOS",
    "INSTITUTO DE EDUCACION INTEGRAL DE MUNRO",
    # Envíos de la sesión actual 2026-03-06 (Configuración corregida)
    "COLEGIO SECUNDARIO SANTO TOMAS DE AQUINO",
    "INSTITUTO ESPAÑOL VIRGEN DEL PILAR"
}

# Credenciales Telegram (NiN-Demon Sync)
TG_TOKEN = "8235094378:AAG-EKXPVUjmXGTZQigDIxyciWqlNMsJ8oA"
DIEGO_ID = 5154360597

import threading

# URL de la Sirena n8n para desacoplo total (Blindaje Permanente)
SIRENA_URL = "http://127.0.0.1:5678/webhook/sirena-telegram"

def notify_telegram_sync(message):
    """Envío directo a Telegram para evitar dependencia de webhooks externos."""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": DIEGO_ID, "text": message}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass

def notify_telegram(message):
    """
    Blindaje Permanente NiN: Envía notificaciones a través de la Sirena
    asíncrona en n8n. El script principal es inmune a colapsos de red.
    """
    t = threading.Thread(target=notify_telegram_sync, args=(message,), daemon=True)
    t.start()

def w_log(msg):
    full_msg = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}"
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

TARGET_TIME = datetime.time(6, 15)  # Programado para las 06:15

def principal():
    w_log("🚀 Iniciando Script Nativo de Envío de CVs (vía Smtplib) [ENVÍO COMPLETO + TELEGRAM]...")
    
    if TARGET_TIME is not None:
        notify_telegram(f"🚀 Script de CVs iniciado. Esperando a las {TARGET_TIME.strftime('%H:%M')} para la tanda completa.")
        ahora = datetime.datetime.now()
        target_dt = datetime.datetime.combine(ahora.date(), TARGET_TIME)
        if ahora > target_dt:
            if ahora.hour > 12:
                target_dt += datetime.timedelta(days=1)
                wait_seconds = (target_dt - ahora).total_seconds()
                w_log(f"⏳ Esperando {wait_seconds:.0f} segundos hasta las {TARGET_TIME.strftime('%H:%M')} de mañana...")
                time.sleep(wait_seconds)
            else:
                w_log(f"⚠️ La hora objetivo ({TARGET_TIME.strftime('%H:%M')}) ya pasó esta madrugada. Avanzando de inmediato.")
        else:
            wait_seconds = (target_dt - ahora).total_seconds()
            w_log(f"⏳ Esperando {wait_seconds:.0f} segundos hasta las {TARGET_TIME.strftime('%H:%M')}...")
            time.sleep(wait_seconds)
        w_log("⏱️ ¡Hora alcanzada! Leyendo base de datos...")
        notify_telegram(f"⏱️ ¡Hora alcanzada ({TARGET_TIME.strftime('%H:%M')})! Iniciando envío a la lista de colegios...")
    else:
        w_log("⚡ Modo inmediato activado. Leyendo base de datos...")
        notify_telegram("🚀 Script de CVs iniciado en MODO INMEDIATO. Enviando a la lista de colegios...")
    
    TEST_MODE = False # Envío real activado
    TEST_EMAIL = "chatjepetex4@gmail.com" # Email de prueba (ignorado en False)
    
    # 1. Leer Excel
    try:
        # Intentamos leer sin encabezados para procesar todo, o definimos comportamiento defensivo
        df = pd.read_excel(EXCEL_PATH, header=None)
    except Exception as e:
        w_log(f"❌ Error leyendo Excel: {e}")
        notify_telegram(f"❌ Error crítico leyendo Excel: {e}")
        return

    colegios_lista = df.to_dict(orient='records')
    total = len(colegios_lista)
    w_log(f"📚 {total} colegios detectados en la lista.")
    
    cuentas_activas = CUENTAS_SMTP.copy()
    
    # 2. Iterar y Enviar (Round-Robin Dinámico)
    i = 0
    while i < total:
        if not cuentas_activas:
            w_log("❌ Todas las cuentas SMTP fallaron o fueron bloqueadas. Abortando.")
            notify_telegram("❌ Abortando envío: Todas las cuentas SMTP fueron bloqueadas.")
            break
            
        fila = colegios_lista[i]
        # Usamos índices numéricos ya que leímos con header=None
        nombre = str(fila.get(0, 'Colegio')).strip()
        email_raw = str(fila.get(1, '')).strip()
        
        # Saltar instituciones ya enviadas exitosamente
        if nombre in ALREADY_SENT:
            w_log(f"⏭️ Saltando [{nombre}] — ya enviado anteriormente.")
            i += 1
            continue
        
        # El chequeo de 'falso header' fue eliminado para evitar saltos erróneos. 
        # El parse_emails ya se encarga de validar si hay correos reales.
        
        if not email_raw or email_raw.lower() == 'nan':
            w_log(f"⚠️ Saltando [{nombre}] por falta de email.")
            i += 1
            continue
        
        emails = parse_emails(email_raw)
        if not emails:
            w_log(f"⚠️ Saltando [{nombre}] — no se encontró email válido en: {email_raw}")
            i += 1
            continue
        
        # Selección de cuenta rotativa
        cuenta_actual = cuentas_activas[i % len(cuentas_activas)]
        origen_user = cuenta_actual['user']
        origen_pass = cuenta_actual['pass']
        
        # Enviar a CADA email de esta institución
        all_ok = True
        for destino in emails:
            w_log(f"✉️ [{i+1}/{total}] Enviando a {nombre} ({destino}) desde [{origen_user}]...")
            resultado = enviar_correo(origen_user, origen_pass, destino, nombre)
            
            if resultado == "OK":
                w_log(f"✅ Enviado a {destino}.")
                notify_telegram(f"✅ [{i+1}/{total}] Enviado a: {nombre} → {destino} (Vía {origen_user})")
            elif resultado == "AUTH_ERROR":
                w_log(f"⚠️ Removiendo cuenta {origen_user} de la rotación por fallo de autenticación.")
                notify_telegram(f"⛔ CUENTA BLOQUEADA/AUTH: {origen_user}. Se retira de la rotación. Reintentando...")
                cuentas_activas.remove(cuenta_actual)
                all_ok = False
                break
            elif "Daily user sending limit exceeded" in str(resultado) or "550" in str(resultado):
                w_log(f"⚠️ Removiendo cuenta {origen_user} por alcanzar LÍMITE DIARIO.")
                notify_telegram(f"⛔ LÍMITE ALCANZADO: {origen_user}. Se retira de la rotación. Reintentando...")
                cuentas_activas.remove(cuenta_actual)
                all_ok = False
                break
            else:
                w_log(f"❌ Falló envío a {destino} de {nombre}: {resultado}")
                notify_telegram(f"❌ ERROR: No se pudo enviar a {nombre} ({destino}) vía {origen_user}.")
        
        if not all_ok and cuentas_activas:
            continue # Reintentar mismo colegio con otra cuenta
        
        # Pausa Anti-Spam entre colegios
        i += 1
        if i < total:
            delay = 60 # Delay fijo de 1 minuto solicitado
            w_log(f"🛑 Pausa anti-spam de {delay} segundos...")
            time.sleep(delay)

    w_log("🏁 Todos los envíos procesados o cancelados.")
    notify_telegram("🏁 ¡Misión finalizada! Se procesó la lista completa de colegios o se agotaron las cuentas.")

if __name__ == "__main__":
    principal()
