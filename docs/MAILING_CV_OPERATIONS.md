# Manual de Operaciones: Sistema de Envíos de CV
*Última actualización: Abril 2026*

Este documento consolida las reglas, arquitectura y parámetros del sistema de envíos masivos de currículums desarrollado y modificado a pedido del profesor Diego Leonardo Succi.

## 1. Topología del Sistema
El script principal encargado del envío se encuentra en `scripts/send_cvs.py`.

A diferencia de la red troncal que dependía de un nodo interno en N8N, este script corre de forma autónoma en el servidor local (ejecutado idealmente bajo capa de aislamiento a través de `scripts/start_demon.sh` para evitar la retención del hilo del agente).

### 1.1 Archivos Operativos
*   **Destinos (Excel)**: `verticals/gmail_cv/data/lista_produccion_colegios.xlsx`
    *   Formato esperado: `Columna 0` -> Nombre de Institución. `Columna 1` -> Emails separados por `,` o `/` o `;`.
*   **Adjunto**: `verticals/gmail_cv/data/CV.PROF.FILOSOFIA.pdf`
    *   *Nota: El nombre debe coincidir siempre de manera idéntica.*
*   **Historial Persistente**: `/tmp/cv_sent_history_v3.json` 
    *   *Nota: Mantenido en /tmp/ previendo errores de Errno 13 (Permissions) de root.*

## 2. Modos de Ejecución
Existen 2 maneras de comandar el operativo desde Antigravity:

* **Modo Aislamiento (Daemon-mode) [Recomendado]**:
  Al ejecutarse con `bash scripts/start_demon.sh send_cvs.py`, el proceso ingresa en el pool de background. Los logs se consultan leyendo stdout/stderr que el demonio escupe.
* **Modo Síncrono (Dry-Run)**:
  Se ejecuta `python scripts/send_cvs.py` directamente con la variable `DRY_RUN = True` editada en el source, para emular envío y probar conexiones.

## 3. Lógica Anti-Spam y Rotación Dinámica
Para prevenir el baneo de las cuentas y manejar el volumen de decenas o cientos de colegios de manera orgánica, se ha implementado la siguiente arquitectura de derivación de carga:

1.  **Deduplicación Estricta**: Al momento de arrancar, el script lee el historial. Cualquier colegio que figure allí como `OK` jamás recibirá un segundo correo.
2.  **Round Robin (Espejo)**: El script está instruido para iterar de la Lista de Cuentas usando el mecanismo simple de Módulo (`%`). Ejemplo: _Mail 1 = Cuenta A, Mail 2 = Cuenta B, Mail 3 = Cuenta A_. 
3.  **Pausado Asimétrico**: Entre envíos, antes de cambiar de destintario, el motor se duerme al azar entre **30 y 40 segundos**.
4.  **Auto Re-Enrutado (Failover)**: Si Google API responde `AuthError`, `LimitExceeded` o error genérico (códigos 535, 554, limit, quota, blocked):
    - La cuenta infractora queda descalificada de la RAM (`cuentas_activas.remove(cuenta_fallida)`).
    - El script **atrapa el mismo mail fallido y lo re-intenta** al instante usando la siguiente cuenta sana.

## 4. Credenciales
Las llaves se encuentran en el archivo `.env` maestro del root path. Las cuentas operativas conectadas como "Contraseñas de Aplicación" para rotación son (a partir del escaneo histórico profundo):

- `profedefilodiego@gmail.com`
- `profesordiegofilosofia@gmail.com`

*(La llave de chatjepetex4@gmail.com está expresamente prohibida a nivel hardcode para que no participe de la colmena).*
