# BitNin Backtester

Servicio local para replay temporal, simulacion y reporte comparativo de BitNin.

## Principios

- point-in-time replay
- sin look-ahead en el analisis del tick
- comparacion contra baselines simples
- resultados para higiene metodologica, no para autorizar ejecucion

## Flujo

1. recorre barras congeladas del dataset de mercado
2. invoca al analista con `as_of` igual al cierre de cada barra
3. recupera analogos solo hasta ese `as_of`
4. persiste decision + review por caso
5. calcula metricas y baselines
6. genera reporte y snapshot

## Baselines

- `buy_and_hold`
- `never_trade`
- `return_signal`

## Exito en esta fase

- demostrar replay honesto
- medir prudencia, cobertura y consistencia
- evitar conclusiones direccionales por autoengaño

No significa:

- edge validado
- permiso para shadow
- permiso para ejecucion real
