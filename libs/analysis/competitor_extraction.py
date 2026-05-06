"""Deterministic competitor candidate extraction.

This module is intentionally conservative: it only emits candidates when a
competitive context and a brand-like signal appear together. It does not call
LLMs and it does not persist full provider answers as evidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import urlparse

MIN_CONFIDENCE = 0.6
ANSWER_EXCERPT_LIMIT = 240

EN_CONTEXT_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("alternatives", re.compile(r"\balternatives?\s+to\b", re.IGNORECASE), "comparison"),
    ("competitors", re.compile(r"\bcompetitors?\s+of\b", re.IGNORECASE), "comparison"),
    ("vs", re.compile(r"\b(?:vs\.?|versus)\b", re.IGNORECASE), "comparison"),
    ("similar_tools", re.compile(r"\bsimilar\s+tools\b", re.IGNORECASE), "comparison"),
    (
        "similar_services",
        re.compile(r"\bsimilar\s+services\b", re.IGNORECASE),
        "comparison",
    ),
    ("best", re.compile(r"\bbest\s+[\w -]{2,80}", re.IGNORECASE), "category_list"),
    ("top", re.compile(r"\btop\s+[\w -]{2,80}", re.IGNORECASE), "category_list"),
)

RU_CONTEXT_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("alternatives_ru", re.compile(r"альтернатив", re.IGNORECASE), "comparison"),
    ("competitors_ru", re.compile(r"конкурент", re.IGNORECASE), "comparison"),
    ("similar_ru", re.compile(r"похож", re.IGNORECASE), "comparison"),
    (
        "similar_services_ru",
        re.compile(r"похожие\s+сервисы", re.IGNORECASE),
        "comparison",
    ),
    (
        "similar_companies_ru",
        re.compile(r"похожие\s+компании", re.IGNORECASE),
        "comparison",
    ),
    ("best_ru", re.compile(r"лучшие", re.IGNORECASE), "category_list"),
    ("top_ru", re.compile(r"\bтоп\b", re.IGNORECASE), "category_list"),
    ("comparison_ru", re.compile(r"сравнен", re.IGNORECASE), "comparison"),
    ("against_ru", re.compile(r"против", re.IGNORECASE), "comparison"),
)

DOMAIN_PATTERN = re.compile(
    r"\b(?:https?://)?(?:www\.)?([a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)+)\b",
    re.IGNORECASE,
)
BRAND_SPAN_PATTERN = re.compile(
    r"\b(?:[A-Z][A-Za-z0-9&'-]*|[А-ЯЁ][А-ЯЁа-яё0-9&'-]*)"
    r"(?:\s+(?:[A-Z][A-Za-z0-9&'-]*|[А-ЯЁ][А-ЯЁа-яё0-9&'-]*)){0,3}\b"
)
WEAK_BRAND_SUFFIX_PATTERN = re.compile(
    r"\b([A-Z][A-Za-z0-9&'-]*(?:\s+[A-Z][A-Za-z0-9&'-]*){0,2})"
    r"\s+(?:Inc|Corp|LLC|Ltd|AI|CRM|SaaS)\b"
)

GENERIC_CANDIDATES = {
    "best",
    "top",
    "alternatives",
    "competitors",
    "similar",
    "tools",
    "services",
    "software",
    "platform",
    "company",
    "companies",
    "solution",
    "solutions",
    "dance studio",
    "ballet classes",
    "children's programs",
    "лучшие",
    "топ",
    "альтернативы",
    "конкуренты",
    "похожие",
}

TITLE_STOPWORDS = {
    "The",
    "A",
    "An",
    "Best",
    "Top",
    "Alternative",
    "Alternatives",
    "Competitor",
    "Competitors",
    "Similar",
    "Compare",
    "Comparison",
    "Recommended",
    "Many",
    "Which",
    "What",
    "How",
}


class PreprocessedTextLike(Protocol):
    original: str


@dataclass(frozen=True)
class CompetitorMention:
    name: str
    mention_count: int = 1
    evidence_type: str = "legacy_phrase"


@dataclass(frozen=True)
class CompetitorExtractionInput:
    answer_text: str
    query_text: str = ""
    brand_name: str | None = None
    brand_domain: str | None = None
    known_competitors: tuple[str, ...] = ()
    query_id: int | None = None
    run_id: int | None = None
    target_id: int | None = None
    level: str | None = None
    model_id: str | None = None


@dataclass(frozen=True)
class CompetitorEvidence:
    query_id: int | None = None
    run_id: int | None = None
    target_id: int | None = None
    answer_excerpt: str = ""
    matched_phrase: str = ""
    evidence_type: str = "comparison"
    level: str | None = None
    model_id: str | None = None
    language: str | None = None
    pattern: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "query_id": self.query_id,
            "run_id": self.run_id,
            "target_id": self.target_id,
            "answer_excerpt": self.answer_excerpt,
            "matched_phrase": self.matched_phrase,
            "evidence_type": self.evidence_type,
            "level": self.level,
            "model_id": self.model_id,
            "language": self.language,
            "pattern": self.pattern,
        }


@dataclass(frozen=True)
class CompetitorCandidateExtraction:
    name: str
    domain: str | None
    confidence: float
    evidence_type: str
    evidence: tuple[CompetitorEvidence, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CompetitiveContext:
    language: str
    pattern: str
    evidence_type: str


def extract_competitor_candidates(
    payload: CompetitorExtractionInput,
) -> list[CompetitorCandidateExtraction]:
    text = f"{payload.query_text}\n{payload.answer_text}".strip()
    context = _competitive_context(text)
    if context is None:
        return []

    own_names = _own_brand_tokens(payload)
    candidates: dict[str, CompetitorCandidateExtraction] = {}
    for raw_name, domain, signal in _candidate_signals(payload):
        name = _clean_candidate_name(raw_name)
        if not _is_acceptable_candidate(name, own_names):
            continue
        confidence = _confidence(signal=signal, evidence_type=context.evidence_type)
        if confidence < MIN_CONFIDENCE:
            continue
        evidence = CompetitorEvidence(
            query_id=payload.query_id,
            run_id=payload.run_id,
            target_id=payload.target_id,
            answer_excerpt=_excerpt(payload.answer_text, name),
            matched_phrase=name,
            evidence_type=context.evidence_type,
            level=payload.level,
            model_id=payload.model_id,
            language=context.language,
            pattern=context.pattern,
        )
        normalized = name.casefold()
        previous = candidates.get(normalized)
        candidate = CompetitorCandidateExtraction(
            name=name,
            domain=domain,
            confidence=confidence,
            evidence_type=context.evidence_type,
            evidence=(evidence,),
        )
        if previous is None or candidate.confidence > previous.confidence:
            candidates[normalized] = candidate

    return sorted(candidates.values(), key=lambda item: (-item.confidence, item.name))


def extract_competitors(
    preprocessed: PreprocessedTextLike,
    brand_name: str,
) -> list[CompetitorMention]:
    """Legacy parser hook.

    The parser historically stores generic extracted "competitors" as JSON in
    ParsedResult. Phase U keeps this hook for backward compatibility; real
    competitor candidates are produced by extract_competitor_candidates().
    """
    own_names = {brand_name.casefold()} if brand_name else set()
    mentions: dict[str, CompetitorMention] = {}
    for match in BRAND_SPAN_PATTERN.finditer(preprocessed.original):
        name = _clean_candidate_name(match.group(0))
        if not _is_acceptable_candidate(name, own_names):
            continue
        normalized = name.casefold()
        if normalized in mentions:
            continue
        mentions[normalized] = CompetitorMention(name=name)
    return list(mentions.values())


def _competitive_context(text: str) -> CompetitiveContext | None:
    for language, patterns in (("en", EN_CONTEXT_PATTERNS), ("ru", RU_CONTEXT_PATTERNS)):
        for name, pattern, evidence_type in patterns:
            if pattern.search(text):
                return CompetitiveContext(
                    language=language,
                    pattern=name,
                    evidence_type=evidence_type,
                )
    return None


def _candidate_signals(
    payload: CompetitorExtractionInput,
) -> list[tuple[str, str | None, str]]:
    text = payload.answer_text
    signals: list[tuple[str, str | None, str]] = []
    for name in payload.known_competitors:
        if name and re.search(rf"\b{re.escape(name)}\b", text, re.IGNORECASE):
            signals.append((name, None, "known"))
    for domain in _domains(text):
        signals.append((_name_from_domain(domain), domain, "domain"))
    for match in WEAK_BRAND_SUFFIX_PATTERN.finditer(text):
        signals.append((match.group(1), None, "brand_like"))
    for match in BRAND_SPAN_PATTERN.finditer(text):
        signals.append((match.group(0), None, "brand_like"))
    return signals


def _domains(text: str) -> list[str]:
    domains: list[str] = []
    for match in DOMAIN_PATTERN.finditer(text):
        domain = match.group(1).lower().rstrip(".")
        parsed = urlparse(f"https://{domain}")
        if parsed.hostname and "." in parsed.hostname:
            domains.append(parsed.hostname)
    return domains


def _name_from_domain(domain: str) -> str:
    label = domain.split(".")[0].replace("-", " ").strip()
    return " ".join(part.capitalize() for part in label.split())


def _confidence(*, signal: str, evidence_type: str) -> float:
    # Deterministic formula from the contract:
    # known context=0.9, domain context=0.8,
    # brand-like+comparison=0.7, brand-like+category-list=0.5.
    # The category-list path stays conservative: only known/domain-backed names
    # pass the 0.6 threshold.
    if signal == "known" and evidence_type in {"comparison", "category_list"}:
        return 0.9
    if signal == "domain" and evidence_type in {"comparison", "category_list"}:
        return 0.8
    if signal == "brand_like" and evidence_type == "comparison":
        return 0.7
    if signal == "brand_like" and evidence_type == "category_list":
        return 0.5
    return 0.0


def _own_brand_tokens(payload: CompetitorExtractionInput) -> set[str]:
    tokens = set()
    if payload.brand_name:
        tokens.add(payload.brand_name.casefold())
    if payload.brand_domain:
        domain_label = payload.brand_domain.split(".")[0].replace("-", " ")
        tokens.add(domain_label.casefold())
    return tokens


def _clean_candidate_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip(" ,.;:()[]{}")).strip()


def _is_acceptable_candidate(name: str, own_names: set[str]) -> bool:
    if not name:
        return False
    normalized = name.casefold()
    if normalized in own_names or normalized in GENERIC_CANDIDATES:
        return False
    first_word = name.split()[0]
    if first_word in TITLE_STOPWORDS:
        return False
    if len(name) < 2 or len(name) > 80:
        return False
    if name.islower():
        return False
    return True


def _excerpt(answer_text: str, candidate: str) -> str:
    if not answer_text:
        return ""
    match = re.search(re.escape(candidate), answer_text, re.IGNORECASE)
    if match is None:
        return answer_text[:ANSWER_EXCERPT_LIMIT]
    start = max(match.start() - 80, 0)
    end = min(match.end() + 80, len(answer_text))
    return answer_text[start:end][:ANSWER_EXCERPT_LIMIT]
