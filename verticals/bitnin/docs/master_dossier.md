# BitNin Master Dossier

## 1. ¿Qué es BitNin hoy?
BitNin es la vertical formal de NiN dedicada a:
- Inteligencia histórica de mercado.
- Memoria RAG sobre episodios y eventos (`cerebro_lucy`).
- Validación de la **Señal Compuesta** como métrica de convergencia.
- Análisis estructurado (`v3-compuesta`) y simulación local.
- Operación **shadow-first** (como paso previo e ineludible a la automatización).

**BitNin NO hace trading real**, no tiene ejecución financiera, ni toca exchange APIs. 

## 2. Estado Exacto Actual
- **Estado General**: `GA SHADOW CERTIFIED (Evidence Pending)`
- **Fase Actual**: `29R` (Ventana Real de Gobernanza Semanal)
- **Próximo Hito Real**: `S1 - 2026-03-24`

## 3. Topología de Capas
El sistema está lógicamente separado en tres planos funcionales:
1. **Plano de Control (`bitnin-control`)**: Maneja ingest, episodios, embeddings, el analista y el supervisor de rutinas.
2. **Plano de Guardia (`bitnin-exec-guard`)**: Ataja las intenciones de trade, las bloquea, requiere aprobación HITL y provee log de auditoría (todo en `dry_run`).
3. **Plano de Observabilidad y Memoria**: Qdrant (`localhost:6333`), métricas longitudinales, scorecards de health y reporte de divergencia/drift narrativo.

## 4. Operación y Recuperación
- **Operación General**: Totalmente regida por el supervisor automático y el scheduler nativo (`systemd --user` en `bitnin-shadow.timer`).
- **Recuperación Total**: BitNin es portátil y reproducible. Sus comandos documentados de `bootstrap`, `backup` y `restore` habilitan reconstrucción _clean-room_ y supervivencia a corrupción de estado (fase RC probada).

## 5. Gobernanza
BitNin no evoluciona por corazonadas; evoluciona bajo evidencia acumulada en su Ledger semanal. La promoción de fase (Ej: Hacia _Pilot_) está estrictamente protegida por un **Promotion Gate** que requiere mínimo 4 semanas reales consecutivas con dictamen operativo `stable`.

---
*Referencia principal de lectura recomendada a un operador nuevo: `architecture_map.md` y `operator_command_map.md`.*
