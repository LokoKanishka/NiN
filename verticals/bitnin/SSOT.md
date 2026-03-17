# BitNin SSOT

Estado: vigente para Fase 0-1
Fecha de congelamiento: 2026-03-13

## 1. Definicion oficial

BitNin es la vertical formal de NiN para:

- inteligencia historica de mercado
- memoria RAG sobre episodios y eventos
- Señal Compuesta como metrica de convergencia
- analisis estructurado
- simulacion de decisiones futuras
- shadow mode como paso previo a cualquier automatizacion posterior

BitNin v1 no es trading real. BitNin v1 es shadow-first.

## 2. Alcance de BitNin v1

BitNin v1 hace:

- relevamiento y normalizacion de datos historicos
- captura de narrativa y eventos con retencion local limitada
- construccion de episodios reutilizables para retrieval
- analisis con salida estructurada
- generacion de intenciones de simulacion o shadow
- persistencia auditable de artefactos

BitNin v1 no hace:

- trading real
- ejecucion financiera
- custody
- Electrum operativo
- uso de credenciales financieras
- cambios en workflows activos existentes
- cambios sobre Telegram real o n8n en runtime

## 3. Principios no negociables

1. Shadow-first. Toda decision futura se valida primero en simulacion o shadow.
2. No-trade by default. `no_trade` e `insufficient_evidence` son salidas validas.
3. Vertical gobernada. La autoridad funcional de BitNin vive en `verticals/bitnin/`.
4. UTC obligatorio. Todo artefacto persistido por BitNin debe usar timestamps UTC en formato RFC 3339.
5. Evidencia antes que intuicion. Ningun analisis debe asumir cobertura suficiente si no queda explicitada.
6. Sin vectores dummy. Qdrant solo puede recibir embeddings reales y dimension explicitada por metadata.

## 4. Componentes usados por BitNin

BitNin se apoya en componentes ya presentes en NiN, sin modificarlos en esta fase:

| Componente | Estado observado | Uso de BitNin |
| :-- | :-- | :-- |
| `n8n` | Orquestador local en `http://localhost:5688` via Docker | Plano de control y pipelines futuros |
| `Ollama` | Motor oficial en `http://host.docker.internal:11434` | Analisis, clasificacion, curaduria |
| `Qdrant` | Servicio local en `http://localhost:6333` | Memoria RAG y retrieval futuro |
| `Telegram` | Entrada oficial solo por webhook n8n; salida por scripts permitida | Aprobaciones y alertas futuras, no activadas en esta fase |

## 5. Separacion de planos

La separacion siguiente es normativa para BitNin. En Fase 0-1 es una separacion logica, no una implementacion activa.

### 5.1 `bitnin-control`

Plano de orquestacion, ingest, enriquecimiento, indexado, analisis y reportes.

Responsabilidades previstas:

- ingest de mercado
- ingest narrativo
- construccion de episodios
- embeddings e indexado
- tick de analista
- reporte diario

### 5.2 `bitnin-exec-guard`

Plano de guardia para intenciones, aprobaciones y cualquier paso que pudiera parecer ejecucion.

Responsabilidades previstas:

- registrar `trade_intent`
- solicitar aprobacion HITL
- bloquear ejecucion real en v1
- dejar trazabilidad de shadow, simulacion o dry_run

**Nota Fase 10:** El `bitnin-exec-guard` está implementado como un servicio local y aislado.
Recibe intenciones, evalúa guardrails y emite `execution_record` exclusivamente en modo `dry_run`. Aún no se conecta con dinero real, wallets ni exchanges. `approved` NO implica ejecución automática.

### 5.3 Auditoria / Replay

Plano de persistencia y revision posterior.

Responsabilidades previstas:

- logs estructurados
- versionado de dataset
- artefactos reproducibles
- replay de episodios, analisis y decisiones

## 6. Baseline real encontrado en NiN

### 6.1 Documentos base

- `docs/ARCHITECTURE_CURRENT.md` declara a n8n, Ollama, Telegram, SearXNG y Qdrant como stack canonico actual.
- `docker-compose.yml` confirma servicios locales para `n8n`, `qdrant` y `searxng`, y expone `OLLAMA_HOST=http://host.docker.internal:11434`.
- `docs/N8N_GOVERNANCE.md` exige gobernanza por `library/catalog.db` y unicidad de autoridad por vertical.
- `docs/TELEGRAM_CHANNEL.md` fija webhook n8n como unica entrada oficial de Telegram y prohibe `getUpdates` en paralelo.
- `docs/CAPABILITIES_MAP.md` establece que una carpeta en `verticals/` es autoridad maxima para su dominio.

### 6.2 Workflows y piezas relevantes observadas

- `workflows/nin_telegram_service.json`
  - activo en el export
  - webhook unificado de salida a Telegram
- `workflows/pilar_5_bunker_de_memoria_rag_cyberpunk_BSgAk06gicLgm7zfPpd3_.json`
  - activo en el export
  - usa `nomic-embed-text:latest`
  - indexa en Qdrant coleccion `cerebro_lucy`
  - dispara por cambios de archivos en `/mnt/Cerebro`
- `workflows/nin_bibliotecario.json`
  - inactivo en el export
  - muestra patron reutilizable para Telegram Trigger + router Python + respuesta
- `workflows/notenin_researcher.json`
  - workflow catalogado como vertical viva en `library/catalog.db`
  - usa Ollama y guarda reportes Markdown en `/home/node/.n8n-files/docs/notenin/`
- `workflows/agente_secreto_-_mapeador_8RwngQmsa4ObRh2I.json`
  - activo en el export
  - webhook + agente LangChain + Ollama
- `workflows/lucy_nin_c_qkLg6wQ5BMJN8IETobT87.json`
  - activo en el export
  - chat trigger + agente + Ollama

### 6.3 Reutilizables para approvals, HITL, reportes y runtime

- `docs/MISSION_SPEC.md`
  - contrato de mision, estados y layout de artefactos en `runtime/missions/<mission_id>/`
- `scripts/bibliotecario/mission_manager.py`
  - persistencia de misiones, artifacts y `mission_log.jsonl`
- `scripts/bibliotecario/hitl.py`
  - requests de aprobacion y timeout/hibernacion por Telegram
- `scripts/bibliotecario/pipeline.py`
  - orquestacion con pausas HITL y resume
- `scripts/bibliotecario/dossier.py`
  - ensamblado de reporte Markdown desde artefactos persistidos
- `scripts/startup_check.py`
  - ejemplo de reporte JSON en `runtime/memoria/startup_report.json`

### 6.4 Restricciones y discrepancias observadas

- `library/catalog.db` contiene `live_workflows`, pero no existe ningun slug ni workflow de BitNin todavia.
- `workflows/pilar_1_sistema_inmunologico_doctor_mSjsiVaTv5sfb99E.json` figura con `"active": false` en el export, mientras `docs/ARCHITECTURE_CURRENT.md` y `library/catalog.db` lo tratan como workflow vigente/activo. Esta discrepancia queda registrada y no se corrige en Fase 0-1.
- `scripts/graph_memory_tool.py` usa vectores dummy para Qdrant. Ese patron queda explicitamente prohibido para BitNin.
- `Blockchain.com Charts API` sirve como referencia historica larga, pero no como barra canonica rica para episodios. Las barras canonicamente operativas de BitNin parten de `Binance klines`.

## 7. Regla de UTC para artefactos

Todo artefacto futuro de BitNin debe:

- persistir timestamps en UTC
- evitar timestamps locales ambiguos
- incluir `dataset_version` o referencia equivalente cuando aplique
- permitir replay sin depender del reloj local del host

## 8. Regla de vertical gobernada

Desde la creacion de `verticals/bitnin/`, esta carpeta es la autoridad documental maxima para BitNin dentro de NiN.

Consecuencias:

- ningun script lateral pasa a ser autoridad de BitNin por defecto
- ningun workflow futuro de BitNin debe considerarse oficial si contradice esta carpeta
- toda futura alta en `library/catalog.db` para BitNin debe respetar esta SSOT y `CATALOG.md`

## 9. Decision de fase

La decision formal de Fase 0-1 es:

- BitNin queda constituida como vertical formal
- la implementacion queda bloqueada a shadow/simulacion
- no se habilita ninguna via de trading real
- el siguiente paso esperado es dataset de mercado versionado

## 10. Nota de Fase 2

Fase 2 introduce un builder local de dataset de mercado dentro de `verticals/bitnin/services/bitnin_dataset_builder/`.

Alcance de esa capa:

- bootstrap historico reproducible
- refresh incremental
- normalizacion UTC
- validacion minima de integridad
- snapshot listo para replay

Lo que sigue fuera de alcance en esa fase:

- narrativa
- episodios
- embeddings o Qdrant
- analista
- shadow o HITL

## 11. Nota de Fase 3 y Baseline Narrativo

Fase 3 agrega discovery narrativo estructurado en `verticals/bitnin/services/bitnin_narrative_builder/`.

Principio de esta capa:

- GDELT se usa para discovery de candidatos narrativos
- los eventos normalizados son hipotesis estructuradas con confianza, no verdad causal absoluta
- se persisten solo metadata, links, resumen local y tags
- no se persiste texto completo externo como dataset normalizado

### 11.1 Baseline Narrativo Efectivo (`v1-robust`)
Durante la estabilización de la Fase 8, el dataset narrativo se migró al baseline `v1-robust` para permitir la validación histórica multi-régimen.
Reglas operativas de este baseline:
- **Rango temporal verificado:** Cubre desde el **`2026-01-07`** en adelante.
- **Hueco conocido:** El periodo de `2026-01-01` a `2026-01-06` se considera un límite material de recuperación inicial desde GDELT; no se asumen convergencias narrativas precisas en esa ventana (el analista mostrará `narrativa_ausente` o forzará un estado "ciego").
- **Parametrización:** Por defecto, el analista apunta al baseline interno normalizado `v1-robust`. Sin embargo, esto es parametrizable dinámicamente vía variable de entorno `BITNIN_NARRATIVE_DATASET_PATH` o parámetro de CLI explícito.

## 12. Nota de Fase 4

Fase 4 agrega construccion de episodios historicos reproducibles en `verticals/bitnin/services/bitnin_episode_builder/`.

Principio rector:

- los episodios son market-first, narrative-augmented
- el mercado dispara o valida el episodio
- la narrativa enriquece, contextualiza y prioriza, pero no define por si sola un episodio salvo reglas futuras explicitamente documentadas
- el constructor de episodios debe ser reproducible y no interpretativo

## 13. Nota de Fase 5

Fase 5 agrega memoria RAG real en `verticals/bitnin/services/bitnin_memory_indexer/`.

Puntos congelados en esta fase:

- embeddings reales via Ollama; quedan prohibidos los vectores dummy
- dimension real medida antes de crear collections: `768` con `nomic-embed-text:latest`
- collections minimas: `bitnin_episodes` y `bitnin_events`
- upsert idempotente por id estable derivado del id canonico del documento
- retrieval semantico inicial con filtros por metadata

Observacion operativa relevante:

- el SSOT historico de NiN documentaba Qdrant en `http://localhost:6333`
- la verificacion real de esta fase encontro el endpoint vivo en `http://127.0.0.1:6333`
- BitNin unifica el puerto operativo en `6333` para evitar ambigüedad.
- BitNin debe medir y verificar el endpoint real antes de indexar, en vez de asumir puertos por herencia documental

## 14. Nota de Fase 6

Fase 6 agrega un analista estructurado en `verticals/bitnin/services/bitnin_analyst/`.

Principios congelados en esta fase:

- el analista no ejecuta nada
- el analista describe el presente, recupera analogos y produce JSON validado
- `no_trade` e `insufficient_evidence` son salidas sanas, no errores
- el analista depende de memoria RAG trazable y no de "memoria interna magica"
- la salida operativa se persiste en `raw`, `normalized` y `snapshots`

## 15. Nota de Fase 7

Fase 7 agrega simulacion y replay en `verticals/bitnin/services/bitnin_backtester/`.

Principios congelados:

- el replay es point-in-time
- el analista no puede ver barras, eventos ni episodios posteriores al `as_of` del tick evaluado
- los resultados de esta fase miden honestidad metodologica antes que rentabilidad
- ningun resultado de backtest autoriza ejecucion ni shadow por si mismo

## 16. Nota de Fase 8

Fase 8 agrega shadow mode local en `verticals/bitnin/services/bitnin_shadow/`.

Principios congelados:

- shadow registra intenciones hipoteticas; no ejecuta
- shadow no usa Telegram ni HITL en esta fase
- toda intencion local debe tener vigencia, estado y review posterior posible
- shadow local sigue siendo no operativo sobre fondos o servicios externos

## 17. Nota de Fase 9

Fase 9 agrega HITL formal en `verticals/bitnin/services/bitnin_hitl/` y artefactos de workflow en `verticals/bitnin/workflows/`.

Principios congelados:

- Telegram entra por webhook canonico, nunca por polling
- `approved` o `rejected` cambian estado formal, no disparan ejecucion
- toda decision humana queda auditada con actor, timestamp y canal
- expiracion es un estado terminal valido si no llega decision a tiempo

## 19. Nota de Fase 12

Fase 12 agrega monitoreo sostenido, archivado longitudinal y detección de drift en `verticals/bitnin/runtime/observability/`.

Principios operativos:
- **Archivado Estructurado**: Los reportes se organizan en `batches/`, los scorecards en `scorecards/` y los metadatos acumulativos en `history/`.
- **Detección de Drift**: El sistema compara automáticamente la ventana actual contra el histórico reciente para detectar desvíos significativos en la cobertura narrativa o en la confianza del analista.
- **Modo Append**: El pipeline está diseñado para crecer longitudinalmente, integrando nuevas ventanas de sombra en un registro temporal continuo.
- **Alertas de Salud de Feed**: Se formaliza la auditoría del dataset narrativo y la memoria activa, distinguiendo entre "ausencia por contexto" y "ausencia por falla técnica".

## 18. Nota de Fase 10

Fase 10 agrega observabilidad longitudinal y pruebas de estabilidad en shadow mode continuo (pipeline script y scorecards en `verticals/bitnin/services/bitnin_observability/`).

Principios congelados:

- el pipeline continuo corre el analista secuencialmente simulando cron diario real
- el scorecard condensa distribuciones de tipologías, estados compuestos y abstención
- están activadas reglas estrictas de detección de **degradación silenciosa** que revientan logs (ej. memoria inútil, 100% de un fallo, narrativa perennemente < 0.2)
- el éxito de esta fase no es operar, sino diagnosticar correctamente cuán bien sostiene el criterio su desempeño en el tiempo.
