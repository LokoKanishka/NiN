# NIN | Orden de Lectura para Agentes (Entry Point)

Para asegurar una intervención segura y evitar la contaminación con información legada o experimental, todo agente (Codex o Antigravity) debe seguir este orden de lectura obligatorio:

---

## 1. El Manifiesto Operativo
**Archivo:** `operating_rules.md`
**Por qué:** Define la ética (Zero Cloud Leak) y las reglas de seguridad. Es el "System Prompt" del proyecto.

## 2. La Verdad Técnica (SSOT)
**Archivos:** `docs/ARCHITECTURE_CURRENT.md` y `docs/CAPABILITIES_MAP.md`.
**Por qué:** Definen qué está vivo y cómo se clasifican las capacidades del sistema. **Ignorar expresamente el `README.md`** si hay contradicción técnica.

## 3. La Infraestructura y el Onboarding
**Archivo:** `docker-compose.yml` y este mismo archivo (`ENTRY_POINT.md`).

---

## Zonas de Exclusión / Ignorar al inicio
- **Documentación Histórica:** `legacy/` y `README.md`. No usar para configurar servicios.
- **Documentación Vertical:** `verticals/` y `AGENTS.md`. Solo leer si la tarea es de trading/CV.
- **Ruido Runtime:** Carpeta `runtime/`, `node_modules/`, `*.db`. No contienen arquitectura.

---

## 🛠️ Verificación Operativa Inicial
Antes de proponer o ejecutar cambios, el agente **DEBE** verificar su entorno con este mini-bloque de comandos:

```bash
# 1. ¿En qué estado estoy?
git branch --show-current
git log -1 --oneline

# 2. ¿Existe la arquitectura canónica?
ls docs/ARCHITECTURE_CURRENT.md docs/ENTRY_POINT.md

# 3. ¿El backend es Ollama (esperado) y no LM Studio?
curl -s http://localhost:11434/api/tags | grep -q "qwen2.5-coder:14b" && echo "Ollama OK"
```

> [!CAUTION]
> Si los comandos fallan o el backend no responde en el puerto 11434, el agente está en un entorno desactualizado o erróneo. **NO PROCEDER** sin consulta.
