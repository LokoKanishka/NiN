from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import subprocess
import os

class LaunchHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/play':
            query = urllib.parse.parse_qs(parsed.query)
            url = query.get('url', [''])[0]
            if url:
                try:
                    # Forzar variables de entorno gráficas por si acaso
                    env = os.environ.copy()
                    env['DISPLAY'] = ':0'
                    
                    # Llamada REAL 100% nativa sin nsenter ni cgroup hacks
                    # -P default es el perfil Lucy Chat interno
                    subprocess.Popen(
                        ['firefox', '-P', 'default', url],
                        env=env,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )

                    # Simular pulsación de tecla "k" (Play/Pause en YouTube)
                    # Esperamos 5 segundos a que cargue la pestaña y renderice el reproductor
                    # Esto salta directamente la restricción de AutoPlay
                    subprocess.Popen(
                        ['bash', '-c', 'sleep 5 && xdotool search --onlyvisible --name "Mozilla Firefox" windowactivate --sync key k'],
                        env=env,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'OK')
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f'Error: {e}'.encode())
            else:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    port = 9999
    server = HTTPServer(('0.0.0.0', port), LaunchHandler)
    print(f"YouTube Launcher Service escuchando en el puerto {port}")
    server.serve_forever()
