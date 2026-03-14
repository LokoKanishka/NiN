from verticals.bitnin.services.bitnin_narrative_builder.classify import classify_topics, extract_entities, score_relevance_btc


def test_classify_topics_and_relevance():
    text = "BlackRock Bitcoin ETF inflows rise while the SEC reviews regulation."
    topics = classify_topics(text)
    assert "etf_institucional" in topics
    assert "regulacion" in topics
    assert score_relevance_btc(text, topics) >= 0.7


def test_extract_entities_returns_known_names():
    entities = extract_entities("Bitcoin ETF flows lift BlackRock and SEC headlines")
    assert "Bitcoin" in entities
