from __future__ import annotations

import re


TOPIC_KEYWORDS = {
    "macro_monetaria": [
        "fed",
        "fomc",
        "central bank",
        "interest rate",
        "inflation",
        "cpi",
        "yield",
        "liquidity",
    ],
    "regulacion": [
        "sec",
        "regulator",
        "regulation",
        "regulatory",
        "law",
        "compliance",
        "ban",
        "lawsuit",
    ],
    "etf_institucional": [
        "etf",
        "blackrock",
        "fidelity",
        "grayscale",
        "institutional",
        "asset manager",
    ],
    "exchange_infraestructura": [
        "exchange",
        "binance",
        "coinbase",
        "kraken",
        "custody",
        "infrastructure",
        "outage",
    ],
    "hack_security": [
        "hack",
        "breach",
        "exploit",
        "vulnerability",
        "stolen",
        "cyber",
        "security",
    ],
    "liquidaciones": [
        "liquidation",
        "liquidations",
        "leveraged",
        "margin call",
        "short squeeze",
        "long squeeze",
    ],
    "geopolitica": [
        "sanction",
        "war",
        "conflict",
        "tariff",
        "trade war",
        "election",
        "government",
    ],
    "sentimiento_social": [
        "social media",
        "retail",
        "viral",
        "sentiment",
        "reddit",
        "x.com",
        "twitter",
        "meme",
    ],
    "halving_mineria": [
        "halving",
        "miner",
        "mining",
        "hashrate",
        "difficulty",
        "block reward",
    ],
    "stablecoins": [
        "stablecoin",
        "usdt",
        "usdc",
        "tether",
        "circle",
        "depeg",
    ],
    "riesgo_global": [
        "recession",
        "crisis",
        "credit risk",
        "bank failure",
        "default",
        "volatility spike",
        "risk-off",
    ],
}


KNOWN_ENTITY_PATTERNS = [
    r"\bBTC\b",
    r"\bBitcoin\b",
    r"\bBinance\b",
    r"\bCoinbase\b",
    r"\bSEC\b",
    r"\bETF\b",
    r"\bFed\b",
    r"\bBlackRock\b",
    r"\bTether\b",
    r"\bUSDT\b",
    r"\bUSDC\b",
]


def classify_topics(text: str) -> list[str]:
    haystack = text.lower()
    topics = [
        topic
        for topic, keywords in TOPIC_KEYWORDS.items()
        if any(keyword in haystack for keyword in keywords)
    ]
    return sorted(set(topics))


def extract_entities(text: str) -> list[str]:
    entities: set[str] = set()
    for pattern in KNOWN_ENTITY_PATTERNS:
        entities.update(re.findall(pattern, text, flags=re.IGNORECASE))

    title_case_matches = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b", text)
    for match in title_case_matches:
        if len(match) > 2:
            entities.add(match)

    cleaned = sorted({entity.strip() for entity in entities if entity.strip()})
    return cleaned[:12]


def score_relevance_btc(text: str, topics: list[str]) -> float:
    haystack = text.lower()
    score = 0.0

    if "bitcoin" in haystack or re.search(r"\bbtc\b", haystack):
        score += 0.55
    if "crypto" in haystack or "cryptocurrency" in haystack:
        score += 0.15
    if any(topic in topics for topic in {"etf_institucional", "stablecoins", "halving_mineria", "exchange_infraestructura"}):
        score += 0.15
    if any(topic in topics for topic in {"macro_monetaria", "riesgo_global", "regulacion"}):
        score += 0.1

    return round(min(score, 1.0), 3)


def score_confidence_source(article: dict) -> float:
    populated = 0
    for field_name in ("url", "title", "domain", "language", "sourcecountry", "seendate"):
        if article.get(field_name):
            populated += 1
    if article.get("socialimage"):
        populated += 1

    return round(min(0.3 + populated * 0.1, 1.0), 3)


def build_summary_local(
    *,
    title: str,
    source_name: str,
    timestamp_start: str,
    topics: list[str],
    relevance_btc: float,
    confidence_source: float,
) -> str:
    if not title:
        return (
            f"Candidato narrativo detectado por GDELT desde {source_name} en {timestamp_start}. "
            f"Cobertura baja; resumen basado solo en metadata permitida."
        )

    topic_text = ", ".join(topics) if topics else "sin topico dominante claro"
    if confidence_source < 0.55:
        coverage_note = "Cobertura baja; resumen austero basado solo en metadata permitida."
    else:
        coverage_note = "Resumen local basado en metadata permitida del discovery."

    return (
        f"{title}. Fuente detectada: {source_name}. "
        f"Topicos iniciales: {topic_text}. "
        f"Relevancia BTC estimada: {relevance_btc:.2f}. {coverage_note}"
    )
