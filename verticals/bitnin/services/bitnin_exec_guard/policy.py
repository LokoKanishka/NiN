"""
Policy definitions for bitnin-exec-guard.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json

class GuardrailContext:
    def __init__(self, intent: Dict[str, Any], approval: Optional[Dict[str, Any]], analysis: Optional[Dict[str, Any]]):
        self.intent = intent
        self.approval = approval
        self.analysis = analysis

class GuardrailPolicy:
    """Hard guardrails that MUST pass for an execution request to be accepted (in dry_run)."""
    
    ALLOWED_ACTIONS = {"buy", "sell", "reduce", "exit", "hold", "no_trade"}
    ALLOWED_MODES = {"dry_run"}
    
    @classmethod
    def evaluate(cls, ctx: GuardrailContext) -> tuple[bool, List[str], List[str]]:
        """
        Evaluates the context against all hard guardrails.
        Returns: (is_valid, list of passed guards, list of failed guards)
        """
        passed = []
        failed = []
        
        # 1. Action allowed
        action = ctx.intent.get("action")
        if action in cls.ALLOWED_ACTIONS:
            passed.append("valid_action")
        else:
            failed.append(f"invalid_action:{action}")
            
        # 2. Intent Mode (Only simulated or shadow or dry_run. In phase 10, execution_mode must be dry_run for the executor)
        # Note: the prompt says the exec_guard ONLY allows dry_run. We will enforce this at executor level or intent level.
        # But for intent, mode could be 'simulation' or 'shadow'. We will just check it is not touching real money.
        intent_mode = ctx.intent.get("mode")
        if intent_mode in {"simulation", "shadow"}:
            passed.append("safe_intent_mode")
        else:
            failed.append(f"unsafe_intent_mode:{intent_mode}")
            
        # 3. Check Approval presence and status
        if not ctx.approval:
            failed.append("missing_approval")
        else:
            if ctx.approval.get("status") == "approved":
                passed.append("approval_status_approved")
            else:
                failed.append(f"approval_status_invalid:{ctx.approval.get('status')}")
                
        # 4. Expiration check
        valid_until_str = ctx.intent.get("valid_until")
        if not valid_until_str:
            failed.append("missing_valid_until")
        else:
            try:
                valid_until = datetime.fromisoformat(valid_until_str.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                if now <= valid_until:
                    passed.append("intent_not_expired")
                else:
                    failed.append("intent_expired")
            except ValueError:
                failed.append("invalid_date_format_valid_until")
                
        # 5. Must have reasoning_ref (from analysis)
        if ctx.intent.get("reasoning_ref"):
            passed.append("has_reasoning_ref")
        else:
            failed.append("missing_reasoning_ref")
            
        # 6. Check Analysis (optional but good if reasoning_ref points to it)
        if ctx.analysis:
            passed.append("analysis_provided")
        else:
            failed.append("missing_analysis_context")
            
        is_valid = len(failed) == 0
        return is_valid, passed, failed
