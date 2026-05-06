"""Draft-safe seed query generation service."""

from __future__ import annotations

import json
import logging
import os
import re
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from libs.execution.openai_config import (
    OpenAIConfigError,
    OpenAIProviderConfig,
    load_openai_provider_config,
)
from libs.execution.openai_provider import OpenAIResponsesClient
from libs.execution.paa_config import load_paa_provider_config
from libs.execution.paa_provider import (
    PeopleAlsoAskProvider,
    PeopleAlsoAskQuestion,
    build_paa_provider,
)
from libs.storage.models import SeedQuerySource, SeedQueryType

logger = logging.getLogger(__name__)

SeedQueryProviderMode = Literal["mock", "openai"]
ProviderCallable = Callable[[str], Awaitable[str]]

DEFAULT_GENERATED_QUERY_COUNT = 10
MAX_GENERATED_QUERY_COUNT = 10
MAX_TOTAL_SEED_QUERY_COUNT = 20
GENERATION_UNAVAILABLE_WARNING = "Seed query generation is currently unavailable."
DOMAIN_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)


class SeedQueryGenerationConfigError(ValueError):
    """Raised when seed query generation configuration is invalid."""


class SeedQueryGenerationUnavailable(RuntimeError):
    """Raised when generation is disabled or provider configuration is unavailable."""


class SeedQueryJSONProvider(Protocol):
    async def generate(self, prompt: str) -> str:
        """Return provider JSON text for seed query suggestions."""


@dataclass(frozen=True)
class SeedQueryGenerationConfig:
    enabled: bool = False
    provider: SeedQueryProviderMode = "mock"
    model: str = "gpt-4.1-mini"
    timeout_seconds: float = 30.0


@dataclass(frozen=True)
class SeedQueryDraft:
    text: str
    type: str | None = None
    source: str = SeedQuerySource.USER.value


@dataclass(frozen=True)
class GenerateSeedQueriesInput:
    brand_name: str | None = None
    brand_domain: str | None = None
    brand_description: str | None = None
    use_domain: bool = False
    use_description: bool = False
    use_paa: bool = False
    language: str | None = None
    country: str | None = None
    paa_seed_query: str | None = None
    count: int = DEFAULT_GENERATED_QUERY_COUNT
    existing_queries: list[SeedQueryDraft] = field(default_factory=list)


@dataclass(frozen=True)
class GeneratedSeedQuerySuggestion:
    text: str
    type: str
    source: str = SeedQuerySource.AI.value
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GeneratedSeedQueriesResult:
    suggestions: list[GeneratedSeedQuerySuggestion] = field(default_factory=list)
    skipped_duplicates: int = 0
    skipped_limit: int = 0
    warnings: list[str] = field(default_factory=list)


class OpenAISeedQueryJSONProvider:
    """OpenAI Responses API JSON provider for seed query generation."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float,
        client: OpenAIResponsesClient | None = None,
    ) -> None:
        self.model = model
        self.client = client or OpenAIResponsesClient(
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )

    async def generate(self, prompt: str) -> str:
        response = await self.client.create_response(
            model=self.model,
            input=prompt,
            max_output_tokens=1200,
        )
        output_text = _get_attr_or_key(response, "output_text")
        if isinstance(output_text, str):
            return output_text
        return json.dumps(_to_json_safe(response))


class MockSeedQueryJSONProvider:
    """Deterministic JSON provider for local development and tests."""

    async def generate(self, prompt: str) -> str:
        del prompt
        return json.dumps(
            {
                "queries": [
                    {"text": text, "type": query_type}
                    for text, query_type in _mock_seed_query_pairs()
                ]
            }
        )


async def generate_seed_query_suggestions(
    payload: GenerateSeedQueriesInput,
    *,
    provider: SeedQueryJSONProvider | ProviderCallable | None = None,
    paa_provider: PeopleAlsoAskProvider | None = None,
    config: SeedQueryGenerationConfig | None = None,
) -> GeneratedSeedQueriesResult:
    """Generate typed seed query suggestions without persisting them."""

    try:
        normalized_payload = _validate_generation_input(payload)
    except ValueError as exc:
        raise SeedQueryGenerationConfigError(str(exc)) from exc

    existing_keys = {
        _query_key(query.text)
        for query in normalized_payload.existing_queries
        if _is_valid_existing_query(query)
    }
    available_slots = MAX_TOTAL_SEED_QUERY_COUNT - len(existing_keys)
    if available_slots <= 0:
        return GeneratedSeedQueriesResult(
            suggestions=[],
            skipped_limit=normalized_payload.count,
            warnings=["Seed query limit is already reached."],
        )

    combined = GeneratedSeedQueriesResult()
    seen = set(existing_keys)
    available_for_ai = available_slots

    if normalized_payload.use_domain or normalized_payload.use_description:
        resolved_provider = provider or _build_provider(config)
        prompt = _build_prompt(normalized_payload)

        try:
            raw_output = await _call_provider(resolved_provider, prompt)
        except Exception:
            logger.warning("Seed query provider call failed.", exc_info=True)
            ai_result = _unavailable_result()
        else:
            ai_result = _suggestions_from_provider_output(
                raw_output=raw_output,
                requested_count=normalized_payload.count,
                existing_keys=seen,
                available_slots=available_for_ai,
            )
        combined = _merge_generation_results(combined, ai_result, seen=seen)

    if normalized_payload.use_paa:
        paa_result = await _generate_paa_suggestions(
            normalized_payload,
            paa_provider=paa_provider,
            seen=seen,
            available_slots=MAX_TOTAL_SEED_QUERY_COUNT - len(seen),
        )
        combined = _merge_generation_results(combined, paa_result, seen=seen)

    return combined


def load_seed_query_generation_config(
    env: Mapping[str, str] | None = None,
) -> SeedQueryGenerationConfig:
    source = os.environ if env is None else env
    provider = source.get("SEED_QUERY_GENERATION_PROVIDER") or source.get(
        "PROVIDER_MODE",
        "mock",
    )
    normalized_provider = provider.strip().lower()
    if normalized_provider not in {"mock", "openai"}:
        raise SeedQueryGenerationConfigError(
            "SEED_QUERY_GENERATION_PROVIDER must be 'mock' or 'openai'."
        )
    return SeedQueryGenerationConfig(
        enabled=_load_bool(source, "SEED_QUERY_GENERATION_ENABLED", False),
        provider=normalized_provider,  # type: ignore[arg-type]
        model=_load_optional_text(source, "SEED_QUERY_GENERATION_MODEL") or "gpt-4.1-mini",
        timeout_seconds=_load_positive_float(
            source,
            "SEED_QUERY_GENERATION_TIMEOUT_SECONDS",
            30.0,
        ),
    )


def _validate_generation_input(
    payload: GenerateSeedQueriesInput,
) -> GenerateSeedQueriesInput:
    if payload.count > MAX_GENERATED_QUERY_COUNT:
        raise ValueError("count must be less than or equal to 10.")
    if payload.count <= 0:
        raise ValueError("count must be greater than 0.")
    if not payload.use_domain and not payload.use_description and not payload.use_paa:
        raise ValueError("At least one generation source must be selected.")

    brand_domain = _normalize_optional_text(payload.brand_domain)
    brand_description = _normalize_optional_text(payload.brand_description)
    brand_name = _normalize_optional_text(payload.brand_name)

    if payload.use_domain:
        if brand_domain is None:
            raise ValueError("brand_domain is required when use_domain is true.")
        brand_domain = _normalize_domain(brand_domain)

    if payload.use_description and brand_description is None:
        raise ValueError("brand_description is required when use_description is true.")

    return GenerateSeedQueriesInput(
        brand_name=brand_name,
        brand_domain=brand_domain,
        brand_description=brand_description,
        use_domain=payload.use_domain,
        use_description=payload.use_description,
        use_paa=payload.use_paa,
        language=_normalize_optional_text(payload.language),
        country=_normalize_optional_text(payload.country),
        paa_seed_query=_normalize_optional_text(payload.paa_seed_query),
        count=payload.count,
        existing_queries=payload.existing_queries,
    )


def _build_provider(config: SeedQueryGenerationConfig | None) -> SeedQueryJSONProvider:
    resolved_config = config or load_seed_query_generation_config()
    if not resolved_config.enabled:
        raise SeedQueryGenerationUnavailable("Seed query generation is disabled.")
    if resolved_config.provider == "mock":
        return MockSeedQueryJSONProvider()

    try:
        openai_config = load_openai_provider_config()
        if not openai_config.api_key:
            raise OpenAIConfigError("OPENAI_API_KEY is required.")
    except OpenAIConfigError as exc:
        raise SeedQueryGenerationUnavailable("OpenAI is not configured.") from exc

    return OpenAISeedQueryJSONProvider(
        api_key=openai_config.api_key,
        model=resolved_config.model or OpenAIProviderConfig().model_l1,
        timeout_seconds=resolved_config.timeout_seconds,
    )


async def _call_provider(
    provider: SeedQueryJSONProvider | ProviderCallable,
    prompt: str,
) -> str:
    if hasattr(provider, "generate"):
        return await provider.generate(prompt)  # type: ignore[union-attr]
    return await provider(prompt)


def _suggestions_from_provider_output(
    *,
    raw_output: str,
    requested_count: int,
    existing_keys: set[str],
    available_slots: int,
) -> GeneratedSeedQueriesResult:
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError:
        return _unavailable_result()

    if not isinstance(parsed, dict) or not isinstance(parsed.get("queries"), list):
        return _unavailable_result()

    suggestions: list[GeneratedSeedQuerySuggestion] = []
    seen = set(existing_keys)
    skipped_duplicates = 0
    skipped_limit = 0
    warnings: list[str] = []

    for item in parsed["queries"]:
        suggestion = _parse_provider_item(item)
        if suggestion is None:
            continue

        key = _query_key(suggestion.text)
        if key in seen:
            skipped_duplicates += 1
            continue

        if len(suggestions) >= min(requested_count, available_slots):
            skipped_limit += 1
            continue

        seen.add(key)
        suggestions.append(suggestion)

    if skipped_duplicates:
        warnings.append(f"{skipped_duplicates} duplicate query suggestion(s) skipped.")
    if skipped_limit:
        warnings.append(
            f"{skipped_limit} query suggestion(s) skipped because the limit is 20."
        )
    if len(suggestions) < requested_count:
        warnings.append("Fewer seed query suggestions were returned than requested.")

    return GeneratedSeedQueriesResult(
        suggestions=suggestions,
        skipped_duplicates=skipped_duplicates,
        skipped_limit=skipped_limit,
        warnings=warnings,
    )


def _parse_provider_item(item: Any) -> GeneratedSeedQuerySuggestion | None:
    if not isinstance(item, dict):
        return None
    text = item.get("text")
    query_type = item.get("type")
    if not isinstance(text, str) or not isinstance(query_type, str):
        return None

    normalized_text = _normalize_optional_text(text)
    if normalized_text is None or query_type not in _allowed_query_types():
        return None

    return GeneratedSeedQuerySuggestion(text=normalized_text, type=query_type)


async def _generate_paa_suggestions(
    payload: GenerateSeedQueriesInput,
    *,
    paa_provider: PeopleAlsoAskProvider | None,
    seen: set[str],
    available_slots: int,
) -> GeneratedSeedQueriesResult:
    if available_slots <= 0:
        return GeneratedSeedQueriesResult(
            skipped_limit=payload.count,
            warnings=["Seed query limit is already reached."],
        )

    provider = paa_provider or build_paa_provider(load_paa_provider_config())
    paa_query = _paa_query(payload)
    if paa_query is None:
        return GeneratedSeedQueriesResult(
            warnings=["People Also Ask requires a brand name, domain, or seed query."]
        )

    try:
        result = await provider.get_questions(
            paa_query,
            payload.language,
            payload.country,
            min(payload.count, available_slots),
        )
    except Exception:
        logger.warning("People Also Ask provider call failed.", exc_info=True)
        return GeneratedSeedQueriesResult(
            warnings=["People Also Ask enrichment is currently unavailable."]
        )

    suggestions: list[GeneratedSeedQuerySuggestion] = []
    skipped_duplicates = 0
    skipped_limit = 0
    local_seen = set(seen)

    for question in result.questions:
        suggestion = _suggestion_from_paa_question(question)
        if suggestion is None:
            continue

        key = _query_key(suggestion.text)
        if key in local_seen:
            skipped_duplicates += 1
            continue

        if len(suggestions) >= min(payload.count, available_slots):
            skipped_limit += 1
            continue

        local_seen.add(key)
        suggestions.append(suggestion)

    warnings = list(result.warnings)
    if skipped_duplicates:
        warnings.append(f"{skipped_duplicates} duplicate query suggestion(s) skipped.")
    if skipped_limit:
        warnings.append(
            f"{skipped_limit} query suggestion(s) skipped because the limit is 20."
        )
    if len(suggestions) < payload.count:
        warnings.append("Fewer seed query suggestions were returned than requested.")

    return GeneratedSeedQueriesResult(
        suggestions=suggestions,
        skipped_duplicates=skipped_duplicates,
        skipped_limit=skipped_limit,
        warnings=warnings,
    )


def _paa_query(payload: GenerateSeedQueriesInput) -> str | None:
    return (
        _normalize_optional_text(payload.paa_seed_query)
        or _normalize_optional_text(payload.brand_name)
        or _normalize_optional_text(payload.brand_domain)
    )


def _suggestion_from_paa_question(
    question: PeopleAlsoAskQuestion,
) -> GeneratedSeedQuerySuggestion | None:
    text = _normalize_optional_text(question.text)
    if text is None:
        return None
    return GeneratedSeedQuerySuggestion(
        text=text,
        type=_infer_paa_query_type(text),
        source=SeedQuerySource.PAA.value,
        metadata=_public_metadata(question.metadata, provider=question.provider),
    )


def _infer_paa_query_type(text: str) -> str:
    normalized = text.casefold()
    if "alternative" in normalized or " vs " in normalized:
        return SeedQueryType.ALTERNATIVE.value
    if "compare" in normalized or "comparison" in normalized:
        return SeedQueryType.COMPARISON.value
    if (
        "best " in normalized
        or "top " in normalized
        or "recommend" in normalized
        or "vendor" in normalized
        or "provider" in normalized
    ):
        return SeedQueryType.RECOMMENDATION.value
    if "how " in normalized or "solve" in normalized or "problem" in normalized:
        return SeedQueryType.PROBLEM_SOLUTION.value
    if "what is" in normalized or "known for" in normalized:
        return SeedQueryType.BRAND_DIRECT.value
    return SeedQueryType.CATEGORY_DISCOVERY.value


def _public_metadata(
    metadata: Mapping[str, object],
    *,
    provider: str,
) -> dict[str, Any]:
    public: dict[str, Any] = {"paa_provider": provider}
    for key, value in metadata.items():
        if key in {"paa_provider", "language", "country"} and isinstance(
            value, str | int | float | bool
        ):
            public[key] = value
    return public


def _is_valid_existing_query(query: SeedQueryDraft) -> bool:
    return _normalize_optional_text(query.text) is not None


def _query_key(query: str) -> str:
    return " ".join(query.strip().split()).casefold()


def _normalize_domain(value: str) -> str:
    normalized = value.strip().lower().rstrip("/")
    if (
        not normalized
        or "://" in normalized
        or "/" in normalized
        or "?" in normalized
        or "#" in normalized
        or not DOMAIN_PATTERN.fullmatch(normalized)
    ):
        raise ValueError("Invalid domain format")
    return normalized


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None


def _build_prompt(payload: GenerateSeedQueriesInput) -> str:
    selected_sources = []
    if payload.use_description:
        selected_sources.append("brand description")
    if payload.use_domain:
        selected_sources.append("brand domain")

    return (
        "Return JSON only with a top-level queries array. "
        f"Generate exactly {payload.count} seed query suggestions if possible. "
        "Each item must include text and one fixed type. "
        "Allowed types: "
        f"{', '.join(sorted(_allowed_query_types()))}. "
        "Avoid duplicates and cover multiple user intents. "
        "Do not include markdown or explanations. "
        f"Brand name: {payload.brand_name or 'unknown'}. "
        f"Brand domain: {payload.brand_domain or 'not provided'}. "
        f"Brand description: {payload.brand_description or 'not provided'}. "
        f"Selected sources: {', '.join(selected_sources)}. "
        "Use description as the primary semantic signal when selected; use domain only "
        "for disambiguation."
    )


def _allowed_query_types() -> set[str]:
    return {item.value for item in SeedQueryType}


def _unavailable_result() -> GeneratedSeedQueriesResult:
    return GeneratedSeedQueriesResult(
        suggestions=[],
        skipped_duplicates=0,
        skipped_limit=0,
        warnings=[GENERATION_UNAVAILABLE_WARNING],
    )


def _merge_generation_results(
    current: GeneratedSeedQueriesResult,
    incoming: GeneratedSeedQueriesResult,
    *,
    seen: set[str],
) -> GeneratedSeedQueriesResult:
    suggestions = [*current.suggestions, *incoming.suggestions]
    for suggestion in incoming.suggestions:
        seen.add(_query_key(suggestion.text))
    return GeneratedSeedQueriesResult(
        suggestions=suggestions,
        skipped_duplicates=current.skipped_duplicates + incoming.skipped_duplicates,
        skipped_limit=current.skipped_limit + incoming.skipped_limit,
        warnings=[*current.warnings, *incoming.warnings],
    )


def _mock_seed_query_pairs() -> list[tuple[str, str]]:
    return [
        ("What is this brand known for?", "brand_direct"),
        ("Best tools in this category", "category_discovery"),
        ("Top services for this problem", "category_discovery"),
        ("Recommended vendors for this use case", "recommendation"),
        ("Which provider should I choose for this need?", "recommendation"),
        ("Compare this brand with alternatives", "comparison"),
        ("This brand vs leading competitors", "comparison"),
        ("Alternatives to this brand", "alternative"),
        ("How to solve this business problem", "problem_solution"),
        ("Best way to improve this workflow", "problem_solution"),
    ]


def _load_bool(source: Mapping[str, str], key: str, default: bool) -> bool:
    raw_value = source.get(key)
    if raw_value is None:
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise SeedQueryGenerationConfigError(f"{key} must be a boolean value.")


def _load_positive_float(source: Mapping[str, str], key: str, default: float) -> float:
    raw_value = source.get(key)
    if raw_value is None:
        return default
    try:
        value = float(raw_value.strip())
    except ValueError as exc:
        raise SeedQueryGenerationConfigError(f"{key} must be a positive number.") from exc
    if value <= 0:
        raise SeedQueryGenerationConfigError(f"{key} must be a positive number.")
    return value


def _load_optional_text(source: Mapping[str, str], key: str) -> str | None:
    value = source.get(key)
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _get_attr_or_key(value: Any, key: str) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)


def _to_json_safe(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, list | tuple):
        return [_to_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _to_json_safe(item) for key, item in value.items()}
    if hasattr(value, "model_dump"):
        return _to_json_safe(value.model_dump())
    if hasattr(value, "__dict__"):
        return _to_json_safe(vars(value))
    return str(value)
