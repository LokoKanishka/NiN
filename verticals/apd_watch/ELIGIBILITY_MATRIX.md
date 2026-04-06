# Eligibility Matrix Contract

Fecha: 2026-04-06
Estado: base canónica inicial

## Objetivo

Definir cómo se versiona y utiliza la matriz de elegibilidad para APD Watch sin romper la lógica central.

## Estructura conceptual de regla

Cada `eligibility_rule` debe contemplar:

- `rule_id` estable,
- nombre oficial,
- alias/variantes,
- código (si existe),
- nivel/modalidad aplicable,
- tipo de coincidencia permitida,
- prioridad,
- confianza esperada,
- observaciones.

## Clasificación operativa

- `segura`: coincidencia determinista fuerte.
- `probable`: coincidencia útil pero con incertidumbre limitada.
- `ambigua`: requiere revisión humana o asistencia opcional con IA.

## Regla de versionado

- La matriz debe mantenerse en formato versionable y legible (JSON/YAML/tabla estructurada).
- Cambios de reglas no deben exigir cambios de código en el motor de matching.
- Toda versión debe registrar `effective_date` y autor de cambio.
