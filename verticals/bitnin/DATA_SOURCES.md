# BitNin Data Sources

Estado: baseline de gobierno de fuentes para Fase 0-1

## Reglas base

- El discovery narrativo queda abierto, pero toda fuente nueva debe agregarse explicitamente a este archivo.
- Se permite guardar metadata, links y resumenes propios.
- Se debe evitar almacenamiento masivo de texto completo de medios con restricciones de licencia o robots.
- CoinGecko se considera secundaria/no canonica al inicio.

| Fuente | Tipo | Uso previsto | Granularidad | Costo | Retencion local permitida | Permitido/Prohibido | Notas |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| `Blockchain.com Charts API` | mercado/on-chain agregado | referencia historica larga, contexto macro y contraste de largo plazo | diario | bajo o gratis segun endpoint | si, series derivadas y snapshots versionados | permitido | referencia larga; no usar como barra canonicamente rica para episodios porque no aporta OHLCV real |
| `Binance klines` | mercado/ohlcv exchange | barras canonicas reales para episodios, regimen, volatilidad y comparacion operativa | 1m a 1d segun endpoint | gratis con rate limits | si, barras normalizadas y manifest | permitido | fuente canonica inicial de barras reales; no implica operacion ni credenciales de trading |
| `GDELT` | narrativa/eventos abiertos | discovery narrativo, clusters tematicos, entidades, enlaces | intradia a diario | gratis | si, metadata, ids, links y resumen local | permitido | no almacenar masivamente contenido completo de medios enlazados |
| `CoinGecko` | mercado/referencia secundaria | contraste de precios, metadata de activos, fallback inicial | minutos a diario | gratis con limites | si, snapshots y metadata derivada | permitido con cautela | secundaria, no canonica inicial |
| `NiN docs/workflows/runtime specs` | interna/gobierno | baseline arquitectonico, politicas, contratos y patrones de persistencia | documental | nulo | si | permitido | fuente de verdad para integracion con el stack NiN, no para señales de mercado |

## Criterios de admision futura

- La fuente debe tener uso claro dentro de mercado, narrativa, episodios o auditoria.
- La licencia y la retencion local deben ser compatibles con uso interno.
- Debe quedar explicito si la fuente es canonica, secundaria o solo exploratoria.
- Toda fuente nueva debe definir el artefacto minimo que produce y su versionado.
