from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import json

@dataclass
class MemoryUnit:
    run_id: str
    timestamp: str
    symbol: str
    interval: str
    market_summary: str
    narrative_summary: str
    data_coverage: float
    narrative_coverage: float
    recommended_action: str
    final_status: str
    confidence: float
    why_not: List[str]
    notes: List[str]
    outcome_operativo: str = "none"
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class MemoryBuilder:
    @staticmethod
    def from_artifacts(analysis: Dict[str, Any], record: Optional[Dict[str, Any]] = None) -> MemoryUnit:
        market = analysis.get("market_state", {})
        
        # Determine dominant cause from supporting/counter factors or notes if available
        narrative_summary = "Presence of market-only signals"
        if "notes" in analysis and analysis["notes"]:
            narrative_summary = analysis["notes"][0]
            
        outcome = "none"
        tags = [analysis.get("recommended_action", "no_trade"), analysis.get("final_status", "unknown")]
        
        if record:
            outcome = record.get("status", "unknown")
            if record.get("dry_run"):
                tags.append("dry_run")
            if record.get("rejection_reasons"):
                tags.extend(record.get("rejection_reasons"))

        return MemoryUnit(
            run_id=analysis.get("analysis_id", "unknown"),
            timestamp=analysis.get("timestamp", ""),
            symbol=market.get("symbol", "BTCUSDT"),
            interval=market.get("interval", "1d"),
            market_summary=market.get("summary", ""),
            narrative_summary=narrative_summary,
            data_coverage=analysis.get("data_coverage_score", 0.0),
            narrative_coverage=analysis.get("narrative_coverage_score", 0.0),
            recommended_action=analysis.get("recommended_action", "no_trade"),
            final_status=analysis.get("final_status", "unknown"),
            confidence=analysis.get("confidence", 0.0),
            why_not=analysis.get("why_not", []),
            notes=analysis.get("notes", []),
            outcome_operativo=outcome,
            tags=list(set(tags))  # Deduplicate tags
        )
