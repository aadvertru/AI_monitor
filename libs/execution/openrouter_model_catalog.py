"""Safe OpenRouter model catalog service with allowlist filtering and cache."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, ConfigDict, Field

from libs.execution.provider_errors import (
    configuration_error,
    no_api_key_error,
    provider_disabled_error,
    provider_request_failed_error,
)

OPENROUTER_MODEL_CATALOG_URL = "https://openrouter.ai/api/v1/models/user"
DEFAULT_OPENROUTER_MODEL_CATALOG_CACHE_TTL_SECONDS = 86_400

AI_FAMILY_LABELS: dict[str, str] = {
    "chatgpt": "ChatGPT",
    "gemini": "Gemini",
    "claude": "Claude",
    "grok": "Grok",
    "perplexity": "Perplexity",
}

PROVIDER_PREFIX_TO_AI_FAMILY: dict[str, str] = {
    "openai": "chatgpt",
    "google": "gemini",
    "anthropic": "claude",
    "x-ai": "grok",
    "perplexity": "perplexity",
}

CATALOG_REFRESH_FAILED_WARNING = (
    "OpenRouter catalog refresh failed; showing cached model catalog."
)


class ModelCatalogModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_id: str
    display_name: str
    model_provider: str
    execution_provider: str = "openrouter"
    ai_family: str
    supports_l1: bool = True
    supports_l2_gateway: bool = True
    l2_experimental: bool = True
    context_length: int | None = None


class ModelCatalogFamily(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    models: list[ModelCatalogModel]


class ModelCatalogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    families: list[ModelCatalogFamily]
    cached_at: datetime | None = None
    expires_at: datetime | None = None
    warnings: list[str] = Field(default_factory=list)
    diagnostic: dict[str, Any] | None = None


@dataclass(frozen=True)
class OpenRouterModelCatalogConfig:
    enabled: bool
    api_key: str | None = field(repr=False)
    allowed_models: tuple[str, ...]
    cache_ttl_seconds: int = DEFAULT_OPENROUTER_MODEL_CATALOG_CACHE_TTL_SECONDS

    def safe_log_dict(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "api_key": "***" if self.api_key else None,
            "allowed_models": list(self.allowed_models),
            "cache_ttl_seconds": self.cache_ttl_seconds,
        }


@dataclass(frozen=True)
class ModelCatalogCacheEntry:
    families: tuple[ModelCatalogFamily, ...]
    cached_at: datetime
    expires_at: datetime

    def to_response(self, *, warnings: list[str] | None = None) -> ModelCatalogResponse:
        return ModelCatalogResponse(
            families=list(self.families),
            cached_at=self.cached_at,
            expires_at=self.expires_at,
            warnings=warnings or [],
        )


class OpenRouterModelCatalogCache:
    def __init__(self) -> None:
        self._entry: ModelCatalogCacheEntry | None = None

    def get(self) -> ModelCatalogCacheEntry | None:
        return self._entry

    def set(self, entry: ModelCatalogCacheEntry) -> None:
        self._entry = entry

    def clear(self) -> None:
        self._entry = None


class OpenRouterModelCatalogClientProtocol(Protocol):
    async def fetch_user_models(self, config: OpenRouterModelCatalogConfig) -> Any:
        """Fetch raw OpenRouter catalog data."""


class OpenRouterModelCatalogClient:
    def __init__(
        self,
        *,
        http_client: Any | None = None,
        endpoint_url: str = OPENROUTER_MODEL_CATALOG_URL,
    ) -> None:
        self._http_client = http_client
        self.endpoint_url = endpoint_url

    async def fetch_user_models(self, config: OpenRouterModelCatalogConfig) -> Any:
        headers = {"Authorization": f"Bearer {config.api_key}"}
        if self._http_client is not None:
            return await self._http_client.get_json(self.endpoint_url, headers=headers)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.endpoint_url, headers=headers)
        response.raise_for_status()
        return response.json()


Clock = Callable[[], datetime]


class OpenRouterModelCatalogService:
    def __init__(
        self,
        *,
        config: OpenRouterModelCatalogConfig | None = None,
        client: OpenRouterModelCatalogClientProtocol | None = None,
        cache: OpenRouterModelCatalogCache | None = None,
        clock: Clock | None = None,
    ) -> None:
        self.config = config or load_openrouter_model_catalog_config()
        self.client = client or OpenRouterModelCatalogClient()
        self.cache = cache or OpenRouterModelCatalogCache()
        self.clock = clock or _utcnow

    async def get_catalog(self) -> ModelCatalogResponse:
        config_error_response = _preflight_response(self.config)
        if config_error_response is not None:
            return config_error_response

        now = self.clock()
        cached = self.cache.get()
        if cached is not None and cached.expires_at > now:
            return cached.to_response()

        try:
            raw_catalog = await self.client.fetch_user_models(self.config)
        except Exception:
            if cached is not None:
                return cached.to_response(warnings=[CATALOG_REFRESH_FAILED_WARNING])
            return ModelCatalogResponse(
                families=[],
                warnings=[],
                diagnostic=provider_request_failed_error("openrouter").to_error_dict(),
            )

        families = normalize_openrouter_catalog(
            raw_catalog,
            allowed_models=set(self.config.allowed_models),
        )
        entry = ModelCatalogCacheEntry(
            families=tuple(families),
            cached_at=now,
            expires_at=now + timedelta(seconds=self.config.cache_ttl_seconds),
        )
        self.cache.set(entry)
        return entry.to_response()


_DEFAULT_CACHE = OpenRouterModelCatalogCache()


async def get_openrouter_model_catalog(
    *,
    config: OpenRouterModelCatalogConfig | None = None,
    client: OpenRouterModelCatalogClientProtocol | None = None,
    cache: OpenRouterModelCatalogCache | None = None,
    clock: Clock | None = None,
) -> ModelCatalogResponse:
    service = OpenRouterModelCatalogService(
        config=config,
        client=client,
        cache=cache or _DEFAULT_CACHE,
        clock=clock,
    )
    return await service.get_catalog()


def load_openrouter_model_catalog_config(
    env: Mapping[str, str] | None = None,
) -> OpenRouterModelCatalogConfig:
    source = os.environ if env is None else env
    return OpenRouterModelCatalogConfig(
        enabled=_load_bool(source, "OPENROUTER_CATALOG_ENABLED", True),
        api_key=_load_optional_text(source, "OPENROUTER_API_KEY"),
        allowed_models=_load_csv_tuple(source, "OPENROUTER_ALLOWED_MODELS"),
        cache_ttl_seconds=_load_positive_int(
            source,
            "OPENROUTER_MODEL_CATALOG_CACHE_TTL_SECONDS",
            DEFAULT_OPENROUTER_MODEL_CATALOG_CACHE_TTL_SECONDS,
        ),
    )


def normalize_openrouter_catalog(
    raw_catalog: Any,
    *,
    allowed_models: set[str],
) -> list[ModelCatalogFamily]:
    grouped: dict[str, list[ModelCatalogModel]] = {
        family_id: [] for family_id in AI_FAMILY_LABELS
    }
    for raw_model in _extract_raw_models(raw_catalog):
        model_id = _extract_text(raw_model, "id")
        if not model_id or model_id not in allowed_models:
            continue
        provider_prefix = _model_provider_prefix(model_id)
        family_id = PROVIDER_PREFIX_TO_AI_FAMILY.get(provider_prefix)
        if family_id is None:
            continue
        grouped[family_id].append(
            ModelCatalogModel(
                model_id=model_id,
                display_name=_display_name(raw_model, model_id),
                model_provider=provider_prefix,
                ai_family=family_id,
                context_length=_context_length(raw_model),
            )
        )

    families: list[ModelCatalogFamily] = []
    for family_id, label in AI_FAMILY_LABELS.items():
        models = sorted(grouped[family_id], key=lambda item: item.display_name.lower())
        if models:
            families.append(ModelCatalogFamily(id=family_id, label=label, models=models))
    return families


def _preflight_response(
    config: OpenRouterModelCatalogConfig,
) -> ModelCatalogResponse | None:
    if not config.enabled:
        return ModelCatalogResponse(
            families=[],
            diagnostic=provider_disabled_error("openrouter").to_error_dict(),
        )
    if not config.api_key:
        return ModelCatalogResponse(
            families=[],
            diagnostic=no_api_key_error("openrouter").to_error_dict(),
        )
    if not config.allowed_models:
        return ModelCatalogResponse(
            families=[],
            diagnostic=configuration_error("openrouter").to_error_dict(),
        )
    return None


def _extract_raw_models(raw_catalog: Any) -> list[Mapping[str, Any]]:
    if isinstance(raw_catalog, Mapping):
        data = raw_catalog.get("data")
        if isinstance(data, list):
            return [item for item in data if isinstance(item, Mapping)]
    if isinstance(raw_catalog, list):
        return [item for item in raw_catalog if isinstance(item, Mapping)]
    return []


def _extract_text(raw_model: Mapping[str, Any], key: str) -> str:
    value = raw_model.get(key)
    if isinstance(value, str):
        return value.strip()
    return ""


def _display_name(raw_model: Mapping[str, Any], model_id: str) -> str:
    return _extract_text(raw_model, "name") or _extract_text(raw_model, "display_name") or model_id


def _model_provider_prefix(model_id: str) -> str:
    if "/" not in model_id:
        return ""
    provider, _model_name = model_id.split("/", 1)
    return provider.strip().lower()


def _context_length(raw_model: Mapping[str, Any]) -> int | None:
    value = raw_model.get("context_length")
    if isinstance(value, int) and value > 0:
        return value
    return None


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _load_optional_text(source: Mapping[str, str], key: str) -> str | None:
    raw_value = source.get(key)
    if raw_value is None:
        return None
    value = raw_value.strip()
    return value or None


def _load_bool(source: Mapping[str, str], key: str, default: bool) -> bool:
    raw_value = source.get(key)
    if raw_value is None:
        return default
    value = raw_value.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return default


def _load_positive_int(source: Mapping[str, str], key: str, default: int) -> int:
    raw_value = source.get(key)
    if raw_value is None:
        return default
    try:
        value = int(raw_value.strip())
    except ValueError:
        return default
    return value if value > 0 else default


def _load_csv_tuple(source: Mapping[str, str], key: str) -> tuple[str, ...]:
    raw_value = source.get(key)
    if raw_value is None:
        return ()
    return tuple(item.strip() for item in raw_value.split(",") if item.strip())
