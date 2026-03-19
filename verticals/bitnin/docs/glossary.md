# BitNin Glossary 

Glosario operativo y canónico formal del sistema BitNin para evitar ambigüedades técnicas.

### B
- **Baseline Freeze**: Estado del código y del runtime que ha sido inspeccionado y congelado documentalmente, significando que ya no sufrirá mutaciones agresivas en pos de asegurar tests longitudinales limpios.
- **Backlog HITL**: Cantidad de Casos (expedientes de aprobación) que el operador humano debe revisar porque el sistema los ha puesto en espera. Retrasar esto influye negativamente en el Score Semanal.

### C
- **Case ID**: Identificador único humano-legible de un expediente HITL (ej. `CASE-2026-xxx`). Es la clave para interactuar a través del CLI.
- **Composite Signal (Señal Compuesta)**: La métrica o score de convergencia central que BitNin produce cruzando análisis técnico (market bar) con la solidez causal externa (soporte narrativo de memoria RAG).

### D
- **Day-close**: El ritual diario. Comando explícito para concluir 24hs de trabajo, asentar la bitácora operativa y empaquetar un bundle histórico en `.zip` o directorio inmutable de logs.
- **Drift**: Corrimiento estadístico o silencioso del sistema respecto a su "estado de salud inicial". Usualmente, BitNin levanta un _drift warning_ si el score analítico global baja un 40-50% respecto al comportamiento promedio que la máquina presentó la semana pasada.
- **Dry-run**: Contexto operativo donde el motor asume funciones 1:1, transitan todas las integraciones (como firmas y _exec-guards_), pero en el paso final las intenciones generadas se escriben en disco local o mockers y la red financiera/exchange no recibe ninguna API Call mutadora.

### G
- **GA Shadow (General Availability Shadow)**: Nivel de confianza institucional indicando que el código no requiere monitoreo intensivo por un _dev_; se consolida el status quo local, su timer daemonizado via `systemd` tiene un comportamiento estable, los fallos son reportados internamente sin matar el _main loop_ y el supervisor lidia solo con locks zombies.

### P
- **Pilot Readiness**: Estado de madurez del sistema requerido para mutar de _Shadow_ a simulación sobre un _paper-trading_ real o capital restringido. Se obtiene luego del _Promotion Gate_.

### S
- **S1 (Semana 1 / Hito 1)**: Meta referencial temporal hacia la que apunta la _Fase 29R_ para extraer su primer paquete verificado completo.
- **Shadow Mode**: Filosofía troncal de BitNin; en esta modalidad se miden predicciones pasivas y diagnósticos estructurados contra la realidad (midiendo cuán "bueno" habría sido tradear esto), y todas las ejecuciones quedan "a la sombra". Nada se transmite en _vivo_.
- **Stale (Proceso Muerto)**: Diagnóstico emitido en el Snapshot de salud si el _cron automático_ o `bitnin_supervisor` fallan en ejecutarse durante varias iteraciones sucesivas a su cadencia estipulada.
- **SSOT**: _Single Source of Truth_. El documento arquitectural rector. Ningún comando, script o workflow n8n prevalecerá sobre un dictamen ya asentado en el SSOT.

### W
- **Week-review**: Compilación del recaudo logístico de los _bundles_ diarios a nivel general de los últimos 7 días. Precede al _Week-close_.
- **Week-close**: Ejecución del mandato humano que concluye el fin de ciclo con el comando explícito "decision [stable, watch, investigate]", inscribiendo estatus operativo en el _Ledger_. 
- **29R (Fase)**: Denominación para la fase "En Curso" (Ventana Real), un _freeze_ diseñado para acarrear evidencia con temporalidad real del mercado transcurriendo. _La R simboliza Real-time Evidential Readiness_.
