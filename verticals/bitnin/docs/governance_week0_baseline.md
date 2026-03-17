# BitNin Phase 29R - Governance Baseline (Day 0)

**Fecha de inicio real:** 2026-03-17
**Próximo hito real:** S1 el 2026-03-24
**Aclaración explícita:** Esto es línea base, no Semana 1.

## Estado de Salud y Riesgos (Hoy)
- **Incidentes Reales Hoy:** `none`
- **Backlog HITL Hoy:** 1 Pendientes (CASE-20260317-002)
- **Riesgos Abiertos Hoy:** `bitnin_ctl.py` no ejecutable (Diagnostic FAIL)

## Evidencia Disponible Hoy

### 1. `bitnin-ctl status`
```text

=== 🎯 BITNIN STATUS 360° ===
System Health: [92mHEALTHY[0m
Scheduler:     🟢 Active
HITL Backlog:  [96m1 Pendientes[0m
==============================

```

### 2. `bitnin-ctl doctor`
```text

=== 🧑‍⚕️ BITNIN DOCTOR (Diagnostic Report) ===
[[92m✅ OK[0m] Project Root Access
[[92m✅ OK[0m] Runtime Directory Structure
[[92m✅ OK[0m] HITL State File present
[[91m❌ FAIL[0m] bitnin_ctl.py executable
[[92m✅ OK[0m] bin/bitnin-ctl wrapper present
[[92m✅ OK[0m] BitNin Timer Active
==========================================

```

### 3. `bitnin-ctl briefing`
```text
# 📋 Briefing Diario del Operador — BitNin

*Generado: 2026-03-17 03:17:36 UTC*

## 🛡️ Resumen de Operación
- **Casos Pendientes**: 1
- **Casos Escalados**: 0
- **Cierres en las últimas 24h**: 1

## 🎯 Próximas Acciones Recomendadas
1. Revisar **CASE-20260317-002** (🟡 MEDIUM): Narrative Crash.

---
*Referencia: use `./bitnin_ctl.py briefing` para ver el estado de salud completo.*
```

### 4. Shadow Timer Status
```text
● bitnin-shadow.timer - Run BitNin Shadow Supervisor periodically
     Loaded: loaded (/home/lucy-ubuntu/.config/systemd/user/bitnin-shadow.timer; enabled; preset: enabled)
     Active: active (waiting) since Tue 2026-03-17 18:15:19 -03; 28min ago
    Trigger: Wed 2026-03-18 00:22:03 -03; 5h 38min left
   Triggers: ● bitnin-shadow.service

mar 17 18:15:19 lucy-ubuntu-System-Product-Name systemd[1955]: Started bitnin-shadow.timer - Run BitNin Shadow Supervisor periodically.
```

### 5. Shadow Timer List
```text
NEXT                            LEFT LAST                        PASSED UNIT                ACTIVATES
Wed 2026-03-18 00:22:03 -03 5h 38min Tue 2026-03-17 00:17:35 -03      - bitnin-shadow.timer bitnin-shadow.service

1 timers listed.
Pass --all to see loaded but inactive timers, too.
```

### 6. Shadow Service Journal (last 50)
```text
mar 16 22:02:43 lucy-ubuntu-System-Product-Name python3[461863]: 2026-03-16 22:02:43,876 - bitnin-active-memory-retriever - INFO - Retrieving active memory with query: BTCUSDT 1d BTCUSDT 1d close=71212.0 return_1d=0.009507 volatility=low breakout=True volume_anomaly=False topics=geopolitica|regulacion|macro_monetaria|etf_institucional|exchange_infraestructura
mar 16 22:02:43 lucy-ubuntu-System-Product-Name python3[461863]: 2026-03-16 22:02:43,889 - bitnin-active-memory-retriever - INFO - Retrieving active memory with query: BTCUSDT 1d BTCUSDT 1d close=71212.0 return_1d=0.009507 volatility=low breakout=True volume_anomaly=False topics=geopolitica|regulacion|macro_monetaria|etf_institucional|exchange_infraestructura
mar 16 22:02:43 lucy-ubuntu-System-Product-Name python3[461863]: 2026-03-16 22:02:43,904 - verticals.bitnin.services.bitnin_runtime_runner.runner - INFO - Registering Observability Replay
mar 16 22:02:43 lucy-ubuntu-System-Product-Name python3[461863]: 2026-03-16 22:02:43,904 - bitnin_pipeline - INFO -      Status: insufficient_evidence | Action: no_trade | CompState: DIVERGENT
mar 16 22:02:43 lucy-ubuntu-System-Product-Name python3[461863]: 2026-03-16 22:02:43,904 - bitnin_pipeline - INFO -      Causal Typology: evidencia_insuficiente | Narrative Cover: 0.598908
mar 16 22:02:43 lucy-ubuntu-System-Product-Name python3[461863]: 2026-03-16 22:02:43,904 - bitnin_pipeline - INFO -      Active Memories: 3
mar 16 22:02:43 lucy-ubuntu-System-Product-Name python3[461863]: 2026-03-16 22:02:43,904 - bitnin_pipeline - INFO -
mar 16 22:02:43 lucy-ubuntu-System-Product-Name python3[461863]: =============================================
mar 16 22:02:43 lucy-ubuntu-System-Product-Name python3[461863]: 2026-03-16 22:02:43,904 - bitnin_pipeline - INFO - Pipeline finished. Total runs: 1
mar 16 22:02:43 lucy-ubuntu-System-Product-Name python3[461863]: 2026-03-16 22:02:43,904 - bitnin_pipeline - INFO - Batch report archived at: /home/lucy-ubuntu/Escritorio/NIN/verticals/bitnin/runtime/observability/batches/batch_report__batch_20260314_20260314.json
mar 16 22:02:43 lucy-ubuntu-System-Product-Name python3[461863]: 2026-03-16 22:02:43,904 - bitnin_pipeline - INFO - Scorecard archived at: /home/lucy-ubuntu/Escritorio/NIN/verticals/bitnin/runtime/observability/scorecards/scorecard__batch_20260314_20260314.md
mar 16 22:02:43 lucy-ubuntu-System-Product-Name python3[461863]: 2026-03-16 22:02:43,905 - bitnin_pipeline - INFO - System looks HEALTHY based on current window.
mar 16 22:02:43 lucy-ubuntu-System-Product-Name python3[461862]: 2026-03-16 22:02:43,914 - bitnin_supervisor - INFO - Window 2026-03-14 to 2026-03-14 completed successfully.
mar 16 22:02:43 lucy-ubuntu-System-Product-Name python3[461862]: 2026-03-16 22:02:43,914 - bitnin_supervisor - INFO - Generating health snapshot at: /home/lucy-ubuntu/Escritorio/NIN/verticals/bitnin/runtime/observability/history/health_snapshot.md
mar 16 22:02:43 lucy-ubuntu-System-Product-Name systemd[1982]: Finished bitnin-shadow.service - BitNin Shadow Supervisor Service.
mar 17 00:17:35 lucy-ubuntu-System-Product-Name systemd[1982]: Starting bitnin-shadow.service - BitNin Shadow Supervisor Service...
mar 17 00:17:35 lucy-ubuntu-System-Product-Name python3[635986]: 2026-03-17 00:17:35,779 - bitnin_supervisor - INFO - Resuming from last processed date: 2026-03-29. Next: 2026-03-30
mar 17 00:17:35 lucy-ubuntu-System-Product-Name python3[635986]: 2026-03-17 00:17:35,779 - bitnin_supervisor - INFO - Target Window: 2026-03-30 to 2026-03-30
mar 17 00:17:35 lucy-ubuntu-System-Product-Name python3[635986]: 2026-03-17 00:17:35,779 - bitnin_supervisor - INFO - Executing: /home/lucy-ubuntu/Escritorio/NIN/.venv/bin/python3 /home/lucy-ubuntu/Escritorio/NIN/scripts/run_shadow_pipeline.py --start-date 2026-03-30 --end-date 2026-03-30 --append
mar 17 00:17:35 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:35,833 - bitnin_pipeline - INFO - =============================================
mar 17 00:17:35 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:35,833 - bitnin_pipeline - INFO - Initializing Continuous Shadow Pipeline (Fase 12)
mar 17 00:17:35 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:35,833 - bitnin_pipeline - INFO - =============================================
mar 17 00:17:35 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:35,833 - bitnin_pipeline - INFO - Using Narrative Baseline: /home/lucy-ubuntu/Escritorio/NIN/verticals/bitnin/runtime/datasets/narrative/normalized/gdelt_doc_artlist__bitcoin__narrative-v1-robust.jsonl
mar 17 00:17:35 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:35,850 - bitnin_pipeline - INFO -
mar 17 00:17:35 lucy-ubuntu-System-Product-Name python3[635987]: ---> Running tick for day 2026-03-30 (as_of: 2026-03-30T23:59:59.999000Z)
mar 17 00:17:35 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:35,850 - verticals.bitnin.services.bitnin_runtime_runner.runner - INFO - Starting BitNin Operational Cycle: sh_20260330
mar 17 00:17:35 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:35,852 - verticals.bitnin.services.bitnin_runtime_runner.runner - WARNING - System degraded (non-blocking). Proceeding.
mar 17 00:17:35 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:35,852 - verticals.bitnin.services.bitnin_runtime_runner.runner - INFO - Invoking Analyst for BTCUSDT 1d with run_id sh_20260330 as_of 2026-03-30T23:59:59.999000Z
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:36,636 - bitnin-active-memory-retriever - INFO - Retrieving active memory with query: BTCUSDT 1d BTCUSDT 1d close=71212.0 return_1d=0.009507 volatility=low breakout=True volume_anomaly=False topics=
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:36,651 - bitnin-active-memory-retriever - INFO - Retrieving active memory with query: BTCUSDT 1d BTCUSDT 1d close=71212.0 return_1d=0.009507 volatility=low breakout=True volume_anomaly=False topics=
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:36,667 - verticals.bitnin.services.bitnin_runtime_runner.runner - INFO - Generating Shadow Intent
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:36,717 - bitnin-active-memory-retriever - INFO - Retrieving active memory with query: BTCUSDT 1d BTCUSDT 1d close=71212.0 return_1d=0.009507 volatility=low breakout=True volume_anomaly=False topics=geopolitica|regulacion|macro_monetaria|etf_institucional|exchange_infraestructura
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:36,733 - bitnin-active-memory-retriever - INFO - Retrieving active memory with query: BTCUSDT 1d BTCUSDT 1d close=71212.0 return_1d=0.009507 volatility=low breakout=True volume_anomaly=False topics=geopolitica|regulacion|macro_monetaria|etf_institucional|exchange_infraestructura
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:36,751 - verticals.bitnin.services.bitnin_runtime_runner.runner - INFO - Registering Observability Replay
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:36,751 - bitnin_pipeline - INFO -      Status: insufficient_evidence | Action: no_trade | CompState: DIVERGENT
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:36,751 - bitnin_pipeline - INFO -      Causal Typology: narrativa_ausente | Narrative Cover: 0.0
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:36,751 - bitnin_pipeline - INFO -      Active Memories: 3
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:36,751 - bitnin_pipeline - INFO -
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635987]: =============================================
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:36,751 - bitnin_pipeline - INFO - Pipeline finished. Total runs: 1
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:36,752 - bitnin_pipeline - INFO - Batch report archived at: /home/lucy-ubuntu/Escritorio/NIN/verticals/bitnin/runtime/observability/batches/batch_report__batch_20260330_20260330.json
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:36,752 - bitnin_pipeline - INFO - Scorecard archived at: /home/lucy-ubuntu/Escritorio/NIN/verticals/bitnin/runtime/observability/scorecards/scorecard__batch_20260330_20260330.md
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:36,752 - bitnin_pipeline - WARNING -
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635987]: OBSERVABILITY ALERTS DETECTED:
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635987]: 2026-03-17 00:17:36,752 - bitnin_pipeline - WARNING -   🔴 **DEGRADATION**: Average narrative coverage critically low (0.00).
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635986]: 2026-03-17 00:17:36,764 - bitnin_supervisor - INFO - Window 2026-03-30 to 2026-03-30 completed successfully.
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635986]: 2026-03-17 00:17:36,764 - bitnin_hitl - INFO - Evaluating batch for HITL: /home/lucy-ubuntu/Escritorio/NIN/verticals/bitnin/runtime/observability/batches/batch_report__batch_20260330_20260330.json
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635986]: 2026-03-17 00:17:36,765 - bitnin_supervisor - INFO - Generating health snapshot at: /home/lucy-ubuntu/Escritorio/NIN/verticals/bitnin/runtime/observability/history/health_snapshot.md
mar 17 00:17:36 lucy-ubuntu-System-Product-Name python3[635986]: 2026-03-17 00:17:36,765 - bitnin_supervisor - INFO - Health snapshot updated (MD & JSON) at 2026-03-17T03:17:36.765454+00:00
mar 17 00:17:36 lucy-ubuntu-System-Product-Name systemd[1982]: Finished bitnin-shadow.service - BitNin Shadow Supervisor Service.
```
