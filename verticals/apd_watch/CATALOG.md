# APD Watch Catalog

Estado general: `planned`
Fecha: 2026-04-06

Catálogo inicial de workflows esperados para APD Watch.

| Slug | Propósito | Inputs | Outputs | Estado inicial | Autoridad esperada |
| :-- | :-- | :-- | :-- | :-- | :-- |
| `apd_fetch_snapshot` | Capturar snapshot diario read-only desde APD. | URL/filtros fuente, fecha objetivo | `offer_raw[]`, manifest, logs | planned | workflow autoritativo de captura APD |
| `apd_normalize_offers` | Normalizar ofertas crudas y computar fingerprint. | `offer_raw[]`, reglas de normalización | `offer_normalized[]`, manifest, logs | planned | workflow autoritativo de normalización |
| `apd_match_eligibility` | Cruzar ofertas normalizadas contra matriz canónica. | `offer_normalized[]`, `eligibility_rule[]` | `match_result[]`, métricas, logs | planned | workflow autoritativo de matching |
| `apd_daily_diff` | Comparar día actual vs día previo. | snapshots normalizados + matches | diff diario, resumen de cambios | planned | workflow autoritativo de diff |
| `apd_daily_report` | Emitir reporte diario legible y alertable. | diff, matches, métricas de cierre | reporte markdown/json + payload resumen | planned | workflow autoritativo de reportes |

## Notas de gobierno

- Todo workflow APD deberá registrarse en `library/catalog.db` antes de ser invocado por scripts.
- Se mantiene convención de nombres con prefijo `apd_` para reducir colisiones.
- Ningún workflow de este catálogo habilita postulación o escritura sobre la fuente APD.
