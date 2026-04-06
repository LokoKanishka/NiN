# APD Watch SSOT

Estado general: `FOUNDATIONAL`
Fecha: 2026-04-06

## 1. Definición oficial

APD Watch es la vertical de NiN para:

- captura diaria read-only de publicaciones APD,
- normalización trazable de ofertas,
- matching determinista contra una matriz canónica de elegibilidad,
- generación de diff diario y reporte legible,
- emisión de alertas resumidas por canal oficial.

## 2. Límites no negociables

APD Watch **sí** hace:

- lectura de fuente APD,
- snapshot bruto y snapshot normalizado,
- matching y clasificación (`seguro`, `probable`, `ambigua`, `no_match`),
- persistencia de artefactos en `runtime/`.

APD Watch **no** hace:

- postulación automática,
- escritura sobre APD,
- bypass de gobernanza de NiN,
- reemplazar reglas deterministas por IA en decisiones básicas.

## 3. Regla de gobernanza

Desde su creación en `verticals/apd_watch/`, esta carpeta es la autoridad documental máxima de APD Watch dentro de NiN.

Consecuencias:

- ningún script lateral se considera autoridad por defecto,
- toda alta futura de workflows APD en catálogo debe respetar esta SSOT y `CATALOG.md`,
- toda integración con Telegram debe respetar el canal webhook oficial.

## 4. Baseline técnico observado en NiN (Tramo 2)

### 4.1 Fuentes inspeccionadas

- `docs/ARCHITECTURE_CURRENT.md`
- `docker-compose.yml`
- `docs/N8N_GOVERNANCE.md`
- `docs/TELEGRAM_CHANNEL.md`
- `docs/CAPABILITIES_MAP.md`

### 4.2 Patrones reutilizables identificados

1. **Workflows periódicos / orquestación**
   - n8n es el orquestador canónico en `http://localhost:5688`.
   - La vertical debe registrarse en catálogo (`live_workflows`) y usar slugs, no IDs hardcodeados.

2. **Alertas**
   - Telegram de entrada oficial por webhook n8n.
   - Salida por scripts/servicios permitida; long polling paralelo prohibido para el mismo bot.

3. **Persistencia en `runtime/`**
   - El estado operativo y artefactos deben vivir en `runtime/`.
   - Patrón recomendado: snapshots + derivados + logs con convención estable.

4. **Uso de Ollama**
   - Ollama es motor local canónico (`host.docker.internal:11434`).
   - APD Watch lo considera opcional y acotado a ambigüedades, nunca como reemplazo de reglas base.

### 4.3 Riesgos de integración documentados

- **Colisión de nombres**
  - Riesgo: slugs/labels ambiguos con otras verticales.
  - Mitigación: prefijo `apd_` para workflows y artefactos.

- **Puertos y endpoints**
  - Riesgo: confundir servicios vecinos o puertos similares.
  - Mitigación: usar solo endpoints canónicos de este repo.

- **Prácticas de catálogo**
  - Riesgo: invocar workflows sin alta en `catalog.db`.
  - Mitigación: registrar cada workflow APD antes de consumo por scripts.

- **Timezone**
  - Riesgo: inconsistencias por `GENERIC_TIMEZONE=America/Santiago` y cierres APD locales.
  - Mitigación: persistir timestamps en UTC + conservar campo de timezone de origen cuando aplique.

- **Formato de reportes**
  - Riesgo: reportes no comparables entre días.
  - Mitigación: contrato fijo (`daily_report.schema.json`) + resumen humano estable.

## 5. Persistencia inicial (simple)

Estructura prevista:

- `runtime/apd_watch/snapshots/`
- `runtime/apd_watch/normalized/`
- `runtime/apd_watch/matches/`
- `runtime/apd_watch/reports/`
- `runtime/apd_watch/logs/`

No se introducen dependencias extra en esta fase fundacional.
