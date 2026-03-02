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

EXCEL_PATH = "/home/lucy-ubuntu/Escritorio/NIN/gmail_cv/data/colegios de prueba cv.xltx"
CV_PATH = "/home/lucy-ubuntu/Escritorio/NIN/gmail_cv/data/Mi_Curriculum.pdf"
SMTP_USER = "chatjepetex4@gmail.com"
SMTP_PASS = "pwytqpcqmqwhsjgw"

# Credenciales Telegram (NiN-Demon Sync)
TG_TOKEN = "8235094378:AAG-EKXPVUjmXGTZQigDIxyciWqlNMsJ8oA"
DIEGO_ID = 5154360597

def notify_telegram(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": DIEGO_ID, "text": message}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        w_log(f"⚠️ Error al notificar Telegram: {e}")

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

def enviar_correo(server, origen, destino, colegio):
    txt, html = armar_textos(colegio)
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "CV.PROF.FILOSOFÍA"
    msg['From'] = origen
    msg['To'] = destino

    # Partes de texto
    part1 = MIMEText(txt, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)
    
    # Adjuntar PDF
    try:
        with open(CV_PATH, "rb") as f:
            part3 = MIMEApplication(f.read(), Name="Mi_Curriculum.pdf")
            part3['Content-Disposition'] = 'attachment; filename="Mi_Curriculum.pdf"'
            msg.attach(part3)
    except Exception as e:
        w_log(f"❌ Error al adjuntar CV: {e}")
        return False
        
    try:
        server.sendmail(origen, destino, msg.as_string())
        return True
    except Exception as e:
        w_log(f"❌ Error SMTP: {e}")
        return False

TARGET_TIME = datetime.time(0, 45, 0)

def principal():
    w_log("🚀 Iniciando Script Nativo de Envío de CVs (vía Smtplib) [ENVÍO COMPLETO + TELEGRAM]...")
    notify_telegram("🚀 Script de CVs iniciado. Esperando a las 00:45 para la tanda completa.")
    
    # 0. Esperar hasta las 00:45
    ahora = datetime.datetime.now()
    target_dt = datetime.datetime.combine(ahora.date(), TARGET_TIME)
    
    if ahora > target_dt:
        if ahora.hour > 12:
            target_dt += datetime.timedelta(days=1)
            wait_seconds = (target_dt - ahora).total_seconds()
            w_log(f"⏳ Esperando {wait_seconds:.0f} segundos hasta las 00:45 de mañana...")
            time.sleep(wait_seconds)
        else:
            w_log("⚠️ La hora objetivo (00:45) ya pasó esta madrugada. Avanzando de inmediato.")
    else:
        wait_seconds = (target_dt - ahora).total_seconds()
        w_log(f"⏳ Esperando {wait_seconds:.0f} segundos hasta las 00:45...")
        time.sleep(wait_seconds)
    
    w_log("⏱️ ¡Hora alcanzada! Leyendo base de datos...")
    notify_telegram("⏱️ ¡Hora alcanzada! Iniciando envío a la lista de colegios...")
    
    # 1. Leer Excel
    try:
        df = pd.read_excel(EXCEL_PATH)
    except Exception as e:
        w_log(f"❌ Error leyendo Excel: {e}")
        notify_telegram(f"❌ Error crítico leyendo Excel: {e}")
        return

    colegios_lista = df.to_dict(orient='records')
    total = len(colegios_lista)
    w_log(f"📚 {total} colegios detectados en la lista.")
    
    # 2. Conectar a Gmail SMTP
    w_log("🔐 Conectando al servidor SMTP de Google...")
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        w_log("✅ Conexión SMTP establecida.")
    except Exception as e:
        w_log(f"❌ Fallo crítico de Autenticación SMTP: {e}")
        notify_telegram(f"❌ Fallo de Autenticación SMTP: {e}")
        return

    # 3. Iterar y Enviar
    for i, fila in enumerate(colegios_lista, 1):
        nombre = str(fila.get('nombre del colegio', 'Colegio')).strip()
        email_raw = str(fila.get('Mail', '')).strip()
        
        if not email_raw or email_raw.lower() == 'nan':
            w_log(f"⚠️ Saltando [{nombre}] por falta de email.")
            continue
            
        destino = email_raw.replace(" / ", ", ").replace("/", ", ")
        
        w_log(f"✉️ [{i}/{total}] Enviando a {nombre} ({destino})...")
        
        exito = enviar_correo(server, SMTP_USER, destino, nombre)
        
        if exito:
            w_log("✅ Enviado.")
            notify_telegram(f"✅ [{i}/{total}] Enviado a: {nombre}")
        else:
            notify_telegram(f"❌ [{i}/{total}] FALLÓ envío a: {nombre}")
        
        # 4. Pausa Anti-Spam
        if i < total:
            delay = random.randint(50, 70)
            w_log(f"🛑 Pausa anti-spam de {delay} segundos...")
            time.sleep(delay)

    try:
        server.quit()
    except:
        pass
    w_log("🏁 Todos los envíos procesados.")
    notify_telegram("🏁 ¡Misión cumplida! Se procesó la lista completa de colegios.")

if __name__ == "__main__":
    principal()
