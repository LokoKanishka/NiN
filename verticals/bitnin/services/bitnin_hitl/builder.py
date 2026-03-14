from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

if __package__ in (None, ""):
    REPO_ROOT = Path(__file__).resolve().parents[4]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from verticals.bitnin.services.bitnin_analyst.context import utc_now_iso  # type: ignore
    from verticals.bitnin.services.bitnin_hitl.approval import build_approval_request  # type: ignore
    from verticals.bitnin.services.bitnin_hitl.snapshot import write_hitl_snapshot  # type: ignore
    from verticals.bitnin.services.bitnin_hitl.state_machine import transition_approval  # type: ignore
    from verticals.bitnin.services.bitnin_hitl.telegram_message import build_telegram_approval_message  # type: ignore
else:
    from verticals.bitnin.services.bitnin_analyst.context import utc_now_iso
    from .approval import build_approval_request
    from .snapshot import write_hitl_snapshot
    from .state_machine import transition_approval
    from .telegram_message import build_telegram_approval_message


BITNIN_ROOT = Path(__file__).resolve().parents[2]
APPROVALS_ROOT = BITNIN_ROOT / "runtime" / "approvals"
REQUESTS_ROOT = APPROVALS_ROOT / "requests"
DECISIONS_ROOT = APPROVALS_ROOT / "decisions"
SNAPSHOTS_ROOT = APPROVALS_ROOT / "snapshots"
APPROVAL_SCHEMA = BITNIN_ROOT / "SCHEMAS" / "approval.schema.json"


class BitNinHitlRunner:
    def __init__(
        self,
        *,
        requests_root: Path | None = None,
        decisions_root: Path | None = None,
        snapshots_root: Path | None = None,
    ) -> None:
        self.requests_root = requests_root or REQUESTS_ROOT
        self.decisions_root = decisions_root or DECISIONS_ROOT
        self.snapshots_root = snapshots_root or SNAPSHOTS_ROOT
        for path in (self.requests_root, self.decisions_root, self.snapshots_root):
            path.mkdir(parents=True, exist_ok=True)
        self.validator = Draft202012Validator(
            json.loads(APPROVAL_SCHEMA.read_text(encoding="utf-8")),
            format_checker=Draft202012Validator.FORMAT_CHECKER,
        )

    def request(self, *, intent_path: str) -> dict[str, Any]:
        intent_file = Path(intent_path)
        intent = json.loads(intent_file.read_text(encoding="utf-8"))
        analysis = json.loads(Path(intent["reasoning_ref"]).read_text(encoding="utf-8"))
        approval = build_approval_request(
            intent=intent,
            shadow_ref=str(intent_file),
            timestamp=utc_now_iso(),
        )
        message = build_telegram_approval_message(approval=approval, intent=intent, analysis=analysis)
        approval["message_ref"] = f"telegram_webhook:{approval['approval_id']}"
        request_payload = {
            **approval,
            "rendered_message": message,
            "analysis_ref": intent["reasoning_ref"],
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
        request_path: str,
        decision: str,
        actor: str,
        notes: str = "",
    ) -> dict[str, Any]:
        request_file = Path(request_path)
        request_payload = json.loads(request_file.read_text(encoding="utf-8"))
        approval = {key: request_payload[key] for key in request_payload if key != "rendered_message" and key != "analysis_ref"}
        updated = transition_approval(
            approval,
            event=decision,
            actor=actor,
            timestamp=utc_now_iso(),
            notes=notes,
        )
        self._validate(updated)
        request_payload.update(updated)
        request_file.write_text(json.dumps(request_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        decision_payload = {
            **updated,
            "source_channel": updated["channel"],
        }
        decision_path = self.decisions_root / f"approval_decision__{updated['approval_id']}__{updated['status']}.json"
        decision_path.write_text(json.dumps(decision_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        snapshot_path = write_hitl_snapshot(
            snapshot_dir=self.snapshots_root,
            approval_id=updated["approval_id"],
            payload={"request": request_payload, "decision": decision_payload},
        )
        return {
            "request_path": str(request_file),
            "decision_path": str(decision_path),
            "snapshot_path": str(snapshot_path),
        }

    def expire(self, *, request_path: str) -> dict[str, Any]:
        request_file = Path(request_path)
        request_payload = json.loads(request_file.read_text(encoding="utf-8"))
        approval = {key: request_payload[key] for key in request_payload if key != "rendered_message" and key != "analysis_ref"}
        updated = transition_approval(
            approval,
            event="expire",
            actor="system_expirer",
            timestamp=utc_now_iso(),
            notes="Approval expired without human decision.",
        )
        self._validate(updated)
        request_payload.update(updated)
        request_file.write_text(json.dumps(request_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        decision_path = self.decisions_root / f"approval_decision__{updated['approval_id']}__expired.json"
        decision_path.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        snapshot_path = write_hitl_snapshot(
            snapshot_dir=self.snapshots_root,
            approval_id=updated["approval_id"],
            payload={"request": request_payload, "expired": updated},
        )
        return {
            "request_path": str(request_file),
            "decision_path": str(decision_path),
            "snapshot_path": str(snapshot_path),
        }

    def _validate(self, payload: dict[str, Any]) -> None:
        errors = sorted(error.message for error in self.validator.iter_errors(payload))
        if errors:
            raise ValueError(json.dumps(errors, indent=2, ensure_ascii=False))


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BitNin HITL runner")
    parser.add_argument("--intent-path")
    parser.add_argument("--request-path")
    parser.add_argument("--decision", choices=["approve", "reject"])
    parser.add_argument("--actor", default="human_operator")
    parser.add_argument("--notes", default="")
    parser.add_argument("--expire", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_cli_parser()
    args = parser.parse_args(argv)
    runner = BitNinHitlRunner()
    if args.intent_path:
        result = runner.request(intent_path=args.intent_path)
    elif args.request_path and args.decision:
        result = runner.decide(
            request_path=args.request_path,
            decision=args.decision,
            actor=args.actor,
            notes=args.notes,
        )
    elif args.request_path and args.expire:
        result = runner.expire(request_path=args.request_path)
    else:
        parser.error("Provide --intent-path, or --request-path with --decision/--expire")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

