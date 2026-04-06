# APD Watch

APD Watch es la vertical formal de NiN para monitorear en modo **read-only** publicaciones de actos públicos docentes (APD), normalizarlas, cruzarlas contra una matriz de elegibilidad y generar reportes/alertas.

## Principios operativos

- **Read-only absoluto** sobre APD: no se ejecutan acciones de escritura ni postulación.
- **Sin autopostulación**: la vertical solo observa, compara y reporta.
- **Separación de responsabilidades**:
  - **NiN** gobierna normas, contratos y autoridad.
  - **n8n** ejecuta pipelines/workflows.
  - **APD Watch** define reglas de dominio (fuente, normalización, matching y reportes).
- **Persistencia inicial simple**: se prioriza trazabilidad en `runtime/` sin sobreingeniería temprana.

## Documentos de autoridad

- `SSOT.md`: alcance, límites, baseline técnico y decisiones canónicas.
- `CATALOG.md`: slugs de workflows previstos y autoridad esperada.
- `POLICY.md`: políticas obligatorias de seguridad, lectura y no automatización.
- `APD_SOURCE.md`: diseño de lectura de la fuente APD en modo read-only.
- `ELIGIBILITY_MATRIX.md`: contrato de la matriz canónica de elegibilidad.
- `schemas/*.json`: contratos de datos para artefactos de la vertical.
