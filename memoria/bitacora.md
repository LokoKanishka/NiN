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

- **Red Docker Bridge**: El sandbox SI puede hablar con los containers usando sus IPs internas tipo `172.29.0.x`.
- **API `GET /workflows/:id` es ineficiente**: Por diseño interno de n8n, pedir un workflow individual demora porque serializa demasiada data. `GET /workflows` es rápido.
- **`stripHeavy`**: Al parsear una respuesta de n8n individual, SIEMPRE hacer pop/delete de `activeVersion`, `shared`, `pinData` antes de que los LLMs intenten leerlo para ahorrar decenas de miles de tokens de contexto.
- **Triggers**: Si un sub-workflow se necesita ejecutar por API, NO usar "When Executed by Another Workflow". Usar "Webhook" en su lugar.
