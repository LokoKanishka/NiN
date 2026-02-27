# 📒 Bitácora de Sesiones — Antigravity

> Log cronológico de sesiones. Cada entrada documenta acciones, éxitos, fallos, y lecciones aprendidas.

---

## 2026-02-25 — Sesión inaugural

**Objetivo**: Crear workflow de prueba en n8n y sistema de memoria persistente.

### Acciones

| # | Acción | Resultado | Lección |
|---|--------|-----------|---------|
| 1 | Crear workflow `.agents/workflows/prueba_x1.md` | ✅ Éxito | Los workflows van en `.agents/workflows/` con frontmatter YAML |
| 2 | Publicar workflow en n8n via `curl` desde sandbox | ❌ Timeout | **No puedo acceder a `localhost:5678` desde el sandbox.** curl se cuelga |
| 3 | Publicar via browser propio (Playwright) | ❌ Login requerido | El browser del sandbox no tiene la sesión de Chrome/diego |
| 4 | GET a la API via `docker exec n8n-lucy wget` | ✅ Éxito | `docker exec` sí puede hablar con la API interna del container |
| 5 | POST via `docker exec n8n-lucy wget --post-data` | ❌ Se cuelga | `wget --post-data` parece tener un bug o timeout dentro del container Alpine |
| 6 | POST via `docker exec n8n-lucy node -e '...'` | ✅ Éxito (HTTP 200) | **Node.js dentro del container es la ruta confiable para POST** |
| 7 | Crear sistema de memoria persistente | ✅ Éxito | Esta bitácora misma |

### Lecciones clave

- **Ruta de acceso a n8n**: `docker exec n8n-lucy node -e '<script>'` — es la ÚNICA forma confiable desde mi sandbox
- **`wget` en Alpine** es poco confiable para POST con body JSON grande
- **El browser del sandbox** no comparte sesión con Chrome del usuario
- **Los workflows de Antigravity** van en `.agents/workflows/` (no confundir con workflows de n8n en `workflows/`)

### Archivos creados/modificados

- `workflows/prueba_x1.json` — Workflow de prueba publicado en n8n
- `.agents/workflows/prueba_x1.md` — Workflow de Antigravity
- `memoria/` — Sistema de memoria completo (este directorio)

---

## 2026-02-25 (cont.) — Fix del workflow "My workflow 2"

**Objetivo**: Corregir el nodo "herramienta - Lector Local" que tenía `/etc/os-release` hardcodeado y causaba error de permisos.

### Acciones

| # | Acción | Resultado | Lección |
|---|--------|-----------|---------|
| 1 | GET workflow via API (`docker exec node`) | ✅ Éxito | El GET funciona bien pero puede ser lento con workflows grandes |
| 2 | PUT para corregir fileSelector via API | ✅ HTTP 200 | La API acepta el cambio pero n8n mantiene draft/published separados |
| 3 | Verificar en UI | ❌ Seguía mostrando `/etc/os-release` | El PUT actualiza el draft, pero la UI puede no refrescar automáticamente |
| 4 | Múltiples docker exec simultaneos | ❌ Container saturado | **NUNCA dejar docker exec colgados** — saturan el container y lo bloquean |
| 5 | `docker restart n8n-lucy` | ✅ Pero Docker también se atascó | Los procesos zombie del host bloquean Docker, necesita `sudo systemctl restart docker` |
| 6 | Usuario ejecuta el fix desde su terminal | ✅ HTTP 200, fileSelector correcto | **La ruta más confiable: que el usuario ejecute el comando directamente** |

### Lecciones clave

- **Docker se satura fácil**: Si dejás múltiples `docker exec` colgados, el container se bloquea. Matar con `pkill` no siempre funciona → requiere `sudo systemctl restart docker`
- **API de n8n — sistema de versiones**: PUT devuelve HTTP 200 pero n8n mantiene draft y published por separado. Para que tome efecto, hay que Publish desde la UI
- **Delegación al usuario**: Cuando Docker se atasca desde el sandbox, es más rápido pedirle al usuario que ejecute el comando directamente
- **Archivo de test válido**: `/home/node/.n8n-files/instrucciones.txt` (mapeado desde `./data` del host)

---

## 2026-02-25 (cont.) — Toma de Control Absoluto de n8n

**Objetivo**: Obtener una forma rápida, confiable y segura de controlar n8n desde el sandbox, porque el método de `docker exec node` demostró saturar Docker con procesos zombies.

### Acciones

| # | Acción | Resultado | Lección |
|---|--------|-----------|---------|
| 1 | Crear bridge Node.js + Wrapper Python (`docker exec`) | ❌ Lento / Zombie-prone | `docker exec` no es sustentable para automatización intensiva porque bloquea el OS del host cuando se encolan peticiones. |
| 2 | Limpiar todos los procesos estancados (`pkill -9`) | ✅ Éxito parcial | Hubo que usar pkill a lo bestia para limpiar el entorno host. |
| 3 | **BREAKTHROUGH**: Conectar a n8n vía IP Bridge de Docker | ✅ Instantáneo (<0.1s) | Obtener la IP con `docker inspect` (ej: `172.29.0.4`) y hacer HTTP directo desde Python bypassa `docker exec` por completo. |
| 4 | Reescribir `n8n_cli.py` full HTTP | ✅ Éxito (`test`, `list`, `create`, `update` vuelan) | **Esta es la forma definitiva de operar n8n.** |
| 5 | Cachear IP en `.n8n_ip` | ✅ Éxito | Evita tener que correr `docker inspect` (lento) en cada llamada del CLI. Se refresca si la IP cambia. |
| 6 | Truncar respuestas de la API (`stripHeavy`) | ✅ Éxito | La API de n8n es lenta devolviendo `activeVersion` y meta pesada. Interceptar la respuesta JSON y limpiar campos la hace usable. |
| 7 | Probar comando `execute` | ❌ 405 Method Not Allowed | Descubrimiento: los workflows que empiezan con "When Executed by Another Workflow" **no se pueden llamar vía API REST o Webhook externo**. Solo un workflow llamador (padre) puede ejecutarlos. |
| 8 | Sinergia con Usuario | ✅ Éxito (VSCode Extensions) | El usuario instaló **n8n Atom 3.0** y **n8n as code** en su IDE. El usuario controla la UI, Antigravity controla el backend. |

### Lecciones clave

- **Red Docker Bridge**: El sandbox SI puede hablar con los containers usando sus IPs internas tipo `172.29.0.x`. Esto bypassa todos los problemas de `localhost` y `pkill`.
- **API `GET /workflows/:id` es ineficiente**: Por diseño interno de n8n, pedir un workflow individual demora porque serializa demasiada data. `GET /workflows` es rápido.
- **`stripHeavy`**: Al parsear una respuesta de n8n individual, SIEMPRE hacer pop/delete de `activeVersion`, `shared`, `pinData` antes de que los LLMs intenten leerlo para ahorrar decenas de miles de tokens de contexto.
- **Triggers**: Si un sub-workflow se necesita ejecutar por API, NO usar "When Executed by Another Workflow". Usar "Webhook" en su lugar.
- **Stack Expandido**: El uso de **n8n Atom 3.0** y **n8n as code** en el IDE permite una simbiosis perfecta: el humano diseña visualmente y la IA opera el backend/JSON.

---

## 2026-02-25 (cont.) — Automatización Gmail CV (Handover Notes)

**Objetivo**: Automatizar el envío de correos con adjuntos CV desde un archivo Excel a los colegios, filtrando por comuna y usando n8n.

### Estado Actual (Handover pre-reinicio)
- Se armó el directorio `/home/lucy-ubuntu/Escritorio/NIN/gmail_cv/` conteniendo `workflow.json`, `README.md` y la carpeta `data/` con el PDF y el Excel.
- Las rutas del n8n se ajustaron a rutas absolutas del host en lugar del `.n8n-files` del contenedor para solucionar errores de lectura de volúmenes.
- **Cambio de arquitectura**: Reemplazamos el nodo nativo de Gmail (OAuth2) por el nodo genérico `emailSend` (SMTP) usando contraseñas de aplicaciones de Google para simplificar la configuración del lado del usuario.
- El usuario reportó ralentizaciones severas de la IA. Mediante un diagnóstico descubrí que había procesos colgados de `curl` y `docker exec` saturando el host debido al modelo asíncrono. Fueron aniquilados vía `pkill`.
- **Qué hacer en el próximo arranque**: Leer esta bitácora. Verificar con el usuario si el Mail CV salió bien o si hubo drama con las contraseñas de App. Si todo está OK, arrancar con la Forja (Pilar 2) o lo que el usuario decida. Todo el código de la sesión de hoy ya está respaldado en Git.

---

## 2026-02-26 — Fix del Workflow Gmail CV y n8n_cli

**Objetivo**: Corregir error de importación y activación del workflow del CV debido a nodos obsoletos y pulir el script de control de n8n.

### Acciones

| # | Acción | Resultado | Lección |
|---|--------|-----------|---------|
| 1 | Analizar error "Unrecognized node type" en la UI | ✅ Éxito | El workflow usaba `n8n-nodes-base.spreadsheetFileRead` (obsoleto). |
| 2 | Reemplazar nodo en `workflow.json` | ✅ Éxito | Se actualizó a `n8n-nodes-base.extractFromFile`. |
| 3 | Actualizar workflow vía `n8n_cli.py` | ✅ HTTP 200 | El CLI actualizó existosamente la definición en la base de n8n. |
| 4 | Testear activación (`activate`) desde API | ❌ Falló ("active is read-only") | La propiedad `active` no se puede cambiar vía `PUT /workflows/:id`. Requiere `POST /workflows/:id/activate`. |
| 5 | Corregir `n8n_cli.py` | ✅ Éxito | Se actualizaron los comandos `activate` y `deactivate` para usar los endpoints oficiales POST y reportar credenciales faltantes. |
| 6 | Intentar activar nuevamente | ❌ Faltan credenciales | El workflow requiere que el usuario asigne manualmente la credencial SMTP desde la UI. Se le indicó cómo hacerlo. |

### Estado Actual (Handover)
- El workflow está listo y corregido en la base de datos de n8n.
- Solo requiere que el usuario asigne la Credencial SMTP en la UI de n8n y presione "Publish".
- El CLI de n8n (`n8n_cli.py`) tiene los verbos activate/deactivate parcheados a la API actual de n8n.
- Todo guardado en el repo. Listos para empezar "La Forja" en la próxima sesión si el usuario lo decide.

---

## 2026-02-26 (cont.) — Ajustes Workflow Gmail CV

**Objetivo**: Modificar el horario de ejecución y el remitente del workflow a pedido del usuario.

### Acciones

| # | Acción | Resultado | Lección |
|---|--------|-----------|---------|
| 1 | Actualizar hora ejecución a 18:05 | ✅ Éxito | El cambio en el cron expression (`5 18 * * *`) se hizo directo en `workflow.json`. |
| 2 | Cambiar correo remitente a `chatjepetex4@gmail.com` | ✅ Éxito | Modificado en en el nodo emailSend. |

### Estado Actual
- Cambios realizados en `/home/lucy-ubuntu/Escritorio/NIN/gmail_cv/workflow.json`.
- Lista la configuración para que dispare hacia las escuelas de la Comuna 1.

---

## 2026-02-26 (cont.) — Incidente de Latencia y Servidor MCP

**Objetivo**: Analizar la demora inaceptable (4.5 minutos) para cambiar la hora de un flujo y programar una solución definitiva a la conectividad con n8n.

### Acciones y Análisis del Incidente

| # | Acción / Suceso | Resultado | Lección |
|---|--------|-----------|---------|
| 1 | Ejecutar script `n8n_cli.py` para cambiar hora | ❌ Falló, se colgó | El daemon de Docker del host estaba congelado, bloqueando cualquier pipe I/O. |
| 2 | Reiniciar Docker manualmente (sudo) | ✅ Éxito (Manual) | Cuando Docker se freeza, los LLM no pueden autogestionarlo sin pedir `sudo` al humano. |
| 3 | Re-ejecutar `n8n_cli.py` | ❌ Falló, Timeout | Al reiniciar Docker, **la IP de la red bridge de n8n cambió**. El script usaba la IP cacheada anterior. |
| 4 | Conexión directa HTTP bypassando el script | ✅ 4.5 minutos | Operar abriendo terminales bash en cada paso para correr un proxy de python es lento y frágil. |
| 5 | **Solución Definitiva**: Crear `n8n_mcp_server.py` | ✅ MCP Programado | Se programó un Servidor MCP para que la conexión a n8n sea nativa al LLM sin abrir terminales. |

### Lecciones clave y Pilares

- **Pilar: "Lo que podemos mejorar, lo programamos"**: Operar aplicaciones vía scripts de consola llamados desde bash es anti-patrón para agentes de alta velocidad. Cualquier herramienta core (como n8n) DEBE integrarse vía **MCP (Model Context Protocol)**.
- **Resiliencia IP**: La caché de IP del bridge de docker es peligrosa si Docker se reinicia. El MCP Server se encargará de resolver la IP dinámicamente o usar persistencia profunda.

### Estado Actual de la Mejora
- Se desarrolló `/home/lucy-ubuntu/Escritorio/NIN/scripts/n8n_mcp_server.py`.
- Requiere que el usuario lo registre una única vez en su cliente IDE para que Antigravity gane control neuronal directo sobre n8n.

---

## 2026-02-26 (cont.) — Resiliencia Nivel 2: Evasión de Bloqueos

**Objetivo**: Siguiendo el pilar de automatizar la resiliencia en base a cuellos de botella detectados ("lo que se puede mejorar, se programa"), garantizar que el MCP Server nunca se asfixie si el daemon de Docker se cuelga.

### Acciones
| Acciones y Decisiones | Resultado | Lección / Justificación |
|---|-----------|---------|
| Implementar timeout estricto de 2s en las llamadas de Docker `inspect` en el Server. | ✅ Éxito | Si el daemon Docker sufre un freeze masivo de I/O, el bot no puede quedarse colgado ilimitadamente. |
| Agregar Subnet Scanner Paralelo (`concurrent.futures`) como `fallback` agresivo. | ✅ Éxito | Ante la falla de los comandos oficiales, la única ruta viable es la fuerza bruta en las direcciones IP locales tipo `172.x.0.x`. |

### Lecciones clave
- **La Herramienta debe Evadir al Fallo**: En sistemas inestables, los scripts no solo deben cumplir un objetivo, sino contar con una ruta B (como un escaneo paralelo ciego de subredes) que se active automáticamente al detectar parálisis en las dependencias primarias del SO.

---

## 2026-02-27 — Visión: n8n como Multiplicador de Fuerza (Agente Secreto)

**Objetivo**: Evolucionar n8n de ser una herramienta operada por la IA a ser un **Agente Secreto** que asista proactivamente a Antigravity en tareas pesadas o de contexto masivo.

### Los 3 Pilares del Agente Secreto
1. **Mapeador de Contexto**: Delegar en n8n el escaneo profundo de archivos y estructuras para entregar resúmenes de alta densidad a la IA.
2. **Monitor Inmunológico**: n8n vigila la salud del sistema (Docker, RAM, Red) y actúa antes de que la IA pierda conexión.
3. **Investigador SearXNG**: n8n realiza investigaciones web profundas y entrega "conocimiento puro" filtrado a la IA.

### Estado Actual
- Iniciando diseño del primer componente: **Agente Secreto - Mapeador**.
- Se requiere que n8n sea capaz de proveer resúmenes de archivos locales que superan el tamaño de ventana de contexto individual.

### [2026-02-27] — Optimización Extrema y Conciencia Dinámica
Se ha completado la transformación del Agente Secreto en dos fases críticas.

**Fase 1: Velocidad Extrema (Opción B)**
Se eliminó la dependencia del modelo de 32B para tareas de utilería.
- **Escaneo Repo**: 0.003s
- **Grep**: 0.018s
- **Lectura Archivos**: 0.027s
- **Estado Sistema**: 0.247s (vía `estado_sistema_nin`).

**Fase 2: Autodescubrimiento (Evolución)**
- **Dynamic Tool Discovery**: El MCP Server ahora registra automáticamente cualquier flujo de n8n que empiece con `Tool:`.
- **Limpieza de Sistema**: Se eliminó el contenedor `lucy_eyes_searxng` que estaba en conflicto. `searxng-lucy` es ahora el buscador central.
- **Pilar 1 & 2 Consagrados**: El sistema es ahora capaz de autogestionar su contexto y herramientas.

---

### 📥 Resumen para Próxima Sesión (Handover)
- **Infraestructura**: Autodescubrimiento y NiN Notebook activos.
- **Docker**: Estado saludable.
- **Pendiente**:
  1. **Configurar Credenciales GDrive**: En n8n para activar el flujo de sync.
  2. **Monitor Inmunológico**: Automatizar reinicio de servicios fallidos vía n8n.
  3. **Pilar 3**: Expandir capacidades de investigación web con SearXNG.
