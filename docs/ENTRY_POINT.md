# NIN | Orden de Lectura para Agentes (Entry Point)

Para asegurar una intervención segura y evitar la contaminación con información legada o experimental, todo agente (IA o Humano) debe seguir este orden de lectura obligatorio al entrar al repositorio:

---

## 1. El Manifiesto Operativo
**Archivo:** `operating_rules.md`
**Por qué:** Define la ética de "Zero Cloud Leak", el protocolo de aislamiento "Blindfold" y las reglas de seguridad para la ejecución de comandos. Es el "System Prompt" del proyecto.

## 2. La Verdad Técnica (SSOT)
**Archivo:** `docs/ARCHITECTURE_CURRENT.md`
**Por qué:** Es el mapa del mundo real. Define qué servicios están vivos (Ollama), qué servicios son leyendas (LM Studio) y cuáles son los endpoints productivos. **Ignorar el README.md si contradice este archivo.**

## 3. La Infraestructura Viva
**Archivo:** `docker-compose.yml`
**Por qué:** Es la radiografía de la red. Define cómo se hablan los contenedores y qué puertos están realmente expuestos.

## 4. El Historial de Estabilidad
**Archivo:** `audit_protocol.md`
**Por qué:** Contiene la evidencia primaria de las últimas pruebas de estrés y la resolución de la falla de conectividad de los 3 segundos. Es el contexto de "por qué las cosas están así ahora".

---

## Zonas de Exclusión / Ignorar al inicio
- **`README.md`:** Solo contexto histórico. No usar para configurar endpoints.
- **`AGENTS.md`:** Documentación vertical de trading. Solo leer si la tarea es específica de trading.
- **`node_modules/`, `data/`, `memoria/`, `*.db`:** Ruido de runtime. No contienen arquitectura.
