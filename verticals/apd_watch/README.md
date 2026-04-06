# APD Watch

APD Watch es la vertical formal de NiN para monitorear en modo **read-only** publicaciones de actos públicos docentes (APD), normalizarlas, cruzarlas contra una matriz de elegibilidad y generar reportes/alertas.

## Principios operativos

- **Read-only absoluto** sobre APD: no se ejecutan acciones de escritura ni postulación.
- **Sin autopostulación**: la vertical solo observa, compara y reporta.
- **Separación de responsabilidades**:
  - **NiN** gobierna normas, contratos y autoridad.
  - **n8n** ejecuta pipelines/workflows.
  - **APD Watch** define reglas de dominio (fuente, normalización, matching y reportes).
- **Persistencia inicial simple**: se fija convención única en `verticals/apd_watch/runtime/` sin sobreingeniería temprana.

## Documentos de autoridad

- `SSOT.md`: alcance, límites, baseline técnico y decisiones canónicas.
- `CATALOG.md`: slugs de workflows previstos y autoridad esperada.
- `POLICY.md`: políticas obligatorias de seguridad, lectura y no automatización.
- `APD_SOURCE.md`: diseño de lectura de la fuente APD en modo read-only.
- `ELIGIBILITY_MATRIX.md`: contrato de la matriz canónica de elegibilidad.
- `data/eligibility_rules.seed.json`: semilla machine-readable inicial de reglas de elegibilidad.
- `schemas/*.json`: contratos de datos para artefactos de la vertical.
- `tools/snapshot_pipeline.py`: pipeline mínimo raw → normalized usando fixture/manual input.
- `tests/fixtures/apd_offers_sample.json`: fixture base para pruebas read-only.

## Estructura fundacional (actual)

```text
verticals/apd_watch/
├── APD_SOURCE.md
├── CATALOG.md
├── ELIGIBILITY_MATRIX.md
├── POLICY.md
├── README.md
├── SSOT.md
├── data/
│   └── eligibility_rules.seed.json
├── runtime/
│   ├── logs/
│   │   └── .gitkeep
│   ├── matches/
│   │   └── .gitkeep
│   ├── normalized/
│   │   └── .gitkeep
│   ├── reports/
│   │   └── .gitkeep
│   └── snapshots/
│       └── .gitkeep
├── schemas/
│   ├── daily_report.schema.json
│   ├── eligibility_rule.schema.json
│   ├── match_result.schema.json
│   ├── offer_normalized.schema.json
│   └── offer_raw.schema.json
├── tests/
│   ├── fixtures/
│   │   └── apd_offers_sample.json
│   └── test_snapshot_pipeline.py
├── tools/
│   └── snapshot_pipeline.py
└── workflows/
    ├── .gitkeep
    └── apd_fetch_snapshot.json
```

## Ejecución mínima local (read-only)

```bash
python verticals/apd_watch/tools/snapshot_pipeline.py --date 2026-04-06
```

Esto genera snapshots y manifests en `verticals/apd_watch/runtime/{snapshots,normalized}/`.
