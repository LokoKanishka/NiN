from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    REPO_ROOT = Path(__file__).resolve().parents[4]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from verticals.bitnin.services.bitnin_analyst.context import CurrentContextBuilder  # type: ignore
    from verticals.bitnin.services.bitnin_analyst.llm import OllamaAnalystClient  # type: ignore
    from verticals.bitnin.services.bitnin_analyst.prompts import PROMPT_VERSION, build_messages  # type: ignore
    from verticals.bitnin.services.bitnin_analyst.retrieve import AnalystRetriever  # type: ignore
    from verticals.bitnin.services.bitnin_analyst.snapshot import write_snapshot  # type: ignore
    from verticals.bitnin.services.bitnin_analyst.validate import (  # type: ignore
        AnalysisOutputValidator,
        normalize_retrieved_episodes,
        post_llm_guardrails,
        pre_llm_guardrail,
    )
else:
    from .context import CurrentContextBuilder
    from .llm import OllamaAnalystClient
    from .prompts import PROMPT_VERSION, build_messages
    from .retrieve import AnalystRetriever
    from .snapshot import write_snapshot
    from .validate import (
        AnalysisOutputValidator,
        normalize_retrieved_episodes,
        post_llm_guardrails,
        pre_llm_guardrail,
    )


BITNIN_ROOT = Path(__file__).resolve().parents[2]
ANALYSES_ROOT = BITNIN_ROOT / "runtime" / "analyses"
RAW_ROOT = ANALYSES_ROOT / "raw"
NORMALIZED_ROOT = ANALYSES_ROOT / "normalized"
SNAPSHOT_ROOT = ANALYSES_ROOT / "snapshots"


def _stable_analysis_id(
    *,
    symbol: str,
    interval: str,
    as_of: str,
    dataset_versions: dict[str, str],
    prompt_version: str,
) -> str:
    seed = json.dumps(
        {
            "symbol": symbol,
            "interval": interval,
            "as_of": as_of,
            "dataset_versions": dataset_versions,
            "prompt_version": prompt_version,
        },
        sort_keys=True,
    )
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def _build_insufficient_analysis(
    *,
    analysis_id: str,
    context: dict[str, Any],
    retrieval: dict[str, Any],
    reasons: list[str],
    model_name: str,
) -> dict[str, Any]:
    return {
        "analysis_id": analysis_id,
        "timestamp": context["analysis_timestamp"],
        "market_state": context["market_state"],
        "dominant_hypothesis": "La evidencia disponible no alcanza para sostener una hipotesis operativa confiable.",
        "supporting_factors": [
            "El contexto actual fue construido correctamente pero la cobertura no alcanza el umbral operativo.",
        ],
        "counterarguments": [
            "Podrian existir analogos utiles fuera del retrieval actual o narrativa adicional no incorporada.",
        ],
        "retrieved_episodes": normalize_retrieved_episodes(retrieval["episode_results"][:3]),
        "confidence": 0.2,
        "recommended_action": "no_trade",
        "risk_level": "unknown",
        "why_now": ["El mercado actual merece observacion, pero no decision operativa."],
        "why_not": sorted(set(reasons)),
        "data_coverage_score": context["data_coverage_score"],
        "narrative_coverage_score": context["narrative_coverage_score"],
        "final_status": "insufficient_evidence",
        "model_name": model_name,
        "prompt_version": PROMPT_VERSION,
        "dataset_versions": context["dataset_versions"],
        "query_refs": retrieval["query_refs"],
        "composite_signal": retrieval.get("composite_signal", {}),
        "active_memory": retrieval.get("active_memories", []),
        "notes": ["Pre-LLM guardrail activado."],
    }


def _coerce_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    return [str(item) for item in value]


class BitNinAnalyst:
    def __init__(
        self,
        *,
        context_builder: CurrentContextBuilder | None = None,
        retriever: AnalystRetriever | None = None,
        llm_client: OllamaAnalystClient | None = None,
        raw_root: Path | None = None,
        normalized_root: Path | None = None,
        snapshot_root: Path | None = None,
    ) -> None:
        self.raw_root = raw_root or RAW_ROOT
        self.normalized_root = normalized_root or NORMALIZED_ROOT
        self.snapshot_root = snapshot_root or SNAPSHOT_ROOT
        for path in (self.raw_root, self.normalized_root, self.snapshot_root):
            path.mkdir(parents=True, exist_ok=True)
        self.context_builder = context_builder or CurrentContextBuilder()
        self.retriever = retriever or AnalystRetriever(raw_root=self.raw_root)
        self.llm_client = llm_client or OllamaAnalystClient()
        self.validator = AnalysisOutputValidator()

    def build(
        self,
        *,
        symbol: str = "BTCUSDT",
        interval: str = "1d",
        top_k_episodes: int = 5,
        top_k_events: int = 5,
        as_of: str | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        context = self.context_builder.build(
            symbol=symbol,
            interval=interval,
            as_of=as_of,
        )
        if run_id:
            analysis_id = run_id
        else:
            analysis_id = _stable_analysis_id(
                symbol=symbol,
                interval=interval,
                as_of=context["market_state"]["as_of"],
                dataset_versions=context["dataset_versions"],
                prompt_version=PROMPT_VERSION,
            )
        retrieval = self.retriever.retrieve(
            analysis_id=analysis_id,
            context=context,
            top_k_episodes=top_k_episodes,
            top_k_events=top_k_events,
        )

        try:
            from verticals.bitnin.services.bitnin_active_memory.retrieve import ActiveMemoryRetriever
            active_mem_retriever = ActiveMemoryRetriever()
            retrieval["active_memories"] = active_mem_retriever.retrieve(context, top_k=3)
        except Exception as e:
            # We don't want to break the analyst if active memory fails
            print(f"Warning: Active memory retrieval failed: {e}")
            retrieval["active_memories"] = []

        # Calculate composite signal
        retrieval["composite_signal"] = self._calculate_composite_signal(context=context, retrieval=retrieval)

        pre_guardrail_reasons = pre_llm_guardrail(context, retrieval)
        llm_result = None
        messages = None
        if pre_guardrail_reasons:
            analysis = _build_insufficient_analysis(
                analysis_id=analysis_id,
                context=context,
                retrieval=retrieval,
                reasons=pre_guardrail_reasons,
                model_name=self.llm_client.model,
            )
        else:
            messages = build_messages(context=context, retrieval=retrieval)
            try:
                llm_result = self.llm_client.analyze(messages=messages)
                analysis = self._merge_llm_output(
                    analysis_id=analysis_id,
                    context=context,
                    retrieval=retrieval,
                    llm_output=llm_result.parsed_output,
                    model_name=llm_result.model_name,
                )
            except Exception as exc:  # pragma: no cover - exercised in real runtime fallback
                analysis = _build_insufficient_analysis(
                    analysis_id=analysis_id,
                    context=context,
                    retrieval=retrieval,
                    reasons=[f"llm_failure:{exc.__class__.__name__}"],
                    model_name=self.llm_client.model,
                )

        analysis, guardrail_notes = post_llm_guardrails(analysis, context=context, retrieval=retrieval)
        errors = self.validator.validate(analysis)
        if errors:
            raise ValueError(json.dumps({"analysis_id": analysis_id, "schema_errors": errors}, indent=2, ensure_ascii=False))

        raw_payload = {
            "analysis_id": analysis_id,
            "context": context,
            "retrieval": retrieval,
            "prompt_version": PROMPT_VERSION,
            "model_name": self.llm_client.model,
            "messages": messages,
            "llm_raw_response": llm_result.raw_response if llm_result else None,
            "guardrail_notes": guardrail_notes,
        }
        raw_path = self.raw_root / f"analysis_raw__{symbol}__{interval}__{analysis_id}.json"
        raw_path.write_text(json.dumps(raw_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        normalized_path = self.normalized_root / f"analysis__{symbol}__{interval}__{analysis_id}.json"
        normalized_path.write_text(json.dumps(analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        snapshot_path = write_snapshot(
            snapshot_dir=self.snapshot_root,
            analysis=analysis,
            raw_ref=str(raw_path),
            normalized_ref=str(normalized_path),
        )
        return {
            "analysis_id": analysis_id,
            "raw_path": str(raw_path),
            "normalized_path": str(normalized_path),
            "snapshot_path": str(snapshot_path),
            "model_name": analysis["model_name"],
            "prompt_version": analysis["prompt_version"],
            "final_status": analysis["final_status"],
            "recommended_action": analysis["recommended_action"],
            "composite_signal": analysis.get("composite_signal", {}),
        }

    def _calculate_composite_signal(
        self,
        *,
        context: dict[str, Any],
        retrieval: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculates a structured convergence signal."""
        # Market Strength (0.3)
        m_state = context.get("market_state", {})
        m_score = 0.5 if m_state.get("breakout") else 0.3
        m_score += min(abs(m_state.get("return_1d", 0)) * 5, 0.5)
        
        # Narrative Support (0.4)
        n_score = context.get("narrative_coverage_score", 0)
        
        # Memory Relevance (0.3)
        memories = retrieval.get("active_memories", [])
        mem_score = max([m.get("score", 0) for m in memories]) if memories else 0
        
        # Final convergence
        convergence = (m_score * 0.3) + (n_score * 0.4) + (mem_score * 0.3)
        
        # Causal Typology
        typology = "evidencia_insuficiente"
        if n_score < 0.15:
            typology = "narrativa_ausente"
        elif n_score < 0.4 and m_score > 0.6:
            typology = "mercado_fuerte_narrativa_debil"
        elif n_score > 0.5 and m_score < 0.4:
            typology = "narrativa_fuerte_mercado_debil"
        elif convergence < 0.4:
            typology = "ruido_predominante"
        
        return {
            "market_strength": round(float(m_score), 4),
            "narrative_support": round(float(n_score), 4),
            "memory_relevance": round(float(mem_score), 4),
            "convergence_score": round(float(convergence), 4),
            "state": "HIGH" if convergence > 0.7 else ("DIVERGENT" if convergence > 0.4 else "LOW"),
            "causal_typology": typology
        }

    def _merge_llm_output(
        self,
        *,
        analysis_id: str,
        context: dict[str, Any],
        retrieval: dict[str, Any],
        llm_output: dict[str, Any],
        model_name: str,
    ) -> dict[str, Any]:
        analysis = {
            "analysis_id": analysis_id,
            "timestamp": context["analysis_timestamp"],
            "market_state": context["market_state"],
            "dominant_hypothesis": str(llm_output["dominant_hypothesis"]),
            "supporting_factors": _coerce_string_list(llm_output["supporting_factors"]),
            "counterarguments": _coerce_string_list(llm_output["counterarguments"]),
            "retrieved_episodes": normalize_retrieved_episodes(retrieval["episode_results"][:3]),
            "confidence": round(float(llm_output["confidence"]), 6),
            "recommended_action": str(llm_output["recommended_action"]),
            "risk_level": str(llm_output["risk_level"]),
            "why_now": _coerce_string_list(llm_output["why_now"]),
            "why_not": _coerce_string_list(llm_output["why_not"]),
            "data_coverage_score": context["data_coverage_score"],
            "narrative_coverage_score": context["narrative_coverage_score"],
            "final_status": str(llm_output["final_status"]),
            "model_name": model_name,
            "prompt_version": PROMPT_VERSION,
            "dataset_versions": context["dataset_versions"],
            "query_refs": retrieval["query_refs"],
            "composite_signal": retrieval.get("composite_signal", {}),
            "active_memory": retrieval.get("active_memories", []),
            "notes": _coerce_string_list(llm_output.get("notes", [])),
        }
        return analysis


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BitNin structured analyst")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--top-k-episodes", type=int, default=5)
    parser.add_argument("--top-k-events", type=int, default=5)
    parser.add_argument("--run-id", type=str, default=None)
    parser.add_argument("--as-of", type=str, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_cli_parser()
    args = parser.parse_args(argv)
    result = BitNinAnalyst().build(
        symbol=args.symbol,
        interval=args.interval,
        top_k_episodes=args.top_k_episodes,
        top_k_events=args.top_k_events,
        run_id=args.run_id,
        as_of=args.as_of,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
