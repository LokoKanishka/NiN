# BitNin Code Surface Map

Mapeo de las superficies de control y _entrypoints_ ejecutivos para gestionar y acceder a los módulos de BitNin. Proporciona una visión estructural del enrutamiento sistémico para su mantenimiento.

## 1. Consola Operativa Central (Operador y Mantenimiento)

### `./bin/bitnin-ctl`
- **Ubicación:** `NIN/bin/bitnin-ctl` (Ejecutable wrapper).
- **Rol:** Entrypoint universal oficial del Operador.
- **Riesgo por uso incorrecto:** Ninguno sustancial en comandos read-only (`status`, `doctor`, `briefing`). Riesgo severo con intenciones directas en `week-close` si dictamina en base a evidencia falsa.
- **Frecuencia:** Diaria.

## 2. Herramientas Administrativas de Infraestructura

### `./scripts/bootstrap.sh`
- **Rol:** Aprovisionamiento local (Copia de configuraciones base, establecimiento de .gitignore y setups de Carpetas).
- **Criticidad:** Alta (Asegurar entorno limpio). Usado solo 1 vez por despliegue de Host.

### `./scripts/scheduler_ctl.sh`
- **Rol:** Entrypoint del Cron Job. `install`, `start`, `stop`, `status` para el Demonio de Linux.
- **Frecuencia:** Solo para _Deployments_ e intervenciones críticas donde Systemd resbala (`stale_data` inamovible).

### `./scripts/ops_backup.sh` y `ops_restore.sh`
- **Rol:** Gestión de DR (Disaster Recovery).
- **Riesgo:** Un Restore borra de cuajo los datos de la Sesión Viva actual (Volatilidad) arrojando en su lugar los de un tarball anterior. Frecuencia de uso excepcional.

## 3. Entrypoint Autónomo (Scheduler/Supervisor)

### `services/bitnin_observability/supervisor.py` -> `tick()`
- **Rol:** Routine principal del daemon de supervisión. 
- **Modo:** Ejecución en fondo (`bitnin-shadow.timer`). Orquesta el `BitNinRuntimeRunner` cada ciclo.
- **Interacción Externa:** Nula. Actúa blindado mediante el cerroco de `bitnin_supervisor.lock`. Solo lo llama Systemd automatizado o una invocación explícita de testing de dev.

## 4. Entrypoint del Pipeline y Orquestación Interna

### `services/bitnin_runtime_runner/runner.py`
- **Rol:** Motor general orquestador ("The Brain"). Construye e invoca los pasos atómicos del vertical: llama secuencialmente Analyst → ShadowRunner → HitlRunner → ExecGuardRunner → Observability.
- **Nivel de Aislamiento:** Diseñado como pieza transaccional de pura lógica centralizada. El Supervisor le encomienda las iteraciones de la fase en vigor.

## 5. Entrypoints de Soporte de Contexto

### `bitnin_active_memory/indexer.py` (Cron Externo Potencial)
- **Rol:** Genera la "Carga RAG". Lee las intenciones aprobadas, eventos operativos pasados, y empuja matrices de datos vectorizadas contra Qdrant Collections (`localhost:6333`).
- **Exposición:** Solo el dev lo invoca en los re-procesamientos batch, o se programa en tuberías `batch/` de reconstrucción estructural.

### `datasets/` o Integración N8N (Pipeline GDELT)
- **Rol:** Ingresan la sangre viva a la arquitectura (noticias de narrativas y barras de mercado base) depositando archivos JSONl en `runtime/datasets/`. No forma parte del Main Loop (se procesan de forma "side-car").
