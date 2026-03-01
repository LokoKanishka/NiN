# Auditoría técnica de salud del proyecto NiN (modo "doctor")

Fecha: 2026-03-01
Alcance: revisión estática de código, configuración e higiene operativa del repositorio (sin desplegar servicios).

## Diagnóstico ejecutivo

**Estado general:** 🟡 **Operable pero con deuda técnica y riesgos de seguridad relevantes.**

- La base del proyecto está bien estructurada para automatización local (n8n + Qdrant + SearxNG + utilidades Python).
- Existen **secretos hardcodeados** y configuraciones permisivas que elevan riesgo en caso de fuga del repo.
- La salud de pruebas es baja: hay scripts de test, pero no un entorno reproducible de dependencias ni suite automatizada estable.
- La documentación es útil a nivel operativo, pero presenta **inconsistencias de puertos/rutas**.

## Hallazgos clave (con severidad)

### 1) Seguridad: secretos y exposición innecesaria — **ALTA**

1. `docker-compose.yml` contiene un `N8N_USER_MANAGEMENT_JWT_SECRET` embebido en texto plano.  
   **Riesgo:** rotación difícil, fuga por historial git, potencial suplantación de sesiones si se reutiliza en otros entornos.

2. `docs/tavily_search.json` incluye una API key Tavily con formato de credencial real en el código del workflow.  
   **Riesgo:** abuso de cuenta/API, consumo indebido, bloqueo de proveedor.

3. En `docker-compose.yml` se habilitan opciones muy permisivas en n8n:
   - `NODE_FUNCTION_ALLOW_BUILTIN=*`
   - `NODE_FUNCTION_ALLOW_EXTERNAL=*`
   - `N8N_BLOCK_FS_WRITE_ACCESS=false`
   - Montaje de `docker.sock`

   **Riesgo:** aumento de superficie de ataque y capacidad de ejecución lateral.

### 2) Calidad de ingeniería: pruebas no reproducibles — **ALTA**

1. `pytest` falla en recolección por dependencias faltantes (`requests`, `mcp`) en varios archivos bajo `scripts/`.
2. No se encontró `requirements.txt`, `pyproject.toml` ni equivalente para bootstrap automático del entorno.

**Impacto:** no existe un "estado verde" portable para CI/local, lo que dificulta detectar regresiones.

### 3) Operación/consistencia documental — **MEDIA**

1. README mezcla puertos de acceso que no coinciden con compose actual (`5688:5678` en compose vs `5678` en pasos del README).
2. README referencia ruta local `~/Escritorio/NIN`, pero el repo/documentación convive con `/workspace/NiN` y otros paths; esto puede confundir despliegues nuevos.

### 4) Mantenibilidad — **MEDIA**

1. Gran parte de la lógica está en scripts utilitarios sin empaquetado formal ni tipado consistente.
2. Se observan fallbacks de red agresivos (escaneo de subredes) en scripts críticos de conexión n8n, útiles para resiliencia pero difíciles de depurar en entornos compartidos.

## Scorecard de salud (0–10)

- **Seguridad:** 4/10
- **Confiabilidad operativa:** 6/10
- **Testabilidad:** 3/10
- **Documentación operativa:** 6/10
- **Mantenibilidad:** 5/10

**Salud global estimada:** **4.8/10**

## Plan de tratamiento recomendado (priorizado)

### Fase 0 (inmediato, 24–48h)

1. **Rotar y eliminar secretos del repositorio**
   - Mover JWT/API keys a `.env` no versionado.
   - Revocar la key Tavily expuesta y generar una nueva.

2. **Reducir permisos de ejecución en n8n**
   - Quitar `NODE_FUNCTION_ALLOW_* = *` salvo necesidad explícita.
   - Revisar necesidad de `docker.sock` montado.

3. **Alinear documentación con runtime real**
   - Unificar puertos de README con `docker-compose.yml`.
   - Corregir rutas de instalación/arranque para evitar ambigüedades.

### Fase 1 (corto plazo, 3–7 días)

1. Crear `requirements.txt` o `pyproject.toml` con dependencias mínimas de scripts.
2. Separar scripts de utilidad de scripts de prueba (nombres claros y carpeta dedicada).
3. Configurar una verificación mínima en CI local:
   - `python -m compileall`
   - `pytest` (aunque sea smoke suite)

### Fase 2 (mediano plazo, 1–2 semanas)

1. Definir perfil de seguridad por entorno (dev/lab/prod).
2. Normalizar logging/errores en scripts de integración n8n.
3. Añadir guías de runbook (backup de `n8n_data`, rotación de claves, recuperación).

## Señales vitales medidas en esta auditoría

- ✅ Compilación estática Python (`compileall`) correcta.
- ⚠️ Suite de pruebas (`pytest`) no ejecutable por dependencias ausentes.
- ⚠️ Validación de compose no ejecutable en este entorno por ausencia del binario `docker`.

## Conclusión del "doctor"

El paciente **no está crítico**, pero sí presenta **hipertensión de permisos** y **exposición de credenciales**. Si se atienden los tres puntos inmediatos (secrets, permisos y documentación), la salud del proyecto puede mejorar rápidamente a un rango de 7/10 con bajo esfuerzo.
