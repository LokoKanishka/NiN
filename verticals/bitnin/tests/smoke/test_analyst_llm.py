from verticals.bitnin.services.bitnin_analyst.llm import _extract_json


def test_extract_json_accepts_markdown_wrapped_payload():
    payload = """```json
{"dominant_hypothesis":"x","supporting_factors":["a"],"counterarguments":["b"],"confidence":0.4,"recommended_action":"no_trade","risk_level":"medium","why_now":["now"],"why_not":["not"],"final_status":"insufficient_evidence","notes":[]}
```"""
    parsed = _extract_json(payload)
    assert parsed["recommended_action"] == "no_trade"
    assert parsed["final_status"] == "insufficient_evidence"

