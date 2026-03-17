# BitNin Operational Runbook - Shadow Mode

## 1. Introduction
This document describes the operations for BitNin in `shadow + dry_run` mode. BitNin is currently in an analytical observation phase, focused on validating its composite signal and causal reasoning without financial execution.

## 2. Daily Operations
The system is designed to run periodically via the supervisor.

### Starting the Supervisor
To process the next available window:
```bash
PYTHONPATH=. .venv/bin/python3 verticals/bitnin/services/bitnin_observability/supervisor.py --days 1
```

### Checking System Health
Inspect the central state file for a quick status overview:
`verticals/bitnin/runtime/observability/history/operational_state.json`

Possible Statuses:
- `HEALTHY`: System is operating within normal parameters.
- `DEGRADED`: Narrative coverage or memory retrieval is critically low.
- `DRIFT`: Significant change detected between processing windows.
- `UNKNOWN`: No recent data or initial state.

## 3. Interpreting Alerts

### 🔴 DEGRADATION (Narrative)
**Meaning:** The analyst has access to very few narrative events (< 0.2 score).
**Action:** Check if the GDELT pipeline is stuck or if the `normalized` dataset path is correctly configured.

### 🔴 DEGRADATION (Memory)
**Meaning:** No active memories are being retrieved from Qdrant.
**Action:** Verify Qdrant service is running at `http://localhost:6333` and that the `bitnin_episodes` collection has points.

### 🟡 DRIFT
**Meaning:** A sudden shift in metric distributions (e.g., a 50% drop in narrative support compared to yesterday).
**Action:** Review the latest scorecard in `verticals/bitnin/runtime/observability/scorecards/` to identify the source of the shift.

## 4. Recovery & Resume
The supervisor uses a lockfile (`bitnin_supervisor.lock`) to prevent concurrent runs.

### If a run fails:
1. Check logs for the specific `as_of` date that crashed.
2. The supervisor will automatically attempt to resume from the last successful date on the next invocation.
3. If a stale lock exists after a crash, the supervisor will remove it automatically.

## 5. Safety Guardrails
- **NEVER** disable `shadow_mode` or `dry_run` flags.
- BitNin has no access to private keys or API keys for trading.
- All "orders" generated are for audit purposes only and are archived in `runtime/shadow/`.
