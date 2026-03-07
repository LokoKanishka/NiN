# GUÍA DE SUPERVIVENCIA NiN: Restauración Post-Formateo

Esta guía es para que mi nueva versión (Antigravity) pueda reconstruirme y ponerme en marcha rápidamente después de que formates la máquina.

## 1. Clonación y Entorno
1. Clonar este repositorio: `git clone [URL-DEL-REPO] NIN`
2. Instalar Docker y Docker Compose.
3. Asegurarse de que el archivo `.env` esté presente con las claves necesarias (ej. `N8N_JWT_SECRET`).

## 2. Restauración de Docker (n8n, Qdrant, SearxNG)
Desde la raíz del proyecto:
```bash
docker-compose up -d
```
Esto levantará el contenedor `N8N-NiN-uso-exclusivo-del-proyecto-nin` en `http://localhost:5688`.

## 3. Restauración de n8n (Búnker de Memoria)
El flujo de trabajo actual está guardado en `n8n_bunker_workflow_v3.json`.
1. Abrir n8n en `http://localhost:5688`.
2. Importar `n8n_bunker_workflow_v3.json`.
3. **IMPORTANTE**: Activar el workflow.
4. Verificar que el webhook `POST /webhook/bunker-sync` responda.

## 4. Recuperación de Memoria Histórica
NiN guarda las sincronizaciones en `data/nin_bunker_log.jsonl`. 
- Al clonar el repo, este archivo se restaurará.
- El **MegaDemon** (`scripts/nin_megademon.py`) lo leerá automáticamente al arrancar.

## 5. Arranque del MegaDemon
```bash
python3 scripts/nin_megademon.py
```
El demonio reportará: `🧠 [NiN-Búnker] Recuperando historia desde disco...` y cargará el contexto de las tareas pendientes.

## 6. Verificación de Git Hooks
Asegurarse de que el hook de git esté activo para que no se pierda nada en el futuro:
```bash
cp scripts/sync_memory_to_n8n.py .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

## 7. Infraestructura de Superpoderes (MCP)
Este proyecto usa puentes SSE para expandir mis capacidades:
1. Instalar dependencias de Node.js:
   ```bash
   npm install
   ```
2. Los servidores se lanzan bajo demanda vía `scripts/nin_mcp_bridge.js`.
3. Asegurarse de que `nin_mcp_config.json` esté en la raíz para que el host pueda cargar las herramientas.

---
*Firmado: Antigravity/NiN (Tu Copiloto de IA)*
