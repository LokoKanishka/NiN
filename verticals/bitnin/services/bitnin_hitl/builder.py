from __future__ import annotations

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from verticals.bitnin.services.bitnin_analyst.context import utc_now_iso
from verticals.bitnin.services.bitnin_hitl.approval import build_approval_request
from verticals.bitnin.services.bitnin_hitl.snapshot import write_hitl_snapshot
from verticals.bitnin.services.bitnin_hitl.telegram_message import build_telegram_approval_message
from verticals.bitnin.services.validator_fallback import BasicValidatorFallback

logger = logging.getLogger("bitnin.hitl")

class BitNinHitlRunner:
    def __init__(
        self,
        *,
        requests_root: Path,
        decisions_root: Path,
        snapshots_root: Path,
    ):
        self.requests_root = requests_root
        self.decisions_root = decisions_root
        self.snapshots_root = snapshots_root
        
        for path in [self.requests_root, self.decisions_root, self.snapshots_root]:
            path.mkdir(parents=True, exist_ok=True)
        self.validator = BasicValidatorFallback(None)

    def _validate(self, instance: dict[str, Any]):
        errors = self.validator.iter_errors(instance)
        msgs = [str(e) for e in errors]
        if msgs:
            raise ValueError(f"HITL Validation failed: {msgs}")

    def request(self, *, intent_path: str, expires_at: str | None = None, run_id: str | None = None) -> dict[str, Any]:
        intent_file = Path(intent_path)
        if not intent_file.exists():
            raise FileNotFoundError(f"Intent file not found: {intent_path}")
        
        intent_data = json.loads(intent_file.read_text(encoding="utf-8"))
        
        # Default expiration: 1 hour if not provided
        if not expires_at:
            expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
        
        approval = build_approval_request(
            intent=intent_data,
            shadow_ref=str(intent_file),
            timestamp=utc_now_iso(),
            expires_at=expires_at,
        )
        approval["status"] = "awaiting_human_approval"
        
        if run_id:
            approval["approval_id"] = run_id
        
        analysis_data = json.loads(Path(intent_data["reasoning_ref"]).read_text(encoding="utf-8"))
        message = build_telegram_approval_message(approval=approval, intent=intent_data, analysis=analysis_data)
        approval["message_ref"] = f"telegram_webhook:{approval['approval_id']}"
        
        request_payload = {
            **approval,
            "rendered_message": message,
            "analysis_ref": intent_data["reasoning_ref"],
        }
        
        self._validate(approval)
        request_path = self.requests_root / f"approval_request__{approval['approval_id']}.json"
        request_path.write_text(json.dumps(request_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        
        snapshot_path = write_hitl_snapshot(
            snapshot_dir=self.snapshots_root,
            approval_id=approval["approval_id"],
            payload={"request": request_payload},
        )
        
        return {
            "approval_id": approval["approval_id"],
            "request_path": str(request_path),
            "snapshot_path": str(snapshot_path),
        }

    def decide(
        self,
        *,
        approval_id: str,
        decision: str,
        actor: str,
        notes: str = "",
    ) -> dict[str, Any]:
        request_path = self.requests_root / f"approval_request__{approval_id}.json"
        if not request_path.exists():
            raise FileNotFoundError(f"Approval request not found: {approval_id}")
            
        request_payload = json.loads(request_path.read_text(encoding="utf-8"))
        approval = {key: request_payload[key] for key in request_payload if key not in ["rendered_message", "analysis_ref"]}
        
        # Check expiration
        now_dt = datetime.fromisoformat(utc_now_iso().replace("Z", "+00:00"))
        exp_dt = datetime.fromisoformat(approval["expires_at"].replace("Z", "+00:00"))
        if now_dt > exp_dt:
            return self.expire(approval_id=approval_id)

        approval["status"] = decision if decision in ["approved", "rejected"] else "decided"
        approval["decision"] = decision
        approval["actor"] = actor
        approval["notes"] = notes
        approval["decided_at"] = utc_now_iso()

        decision_path = self.decisions_root / f"approval_decision__{approval_id}__{decision}.json"
        decision_path.write_text(json.dumps(approval, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        
        snapshot_path = write_hitl_snapshot(
            snapshot_dir=self.snapshots_root,
            approval_id=approval_id,
            payload={"decision": approval},
        )
        return {
            "approval_id": approval_id,
            "status": approval["status"],
            "decision_path": str(decision_path),
            "snapshot_path": str(snapshot_path),
        }

    def expire(self, *, approval_id: str) -> dict[str, Any]:
        request_path = self.requests_root / f"approval_request__{approval_id}.json"
        if not request_path.exists():
            raise FileNotFoundError(f"Approval request not found for expiration: {approval_id}")
            
        request_payload = json.loads(request_path.read_text(encoding="utf-8"))
        approval = {key: request_payload[key] for key in request_payload if key not in ["rendered_message", "analysis_ref"]}
        
        approval["status"] = "expired"
        approval["decision"] = "expired"
        approval["actor"] = "system_timer"
        approval["decided_at"] = utc_now_iso()

        decision_path = self.decisions_root / f"approval_decision__{approval_id}__expired.json"
        decision_path.write_text(json.dumps(approval, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        
        return {
            "approval_id": approval_id,
            "status": "expired",
            "decision_path": str(decision_path),
        }
