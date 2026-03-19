# Host Post-Clone Audit y Mapa de Servicios

Auditoría integral del host Ubuntu tras el clonado a nuevo disco, enfocado en descubrir rutas rotas, mounts fantasma o servicios caídos.

## 1. Mapa de Almacenamiento y Montaje
- **Disco Físico Actual**: `nvme0n1` (1.9T).
- **Montajes Principales**:
  - `/` montado en `/dev/nvme0n1p2` (ext4) usando `UUID=fc7ea308-093e-4408-90c7-4aed32580245`.
  - `/boot/efi` montado en `/dev/nvme0n1p1` (vfat) usando `UUID=C8AD-5CC2`.
- **Veredicto de Storage**: `SANO`. El `/etc/fstab` coincide con los UUIDs reales del NVME. No hay referencias zombis a `sdb` (el disco original del cual se clonó) más allá de los comentarios de instalación originales ("was on /dev/sdb2 during curtin installation").

## 2. Mapa de Servicios Systemd
- **Servicios Fallidos System**: Ninguno (`0 loaded units failed`).
- **Servicios Fallidos User**: Ninguno (`0 loaded units failed`).
- **Timers Críticos Activos**:
  - `bitnin-shadow.timer` (Activo y programado).
- **Veredicto de Systemd**: `SANO`.

## 3. Topología de Entorno (Python y Rutas)
- **Global Python**: `/home/lucy-ubuntu/Miniforge3/bin/python3` (versión `3.13.12`).
- **BitNin `.venv`**: El symlink `python` en `.venv/bin/` apunta a `python3.12`.
- **Hallazgo / Riesgo**: Desfase de entorno. El clonado retuvo la `.venv` compilada para `Python 3.12`, pero Miniforge parece haber traído o actualizado `Python 3.13`.
  - *Impacto*: Si se invoca sin el wrapper asilado o fuera del `.venv`, `bash -lc` podría inyectar `3.13` a los scripts de BitNin causando errores de importación masiva. 
- **Veredicto de Entorno**: `DUDOSO`. El uso intensivo de invocaciones directas a `/home/lucy-ubuntu/Escritorio/NIN/...` con `bash -c` palia este problema, pero queda como deuda técnica unificada.

## 4. Estado de Proyectos y Contenedores Críticos
Evaluación de dependencias periféricas que mantienen vivo el sistema:

1. **Ollama**: `SANO`.
   - Servicio `systemd` activo. Api activa en `localhost:11434`. Modelos Gemma 3 cargados.
2. **Qdrant (Memoria)**: `ROTO`.
   - **Síntoma**: No responde en `localhost:6333`. Ni está en Docker PS.
   - **Impacto BitNin**: Memoria RAG inactiva. El Analista degradará el score de convergencia forzadamente hacia abajo al no encontrar análogos, aunque *no crasheará* el sistema gracias a las excepciones controladas.
3. **N8N (Data Ingest)**: `ROTO` (Para BitNin).
   - **Síntoma**: Hay un contenedor `doctor_lucy_n8n` vivo mapeando al puerto `6969`, sin embargo, el puerto canónico para ingestión de flujos de BitNin reportado frecuentemente en el runtime (`localhost:5688`) *no* responde en HTTP.
   - **Impacto BitNin**: No habrá flujo de nuevas narrativas ni episodios automatizados entrantes si dependían de esta instancia.

## 5. Resumen de Post-Auditoría
El host clonado **arranca de forma limpia y transparente** en el plano del Sistema Operativo (`host sano`). Sin embargo, **el ecosistema de backend auxiliar quedó parcialmente quebrado en el proceso clonatorio** (`host con incidentes`):
- Los motores vectoriales (Qdrant) y de ingesta (N8n instanciado) cayeron, no se auto-iniciaron, o no existen en el stack actual de docker activo.
- La `.venv` carga pasivos de versionado cruzado con Miniforge (`3.12` vs `3.13`).

### Fixes Mínimos Sugeridos a Futuro (No invasivos para 29R hoy)
1. Levantar el contenedor Qdrant en el puerto 6333 usando los volúmenes recuperados si los hay, o instanciarlo vacío (el sistema se auto-reparará degradando score hasta la próxima inyección RAG).
2. Revisar el archivo compose/arranque docker del `n8n` específico de la fase y asegurar que se exponga al `5688` donde el supervisor lo espera.
3. A largo plazo (Post S1), purgar y reconstruir la `.venv` sincronizando con el binario local base.
