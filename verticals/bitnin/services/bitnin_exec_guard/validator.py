"""
Validator for bitnin-exec-guard.
"""
from typing import Dict, Any, Tuple
from verticals.bitnin.services.bitnin_exec_guard.policy import GuardrailPolicy, GuardrailContext

class ExecValidator:
    """Validates an intent + approval + analysis against the Policy."""
    
    @staticmethod
    def validate(intent: Dict[str, Any], approval: Dict[str, Any] = None, analysis: Dict[str, Any] = None) -> Tuple[bool, list, list]:
        """
        Runs the context through the GuardrailPolicy.
        Returns: (is_valid, passed_guards, blocking_guards)
        """
        ctx = GuardrailContext(intent=intent, approval=approval, analysis=analysis)
        is_valid, passed, failed = GuardrailPolicy.evaluate(ctx)
        return is_valid, passed, failed
