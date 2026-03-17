# BitNin Operational Runbook - Shadow Mode

## 1. Introduction
This document describes the operations for BitNin in `shadow + dry_run` mode. BitNin is currently in an analytical observation phase, focused on validating its composite signal and causal reasoning without financial execution.

## 2. Daily Operations
The system is designed to run periodically via the supervisor.

### Starting the Supervisor (Automated)
BitNin runs automatically via systemd. To manage the service:
```bash
# View status
systemctl --user status bitnin-shadow.timer
systemctl --user status bitnin-shadow.service

# View real-time logs
journalctl --user -u bitnin-shadow.service -f

# Force immediate execution
systemctl --user start bitnin-shadow.service
```

### Checking System Health
Inspect the human-readable snapshot for a quick status overview:
`verticals/bitnin/runtime/observability/history/health_snapshot.md`

The internal state is kept in `operational_state.json` (ignored by git) to ensure no runtime noise contaminates the repository.

## 3. Interpreting Alerts
... (keeping previous alerts) ...

## 5. Maintenance & Clean Runtime
- **Git Hygiene:** Never force-add `operational_state.json` or `*.lock` files to git.
- **Housekeeping:** Batch reports in `runtime/observability/batches/` can be archived or deleted periodically. Scorecards in `scorecards/` should be kept for audit.
- **Snapshot Monitoring:** `health_snapshot.md` is the primary source of truth for humans; if it reports `DEGRADED`, check the scorecards for details.

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
