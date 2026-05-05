from __future__ import annotations

from copy import deepcopy
from typing import Any


def audit_target_fixture(
    *,
    ai_family: str = "chatgpt",
    execution_provider: str = "openrouter",
    model_provider: str = "openai",
    model_id: str = "openai/gpt-4o-mini",
    display_name: str = "GPT-4o mini",
    level: str = "L1",
    gateway: bool = True,
    gateway_l2_experimental: bool = False,
) -> dict[str, Any]:
    return {
        "ai_family": ai_family,
        "execution_provider": execution_provider,
        "model_provider": model_provider,
        "model_id": model_id,
        "display_name": display_name,
        "level": level,
        "gateway": gateway,
        "gateway_l2_experimental": gateway_l2_experimental,
    }


def audit_create_payload_fixture(
    *,
    brand_name: str = "Acme Targets",
    seed_queries: list[str] | None = None,
    providers: list[str] | None = None,
    model_targets: list[dict[str, Any]] | None = None,
    runs_per_query: int = 1,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "brand_name": brand_name,
        "runs_per_query": runs_per_query,
        "seed_queries": seed_queries or ["best ai visibility tools"],
    }
    if model_targets is None:
        payload["providers"] = providers or ["mock"]
    else:
        payload["model_targets"] = deepcopy(model_targets)
    return payload


LEGACY_SINGLE_PROVIDER_L1 = audit_create_payload_fixture(
    brand_name="Legacy L1",
    providers=["mock"],
)

LEGACY_AUDIT_WITHOUT_TARGETS = audit_create_payload_fixture(
    brand_name="Legacy Without Targets",
    providers=["openai"],
)

SINGLE_MODEL_L1 = audit_create_payload_fixture(
    brand_name="Single Model L1",
    model_targets=[audit_target_fixture()],
)

SINGLE_MODEL_L1_L2 = audit_create_payload_fixture(
    brand_name="Single Model L1 L2",
    model_targets=[
        audit_target_fixture(display_name="GPT-4o mini L1", level="L1"),
        audit_target_fixture(
            display_name="GPT-4o mini L2",
            level="L2",
            gateway_l2_experimental=True,
        ),
    ],
)

TWO_MODELS_SAME_LEVEL_L1 = audit_create_payload_fixture(
    brand_name="Two Models L1",
    model_targets=[
        audit_target_fixture(
            ai_family="chatgpt",
            model_provider="openai",
            model_id="openai/gpt-4o-mini",
            display_name="GPT-4o mini",
        ),
        audit_target_fixture(
            ai_family="claude",
            model_provider="anthropic",
            model_id="anthropic/claude-3.5-sonnet",
            display_name="Claude 3.5 Sonnet",
        ),
    ],
)

TWO_FAMILIES_MIXED_LEVELS = audit_create_payload_fixture(
    brand_name="Mixed Families",
    model_targets=[
        audit_target_fixture(
            ai_family="chatgpt",
            model_provider="openai",
            model_id="openai/gpt-4o-mini",
            display_name="GPT-4o mini L1",
            level="L1",
        ),
        audit_target_fixture(
            ai_family="gemini",
            model_provider="google",
            model_id="google/gemini-2.0-flash-001",
            display_name="Gemini 2.0 Flash L2",
            level="L2",
            gateway_l2_experimental=True,
        ),
    ],
)

OPENROUTER_L1_TARGET = audit_target_fixture(
    model_provider="openai",
    model_id="openai/gpt-4o-mini",
    display_name="OpenRouter GPT-4o mini",
    level="L1",
)

OPENROUTER_L2_EXPERIMENTAL_TARGET = audit_target_fixture(
    model_provider="openai",
    model_id="openai/gpt-4o-mini",
    display_name="OpenRouter GPT-4o mini web",
    level="L2",
    gateway_l2_experimental=True,
)

TWO_OPENROUTER_SAME_LEVEL_TARGETS = audit_create_payload_fixture(
    brand_name="OpenRouter Same Level",
    model_targets=[
        OPENROUTER_L1_TARGET,
        audit_target_fixture(
            ai_family="claude",
            model_provider="anthropic",
            model_id="anthropic/claude-3.5-sonnet",
            display_name="OpenRouter Claude 3.5 Sonnet",
            level="L1",
        ),
    ],
)

AUDIT_OVER_CAPS = audit_create_payload_fixture(
    brand_name="Over Caps",
    seed_queries=["query one", "query two", "query three"],
    model_targets=TWO_OPENROUTER_SAME_LEVEL_TARGETS["model_targets"],
    runs_per_query=5,
)


BACKEND_AUDIT_TARGET_FIXTURES = {
    "legacy_single_provider_l1": LEGACY_SINGLE_PROVIDER_L1,
    "single_model_l1": SINGLE_MODEL_L1,
    "single_model_l1_l2": SINGLE_MODEL_L1_L2,
    "two_models_same_level_l1": TWO_MODELS_SAME_LEVEL_L1,
    "two_families_mixed_levels": TWO_FAMILIES_MIXED_LEVELS,
    "openrouter_l1_target": audit_create_payload_fixture(
        brand_name="OpenRouter L1",
        model_targets=[OPENROUTER_L1_TARGET],
    ),
    "openrouter_l2_experimental_target": audit_create_payload_fixture(
        brand_name="OpenRouter L2",
        model_targets=[OPENROUTER_L2_EXPERIMENTAL_TARGET],
    ),
    "two_openrouter_same_level_targets": TWO_OPENROUTER_SAME_LEVEL_TARGETS,
    "audit_over_caps": AUDIT_OVER_CAPS,
    "legacy_audit_without_targets": LEGACY_AUDIT_WITHOUT_TARGETS,
}
