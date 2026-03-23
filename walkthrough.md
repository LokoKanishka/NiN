# Validación y Entregables: Reconexión Narrativa

**1. Archivo exacto modificado:**
`scripts/run_shadow_pipeline.py`

**2. Estrategia elegida:**
`pre-step` inyectado dentro de `run_shadow_pipeline.py`.
*Justificación:* Es el lugar más cohesionado, ya que asegura que cualquier ejecución futura del pipeline analítico (ya sea vía `supervisor.py` u otra orquestación manual) tenga acceso a los datos narrativos refrescados exactamente antes del *Tick* diario. 

**3. Diff corto explicado:**
Se importó `subprocess` de manera inline y se armó la llamada CLI de Python exacta que espera el builder, inyectándola dinámicamente con el `narrative_version` actual del Contexto, y disparándolo en el `cwd` raíz del repositorio. Si el fetch falla por error de red/GDELT, hace log como ERROR pero continúa el pipeline para no bloquear el análisis por completo (utilizaría old baseline).

```diff
--- a/scripts/run_shadow_pipeline.py
+++ b/scripts/run_shadow_pipeline.py
@@ -64,6 +64,22 @@
         run_id = f"sh_{current_dt.strftime('%Y%m%d')}"
         logger.info(f"\n---> Running tick for day {current_dt.strftime('%Y-%m-%d')} (as_of: {as_of})")
         
+        # PRE-STEP: Refresh narrative data before tick
+        logger.info("PRE-STEP: Refreshing narrative dataset from GDELT...")
+        import subprocess
+        narrative_version = ctx.narrative_path.stem.split("__")[-1]
+        cmd_build = [
+            sys.executable, "-m", "verticals.bitnin.services.bitnin_narrative_builder.builder",
+            "gdelt", "--dataset-version", narrative_version,
+            "--mode", "full", "--query", "bitcoin", "--timespan", "1d", "--maxrecords", "50"
+        ]
+        try:
+            cmd_cwd = str(Path(__file__).resolve().parents[2])
+            subprocess.run(cmd_build, check=True, cwd=cmd_cwd)
+            logger.info("Narrative dataset refreshed successfully.")
+        except subprocess.CalledProcessError as e:
+            logger.error(f"Failed to refresh narrative dataset: {e}")
+            
         try:
             res = runner.run_once(
```

**4. Evidencia de que narrativa ya no queda stale:**
```
=== LS RAW ===
total 1664
-rw-rw-r-- 1 lucy-ubuntu lucy-ubuntu  28917 mar 23 19:08 gdelt_doc_artlist__bitcoin__2026-03-23T22-08-46.281Z.json
...

=== STAT ===
  Fichero: verticals/bitnin/runtime/datasets/narrative/normalized/gdelt_doc_artlist__bitcoin__narrative-v1-robust.jsonl
Acceso: 2026-03-23 19:08:46.329112381 -0300
Modificación: 2026-03-23 19:08:46.291133706 -0300
```
*Se generaron raw jsons nuevos y el jsonl normalizado fue modificado hoy con entradas nuevas como "Breakfast briefing : Trump backs down...".*

**5. Evidencia de que shadow sigue corriendo:**
```
=== 🧑‍⚕️ BITNIN DOCTOR (Diagnostic Report) ===
[✅ OK] Project Root Access
[✅ OK] System Health: HEALTHY
Scheduler:     🟢 Active
...
```
*El timer y service ejecutaron el pipeline correctamente y guardaron el batch report (batch_report__batch_20260403_20260403.json).*

**6. `git status --short`**
```
 M scripts/run_shadow_pipeline.py
```
*(Se omiten los archivos modificados previamente que no pertenecen a este scope)*

**7. `git diff --stat`**
```
 scripts/run_shadow_pipeline.py | 16 ++++++++++++++++
 1 file changed, 16 insertions(+)
```
