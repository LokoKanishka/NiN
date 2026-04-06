# APD Watch Policy

Fecha: 2026-04-06
Estado: obligatorio

## 1) Política de seguridad funcional

1. APD Watch opera en **modo read-only**.
2. Está prohibida toda automatización de postulación, inscripción o modificación en APD.
3. Toda integración externa debe poder apagarse sin perder trazabilidad local.

## 2) Política de gobernanza

1. NiN gobierna el marco operativo y de catálogo.
2. n8n ejecuta workflows registrados.
3. La vertical APD Watch define contratos y reglas de dominio.
4. Un workflow no registrado en catálogo no puede considerarse oficial.

## 3) Política de datos y persistencia

1. Persistencia inicial mínima y auditable en `runtime/apd_watch/`.
2. Snapshots diarios obligatorios (bruto y normalizado).
3. Todo artefacto debe incluir fecha de snapshot y metadatos de fuente.
4. Se recomienda timestamp UTC RFC3339 para comparabilidad cross-day.

## 4) Política de alertas

1. Canal de entrada de Telegram: webhook n8n (arquitectura oficial NiN).
2. Evitar duplicados del mismo día para la misma novedad.
3. Alertas deben enviar resumen + referencia al reporte completo.

## 5) Política de IA opcional

1. Cualquier asistencia con Ollama es opcional y acotada a ambigüedades.
2. Reglas canónicas deterministas tienen precedencia sobre sugerencias de IA.
3. Si falla Ollama, el pipeline debe continuar en modo determinista/fallback.
