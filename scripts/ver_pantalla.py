import pyautogui
import os
import time
import sys

def take_screenshot(output_path="/tmp/vision_nin.png"):
    """
    Captura la pantalla actual del host NiN.
    Requiere que el entorno X11 de Linux esté accesible.
    """
    try:
        # Asegurar que el directorio de salida existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Capturar pantalla
        screenshot = pyautogui.screenshot()
        screenshot.save(output_path)
        
        file_size = os.path.getsize(output_path)
        print(f"✅ Captura exitosa: {output_path} ({file_size} bytes)")
        return True
    except Exception as e:
        print(f"❌ Error capturando pantalla: {e}")
        return False

if __name__ == "__main__":
    path = "/tmp/vision_nin.png"
    if len(sys.argv) > 1:
        path = sys.argv[1]
    
    take_screenshot(path)
