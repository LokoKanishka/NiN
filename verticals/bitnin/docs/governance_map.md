# BitNin Governance Map

BitNin está sujeto a revisión institucional formal. Las simulaciones técnicas no dictan su estado; el **Ledger Semanal** lo hace.

## 📊 1. Arquitectura de Gobernanza 

La Gobernanza de BitNin vigila que el criterio del `bitnin_analyst` y la ejecución del sistema no declaren _salud_ en falsos positivos. Para transicionar fuera de _Shadow_ se impone una rigurosidad metódica:

### KPIs Oficiales (La Tríada Operativa)
- **Operativos**: Uptime del scheduler (>98%) y ejecución regular de backups.
- **Analíticos**: Cobertura narrativa sana y estabilidad de la **Señal Compuesta** sin _drifts_ repentinos.
- **Humanos**: Control exhaustivo del backlog HITL (generalmente < 5 casos pendientes). Retrasar aprobaciones humanas se considera un fallo de eficiencia operativa.

## 💼 2. Ciclo de Revisión Institucional

### El "Week Review" y "Week Close"
Dado que el ritmo natural de cripto y de los mercados tradicionales difiere, el compás macro se evalúa por semana (`YYYY-WW`).

1. **Recolección (`week-review`)**: El operador extrae el consolidado de batcheos diarios (`weekly_scorecard.md`) que arroja promedios, porcentajes de fallos, tiempos de latencia y distribuciones de intenciones. Genera el paquete semanal en crudo pero no muta la historia.
2. **Dictamen de Ledger (`week-close`)**: Tras inspección visual del paquete, el humano emite una sentencia obligatoria: `stable`, `watch` o `investigate`. Esta se incrusta irrevocablemente en el Ledger (`weekly_review_state.json`) junto con una Nota del Operador.

### Promotion Gate (El "Peaje" a Pilot)
- BitNin **no se promueve automáticamente** si su software funciona. 
- La promoción ineludible a `Pilot` (siguiente gran hito evolutivo) exige mínimo **cuatro (4) semanas cronológicas reales** de funcionamiento `stable` documentado e ininterrumpido en el Ledger Semanal.

## 🚩 3. ¿Qué significa la Fase 29R?
- `29R` es el acrónimo para la _Ventana Real de Gobernanza_.
- Esto significa abolir el desarrollo acelerado, las simulaciones o los engaños del reloj del sistema.
- Durante `29R`, BitNin tiene que probar con tiempo de pared (físico, biológico) que sostiene su asertividad analítica y su resistencia técnica (scheduler / HITL inbox / observabilidad) a escala 1:1 real con el mercado. Las incidencias son empíricas.
- Hasta no alcanzar estas validaciones tangibles cronológicas (El Hito Evaluatorio "S1"), consideramos justificadamente que BitNin no está preparado para el escalado a Pilot; carece de evidencia.
