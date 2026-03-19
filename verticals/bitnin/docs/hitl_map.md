# BitNin HITL (Human-in-the-Loop) Map

El flujo HITL (Human In The Loop) es la muralla impasable entre la intención probabilística de la máquina y la validación táctica humana. En Shadow, las decisiones impactan el reporte; en futuras fases, el `exec_guard` no operará nada real sin estas firmas y _timestamps_.

## 🏷️ Identidad y Aislamiento

- **`run_id`**: Traza generada en cada ejecución del `bitnin_supervisor`, correlativa de un día y de un asset particular.
- **`batch_id`**: Compilado de runs a nivel agrupado.
- **`case_id`**: El identificador unívoco de un expediente HITL particular levantado (ej. `CASE-20260317-002`). Un `run` inyecta un `case` cuando la intención supera cierto umbral y se le exige visado humano.

## 🔄 Estados y Workflow de Revisión

### Estados Canónicos del HITL
El State Machine del JSON (`hitl_state.json`) acepta únicamente los siguientes estatus por caso:
1. `PENDING`: Generado. En espera.
2. `APPROVED`: Operador asiente el razonamiento y la intención. Relega control al exec_guard.
3. `REJECTED` / `DISMISSED`: Despejado y rechazado el hilo (ya sea por error del analista o por contexto adverso).
4. `ESCALATED`: Require escrutinio profundo del equipo/mantenedor.
5. `EXPIRED`: Murió el timeout útil de la intención antes que un humano llegara. Operacionalmente equivale a un descarte sin ejecución.

### Proyecciones (MDs)
El CLI de HITL proyecta inmediatamente en texto para consumo del operador:
- **Inbox** (`hitl_inbox.md`): La cola priorizada.
- **Archive** (`hitl_archive.md`): Casos finitos donde el actor dictaminó, con _timeline inmutable_ y fecha de cierre.

## 📅 El "Ritual Diario" (`day-close`)
El ciclo diario de la interacción humana:

1. El operador revisa el `briefing` (lista corta de prioridades).
2. Procesa vía `bitnin-ctl hitl review ...` resoluciones para dejar el Backlog limpio.
3. Al finalizar, lanza `./bitnin_ctl.py day-close`.
   - **Compilación Operativa**: Elabora el `operator_journal.md`, registrando qué dictámenes puntuales se emitieron hoy (Logs "EVENT: review/dismiss/escalate").
   - **Bundle Histórico**: Envasa todos los reportes sueltos en un `daily_bundle` atómico fechado, purgando la superficie inmediata de trabajo para el turno del día siguiente.
