from verticals.bitnin.services.bitnin_analyst.validate import (
    AnalysisOutputValidator,
    post_llm_guardrails,
    pre_llm_guardrail,
)


def test_pre_llm_guardrail_triggers_on_sparse_retrieval():
    context = {"data_coverage_score": 1.0, "narrative_coverage_score": 0.1}
    retrieval = {"episode_results": [{"score": 0.49}]}
    reasons = pre_llm_guardrail(context, retrieval)
    assert "top_episode_similarity_too_low" in reasons or "too_few_episode_analogues" in reasons
    assert "narrative_coverage_below_threshold" in reasons


def test_post_llm_guardrails_downgrade_directional_action():
    analysis = {
        "recommended_action": "long",
        "final_status": "ok",
        "confidence": 0.4,
        "why_not": [],
        "notes": [],
    }
    updated, notes = post_llm_guardrails(
        analysis,
        context={"narrative_coverage_score": 0.5},
        retrieval={"episode_results": [1, 2, 3]},
    )
    assert updated["recommended_action"] == "no_trade"
    assert updated["final_status"] == "no_trade"
    assert notes


def test_builder_coerces_string_fields_from_model():
    from verticals.bitnin.services.bitnin_analyst.builder import _coerce_string_list

    assert _coerce_string_list("salida provisional") == ["salida provisional"]
    assert _coerce_string_list(["a", "b"]) == ["a", "b"]


def test_analysis_output_schema_validator_accepts_valid_payload():
    payload = {
        "analysis_id": "abc123",
        "timestamp": "2026-03-13T23:00:00.000Z",
        "market_state": {
            "symbol": "BTCUSDT",
            "interval": "1d",
            "as_of": "2026-03-13T23:59:59.999Z",
            "close": 71212.0,
            "return_1d": 0.01,
            "return_3d": 0.03,
            "return_7d": 0.06,
            "volatility_regime": "medium",
            "breakout": True,
            "volume_anomaly": True,
            "summary": "BTCUSDT 1d close=71212.0"
        },
        "dominant_hypothesis": "Momentum con soporte narrativo moderado.",
        "supporting_factors": ["Breakout reciente", "Volumen elevado"],
        "counterarguments": ["Cobertura narrativa todavia limitada"],
        "retrieved_episodes": [
            {
                "episode_id": "ep_a",
                "score": 0.71,
                "summary_local": "Episodio previo con breakout.",
                "dominant_cause": "etf_institucional"
            }
        ],
        "confidence": 0.58,
        "recommended_action": "observe",
        "risk_level": "medium",
        "why_now": ["El mercado acaba de romper rango."],
        "why_not": ["Los analogos no son suficientes para una postura direccional."],
        "data_coverage_score": 1.0,
        "narrative_coverage_score": 0.46,
        "final_status": "ok",
        "model_name": "qwen2.5:14b",
        "prompt_version": "bitnin-analyst-v0",
        "dataset_versions": {
            "market": "market-v0-binance-1d",
            "narrative": "narrative-v0-gdelt",
            "episodes": "episodes-v0-real"
        },
        "query_refs": ["/tmp/query.json"],
        "notes": []
    }
    assert AnalysisOutputValidator().validate(payload) == []
