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
# Lista de cuentas para rotación (Round-Robin)
CUENTAS_SMTP = [
    {"user": "profesordiegofilosofia@gmail.com", "pass": "PON_AQUI_EL_PASSWORD_DE_APLICACION_1"},
    {"user": "profedefilodiego@gmail.com", "pass": "PON_AQUI_EL_PASSWORD_DE_APLICACION_2"},
]

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
            part3 = MIMEApplication(f.read(), Name="Mi_Curriculum.pdf")
            part3['Content-Disposition'] = 'attachment; filename="Mi_Curriculum.pdf"'
            msg.attach(part3)
    except Exception as e:
        w_log(f"❌ Error al adjuntar CV: {e}")
        return "ERROR_ARCHIVO"
        
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(origen_user, origen_pass)
        server.sendmail(origen_user, destino, msg.as_string())
        server.quit()
        return "OK"
    except smtplib.SMTPAuthenticationError as e:
        w_log(f"❌ Autenticación fallida o bloqueo para {origen_user}: {e}")
        return "AUTH_ERROR"
    except Exception as e:
        w_log(f"❌ Error SMTP en envío: {e}")
        return "SMTP_ERROR"

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
    
    cuentas_activas = CUENTAS_SMTP.copy()
    
    # 2. Iterar y Enviar (Round-Robin Dinámico)
    i = 0
    while i < total:
        if not cuentas_activas:
            w_log("❌ Todas las cuentas SMTP fallaron o fueron bloqueadas. Abortando.")
            notify_telegram("❌ Abortando envío: Todas las cuentas SMTP fueron bloqueadas.")
            break
            
        fila = colegios_lista[i]
        nombre = str(fila.get('nombre del colegio', 'Colegio')).strip()
        email_raw = str(fila.get('Mail', '')).strip()
        
        if not email_raw or email_raw.lower() == 'nan':
            w_log(f"⚠️ Saltando [{nombre}] por falta de email.")
            i += 1
            continue
            
        destino = email_raw.replace(" / ", ", ").replace("/", ", ")
        
        # Selección de cuenta rotativa
        cuenta_actual = cuentas_activas[i % len(cuentas_activas)]
        origen_user = cuenta_actual['user']
        origen_pass = cuenta_actual['pass']
        
        w_log(f"✉️ [{i+1}/{total}] Enviando a {nombre} ({destino}) desde [{origen_user}]...")
        
        resultado = enviar_correo(origen_user, origen_pass, destino, nombre)
        
        if resultado == "OK":
            w_log("✅ Enviado.")
            notify_telegram(f"✅ [{i+1}/{total}] Enviado a: {nombre} (Vía {origen_user})")
            
            # Pausa Anti-Spam
            if i + 1 < total:
                delay = random.randint(50, 110)
                w_log(f"🛑 Pausa anti-spam de {delay} segundos... (Próximo cambio de cuenta)")
                time.sleep(delay)
            i += 1  # Avanzar al siguiente
            
        elif resultado == "AUTH_ERROR":
            w_log(f"⚠️ Removiendo cuenta {origen_user} de la rotación por fallo de autenticación.")
            notify_telegram(f"⚠️ Cuenta {origen_user} bloqueada/rebotada. Cambiando de cuenta para {nombre}...")
            cuentas_activas.remove(cuenta_actual)
            # NO incrementamos 'i', el while loop volverá a intentar enviar al mismo colegio con la siguiente cuenta
            
        else: # SMTP_ERROR o ERROR_ARCHIVO
            w_log(f"❌ Falló el envío a: {nombre}. Saltando colegio.")
            notify_telegram(f"❌ [{i+1}/{total}] FALLÓ envío a: {nombre} (Vía {origen_user})")
            i += 1  # Avanzar al siguiente asumiendo que el colegio fue el problema
            time.sleep(10)

    w_log("🏁 Todos los envíos procesados o cancelados.")
    notify_telegram("🏁 ¡Misión finalizada! Se procesó la lista completa de colegios o se agotaron las cuentas.")

if __name__ == "__main__":
    principal()
