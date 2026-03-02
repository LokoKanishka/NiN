import os
import time
import requests
import random
import datetime
import pandas as pd
from dotenv import load_dotenv

load_dotenv("/home/lucy-ubuntu/Escritorio/NIN/.env")

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

load_dotenv("/home/lucy-ubuntu/Escritorio/NIN/.env")

EXCEL_PATH = "/home/lucy-ubuntu/Escritorio/NIN/gmail_cv/data/colegios de prueba cv.xltx"
CV_PATH = "/home/lucy-ubuntu/Escritorio/NIN/gmail_cv/data/Mi_Curriculum.pdf"
SMTP_USER = "chatjepetex4@gmail.com"
SMTP_PASS = "pwytqpcqmqwhsjgw" # App Password limpia

def w_log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

def armar_textos(colegio):
    # Texto Plano
    texto_plano = (
        f"A las autoridades de la institución {colegio}:\n\n"
        "Me dirijo a ustedes para poner a disposición mi currículum vitae a fin de que lo tengan en cuenta en futuras oportunidades en la institución. Poseo título habilitante, experiencia en el manejo de grupos y una amplia disponibilidad horaria.\n\n"
        "Atte: Profesor Diego Leonardo Succi."
    )
    
    # HTML
    texto_html = (
        f"A las autoridades de la institución <b>{colegio}</b>:<br><br>"
        "Me dirijo a ustedes para poner a disposición mi currículum vitae a fin de que lo tengan en cuenta en futuras oportunidades en la institución. Poseo título habilitante, experiencia en el manejo de grupos y una amplia disponibilidad horaria.<br><br>"
        "Atte: Profesor Diego Leonardo Succi."
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

import time
import random
import datetime

TARGET_TIME = datetime.time(23, 40, 0)

def principal():
    w_log("🚀 Iniciando Script Nativo de Envío de CVs (vía Smtplib) [ENVÍO COMPLETO]...")
    
    # 0. Esperar hasta las 23:40
    ahora = datetime.datetime.now()
    target_dt = datetime.datetime.combine(ahora.date(), TARGET_TIME)
    
    if ahora > target_dt:
        w_log("⚠️ La hora objetivo (23:40) ya pasó el día de hoy. Avanzando de inmediato.")
    else:
        wait_seconds = (target_dt - ahora).total_seconds()
        w_log(f"⏳ Esperando {wait_seconds:.0f} segundos hasta las 23:40...")
        time.sleep(wait_seconds)
    
    w_log("⏱️ ¡Hora alcanzada! Leyendo base de datos...")
    
    # 1. Leer Excel
    try:
        df = pd.read_excel(EXCEL_PATH)
    except Exception as e:
        w_log(f"❌ Error leyendo Excel: {e}")
        return

    colegios_lista = df.to_dict(orient='records')
    total = len(colegios_lista)
    w_log(f"📚 {total} colegios detectados en la lista.")
    
    # 2. Conectar a Gmail SMTP
    w_log("🔐 Conectando al servidor SMTP de Google...")
    try:
        # Requerimos el server persistente para no loguear 15 veces
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        w_log("✅ Conexión SMTP establecida.")
    except Exception as e:
        w_log(f"❌ Fallo crítico de Autenticación SMTP: {e}")
        return

    # 3. Iterar y Enviar
    for i, fila in enumerate(colegios_lista, 1):
        nombre = str(fila.get('nombre del colegio', 'Colegio')).strip()
        email_raw = str(fila.get('Mail', '')).strip()
        
        if not email_raw or email_raw.lower() == 'nan':
            w_log(f"⚠️ Saltando [{nombre}] por falta de email.")
            continue
            
        # Formatear email por si hay múltiples
        destino = email_raw.replace(" / ", ", ").replace("/", ", ")
        
        w_log(f"✉️ [{i}/{total}] Enviando a {nombre} ({destino})...")
        
        exito = enviar_correo(server, SMTP_USER, destino, nombre)
        
        if exito:
            w_log("✅ Enviado.")
        
        # 4. Pausa Anti-Spam (solo si no es el último)
        if i < total:
            delay = random.randint(50, 70)
            w_log(f"🛑 Pausa anti-spam de {delay} segundos...")
            time.sleep(delay)

    # Cerrar conexión
    try:
        server.quit()
    except:
        pass
    w_log("🏁 Todos los envíos procesados.")

if __name__ == "__main__":
    principal()

