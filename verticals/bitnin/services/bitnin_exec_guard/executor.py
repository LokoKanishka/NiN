"""
Executor for bitnin-exec-guard.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from verticals.bitnin.services.bitnin_exec_guard.validator import ExecValidator

class ExecGuardExecutor:
    """
    Executes an intent in dry_run mode.
    Does not touch real money, wallets, or exchanges.
    """
    
    VERSION = "v1.0.0-dry_run"
    
    def __init__(self):
        pass

    def execute(self, intent: Dict[str, Any], approval: Dict[str, Any] = None, analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Receives an intent, validates it, and generates an execution_record.
        """
        is_valid, passed_guards, blocking_guards = ExecValidator.validate(
            intent=intent, approval=approval, analysis=analysis
        )
        
        exec_id = f"exec_{uuid.uuid4().hex[:12]}"
        now_str = datetime.now(timezone.utc).isoformat()
        
        status = "accepted_dry_run" if is_valid else "rejected"
        
        # If the intent itself is invalid structurally/expired
        if any(r.startswith("intent_expired") or r.startswith("invalid_date_format_valid_until") for r in blocking_guards):
            status = "expired"
        elif any(r.startswith("invalid_action") for r in blocking_guards):
            status = "invalid_intent"
        elif len(blocking_guards) > 0 and status != "expired" and status != "invalid_intent":
            status = "guardrail_blocked"
            
        record = {
            "execution_id": exec_id,
            "intent_id": intent.get("intent_id", "unknown"),
            "executed_at": now_str,
            "status": status,
            "execution_mode": "dry_run",
            "result_ref": f"local_sim_{exec_id}",
            "notes": "Simulacion de paso de guard. No es ejecucion financiera.",
            "validated_guards": passed_guards,
            "rejection_reasons": blocking_guards,
            "dry_run": True,
            "executor_version": self.VERSION
        }
        
        return record
