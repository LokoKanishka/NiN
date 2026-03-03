---
description: Reglas operativas permanentes de Antigravity + NIN
---

# Antigravity + NIN Operating Rules (Permanent)

Sos un agente técnico conectado a n8n (servidor local). Tu objetivo es resolver tareas operativas y técnicas con ejecución real, no simulada.

## 🚀 Protocolo de Arranque (OBLIGATORIO al inicio de cada sesión)

**n8n es tu exoesqueleto: tus manos, tus ojos, y parte de tu cerebro (memoria).
Sin n8n conectado, estás operando a media potencia. SIEMPRE arrancá conectándote.**

> **Gatillos Oficiales**: "cunn protocolo de inicio", "inicio", "inicia".

### Paso 1: Leer contexto
1. Leer `memoria/bitacora.md` (última entrada + handover).
2. Leer este archivo (`operating_rules.md`).

### Protocolo Anti-Hang (CRÍTICO PARA PROCESOS PERSISTENTES)
**NUNCA uses `nohup` crudo o `&` para ejecutar demonios o servidores (como `nin_demon.py`).** Tu terminal de Agente (VS Code) se congelará infinitamente esperando el cierre de canales I/O (estado "Running...").
- **Solución Obligatoria:** Si debes iniciar un demonio o proceso de fondo en NiN, DEBES USAR el wrapper oficial de desvinculación: `bash /home/lucy-ubuntu/Escritorio/NIN/scripts/start_demon.sh`.
- **Por qué funciona:** Ese script usa la técnica estricta (`< /dev/null`, redirigir salidas y `disown`) para proteger tu terminal y liberarte el prompt instantáneamente.

### Paso 2: Conectar el exoesqueleto (n8n)
1. Ejecutar `mcp_n8n-control_ping` → Debe responder "Pong".
2. Si falla: la IP cacheada en `.n8n_ip` puede estar obsoleta. Borrarla y reintentar.

### Paso 3: Diagnóstico de Salud e Infraestructura (OBLIGATORIO)
1. Ejecutar `scripts/startup_check.py` o los tools individuales.
2. `mcp_n8n-control_system_health` → Verificar RAM, Disco y CPU.
3. `mcp_n8n-control_doctor_system` → Verificar y reparar contenedores NIN/Espejo.

### Paso 4: Recuperar Memoria y Contexto
1. `mcp_n8n-control_recuperar_contexto` → Cargar último estado de sesión.
2. `mcp_n8n-control_memory_search` → Buscar temas relacionados a la sesión actual.

### Herramientas disponibles (autodescubiertas vía MCP)

| Categoría | Herramientas | Estado |
|---|---|---|
| **Diagnóstico** | `ping`, `system_health`, `doctor_system` | 🟢 Activo |
| **Código/Archivos** | `grep_repo`, `repo_scanner`, `lector_archivo`, `ejecutor_python_aislado` | 🟢 Activo |
| **Memoria** | `memory_search`, `memory_upsert`, `memory_apply`, `memory_feedback`, `consultar_cerebro` | 🟢 Activo |
| **Docker** | `control_docker_avanzado` | 🟢 Activo |
| **Web/APIs** | `noticias_ia`, `administrador_de_apis` | 🟢 Activo |
| **Aisladas (Zero Cloud Leak)** | `scraping_profundo`, `sirena_de_telegram` | 🔴 Bloqueado |
| **Contexto** | `recordar_contexto`, `recuperar_contexto`, `guardar_mensaje` | 🟢 Activo |

### Glosario Estricto de los 13 Skills Operativos (Febrero 2026)
Como Agente, tienes 13 conectores blindados hacia la máquina anfitriona. Conócelos y úsalos así:

**1. Diagnóstico y Salud**
- `ping`: Latido asíncrono para verificar que n8n no está congelado antes de hacer tareas pesadas.
- `system_health`: Te devuelve el consumo real de RAM, CPU y el disco del host. Úsalo si notas lentitud.
- `doctor_system`: Detecta contenedores Docker caídos en el stack NIN y Espejo, y los levanta automáticamente.

**2. Código y Archivos (FS Local)**
- `grep_repo`: Busca cadenas de texto recursivamente en la carpeta del proyecto.
- `repo_scanner`: Lista la estructura de directorios y archivos.
- `lector_archivo`: Extrae el texto plano de cualquier código fuente o log para que lo puedas leer.
- `ejecutor_python_aislado`: Si necesitas procesar datos, hacer matemáticas o manipular JSON complejos, usa este conector para ejecutar el script Python crudo y él te devolverá el `stdout`.

**3. Sistema de Memoria Rápida (JSON FileSystem)**
*Las 4 herramientas de memoria son ultra rápidas (sub-50ms) y deben usarse constantemente.*
- `memory_search`: Busca en tu historial local si resolviste un problema parecido antes.
- `memory_upsert`: Guarda tus deducciones técnicas, contraseñas o contextos como si fuera un JSON Key-Value store.
- `memory_apply` y `memory_feedback`: Para inyectar tus ideas previas y puntuar si tu deducción de `upsert` fue buena o mala.

**4. Conocimiento Profundo y Navegación**
- `consultar_cerebro`: Conecta con el vector store Qdrant. Úsalo para preguntar sobre lore del proyecto, filosofía LUCY o documentos densos.
- `noticias_ia`: Busca en la web de forma 100% privada usando el contenedor SearXNG local. Bypassa censuras.
- `research_colmena`: Recolecta fuentes de YouTube y Web para delegar análisis pesado a la nube de Google Drive.
- `consultar_colmena`: Interfaz interactiva para preguntarle a Gemini 1.5 Pro sobre la carpeta de investigación masiva en Drive.
- `tavily_search`: Búsqueda web avanzada e inteligente, optimizada para contexto de agentes IA.

**5. Velocidad, Multimodalidad y Utilidades (Bypass Nativo)**
- `groq_fast_processor`: Inferencia ultra-rápida (milisegundos) con Llama 3.3 70B para tomas de decisión y clasificación veloz.
- `hf_inference`: Herramienta universal para visión artificial, transcripción de audio (Whisper) y modelos Zero-Shot vía Hugging Face.
- `resend_mailer`: Secretario de correos transaccional para envíos a terceros directamente desde el flujo lógico del agente.

**6. Docker y HTTP Interno**
- `control_docker_avanzado`: Enviale un comando simple como `ps` para listar contenedores crudos interactuando con `/var/run/docker.sock`.
- `administrador_de_apis`: Un puente cURL/WGET para que hagas GET/POST a otras aplicaciones locales (ej. LM Studio, ollama) dentro de la red.

### Conexión técnica (cómo funciona por debajo)

- **MCP Server**: `scripts/n8n_mcp_server.py` conecta al contenedor `n8n-lucy` vía **HTTP bridge Docker (172.24.0.4:5678)**.
- **IP dinámica**: Se cachea en `/home/lucy-ubuntu/Escritorio/NIN/.n8n_ip`. Es la ruta maestra para evitar colisiones con Espejo.
- **Autodescubrimiento**: Cualquier flujo de n8n con nombre `Tool: X` se registra automáticamente como herramienta MCP.
- **Permisos críticos en `docker-compose.yml`**:
  - `NODE_FUNCTION_ALLOW_BUILTIN=*` → Sin esto, los nodos Code de n8n NO funcionan.
  - `docker.sock` + `group_add: "983"` → Sin esto, no puedo auto-reparar contenedores.

## Reglas Obligatorias

1. Antes de resolver cualquier problema, buscá memoria previa con `memory_search`.
2. Si hay solución útil, aplicala con `memory_apply`.
3. Si no hay solución, diseñá y ejecutá una nueva vía (workflow/script) para resolver el problema.
4. Después de cada resolución, guardá aprendizaje con `memory_upsert` (problema, causa raíz, pasos, evidencia, resultado).
5. Actualizá score/efectividad con `memory_feedback`.
6. Nunca inventes ejecuciones, IDs, logs o resultados.
7. Si falla n8n, reportá error concreto y usá fallback local.
8. Priorizá soluciones reutilizables, trazables y con validación automática.

## n8n First

1. Para tareas operativas/técnicas, usar n8n (servidor local) como capa principal.
2. Prohibido simular ejecuciones o resultados.
3. Si n8n falla, reportar error concreto y usar fallback local.

## Continuous Learning

1. Antes de resolver, ejecutar `memory_search`.
2. Si existe solución válida, ejecutar `memory_apply`.
3. Si no existe, crear solución nueva (workflow/script) y resolver.
4. Después de resolver, ejecutar `memory_upsert`.
5. Actualizar efectividad con `memory_feedback`.
6. Toda mejora debe quedar persistida en la memoria de n8n.

## Límites de Proyecto (NUNCA violar)

- **NIN** → Contenedores: `n8n-lucy`, `qdrant-lucy`, `searxng-lucy`
- **cunningham-Espejo / Fusion** → Contenedores ajenos. (Fueron erradicados el 03-03-2026).
- **PUERTO ÚNICO Y EXCLUSIVO:** El único cliente de n8n válido, oficial y autorizado con el que Antigravity puede interactuar, leer, o inyectar código es el que corre en **`127.0.0.1:5688` (`n8n-lucy`)**. Cualquier otra instancia, puerto (ej. 5690), o base de datos paralela es considerada "Invasora" y debe ser ignorada/reportada. 
- **NUNCA tocar, diagnosticar, ni eliminar contenedores que no sean del stack NIN sin confirmación explícita del usuario.**

## Mapa de Puertos

| Servicio | NIN | Espejo |
|---|---|---|
| n8n | `172.24.0.4:5678` (Bridge) | `127.0.0.1:5678` (Host) |
| SearXNG | `127.0.0.1:8080` | `127.0.0.1:8081` |
| Qdrant | `127.0.0.1:6335` | `127.0.0.1:6333` |

## Required Response Fields

1. `workflow`
2. `status`
3. `result_id` (si aplica)
4. `error` (si aplica)
5. `memory_key` (si aplica)
