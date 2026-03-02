import pyautogui
import time
import os
import sys
import cv2
import numpy as np

# Configuración
CHECK_INTERVAL = 2  # Segundos entre capturas
SKIP_AD_TEXT = ["Saltar", "Skip", "Saltar anuncio"]
PLAY_KEYS = ['space', 'k']

def find_and_click_skip():
    """
    Busca el botón 'Saltar anuncio' dinámicamente.
    YouTube suele tener un botón con fondo oscuro y texto claro, o viceversa.
    """
    try:
        # Captura de pantalla
        screen = pyautogui.screenshot()
        img_rgb = np.array(screen)
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        
        # En lugar de template matching fijo, buscaremos el rectángulo 
        # característico del botón de Skip en la zona inferior derecha.
        h, w = img_gray.shape
        region_x = int(w * 0.7)  # 70% del ancho
        region_y = int(h * 0.7)  # 70% del alto
        roi = img_gray[region_y:, region_x:]
        
        # Umbral para detectar el botón (suele ser gris/blanco sobre fondo oscuro)
        _, thresh = cv2.threshold(roi, 200, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            x, y, cw, ch = cv2.boundingRect(cnt)
            # El botón de skip suele tener un ratio de aspecto 3:1 o 2:1 y tamaño moderado
            if 100 < cw < 300 and 30 < ch < 100:
                print(f"🎯 Posible botón de salto detectado en {region_x + x}, {region_y + y}")
                pyautogui.click(region_x + x + cw//2, region_y + y + ch//2)
                return True
        
        # Fallback ciego: Click en zona probable si el anuncio es imbatible visualmente
        # (Muchas personas usan adblockers, pero aquí estamos automatizando el click nativo)
        
    except Exception as e:
        print(f"❌ Error en búsqueda de botón: {e}")
    return False

def ensure_play():
    """
    Intenta detectar si el video está pausado (botón play grande al centro).
    """
    try:
        # Si no hay movimiento en el centro de la pantalla, intentamos 'k'
        # Pero más seguro es enviar 'k' cada cierto tiempo si no estamos en anuncio
        pass
    except:
        pass

if __name__ == "__main__":
    print("🚀 YouTube Watchdog v1.0 [NiN-Vision] iniciado...")
    print("Monitoreando pantalla cada 2 segundos...")
    last_skip = 0
    try:
        while True:
            skipped = find_and_click_skip()
            if skipped:
                last_skip = time.time()
                time.sleep(1) # Esperar transición
                pyautogui.press('k') # Asegurar play tras skip
            
            # Si pasaron 10s desde el último skip, asegurar que no esté pausado
            if time.time() - last_skip > 10:
                # Comprobar si el mouse no se ha movido (el usuario no está operando)
                pass # Lógica de play automático opcional aquí
                
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\n🛑 Watchdog detenido.")
