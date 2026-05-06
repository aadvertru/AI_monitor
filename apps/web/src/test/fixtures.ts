import type {
  AuditCreateResponse,
  AuditDetail,
  AuditListItem,
  AuditPipelineRunResponse,
  AuditResultsResponse,
  AuditRunTriggerResponse,
  AuditSummaryResponse,
  AuditStatusResponse,
  AuditTarget,
  AuditTargetWire,
  LogoutResponse,
  CurrentUser,
  ProviderDiagnostic,
  AuditCreateRequest,
  ModelCatalogResponseWire,
  AuditEstimateResponse,
  ProfileResponse,
  AnswerMatrixResponse,
  AuditSummaryV2Response,
  SourceDomainsResponse,
} from "../lib/api/types";
import type { ApiErrorPayload } from "../lib/api/client";

export const currentUserFixture: CurrentUser = {
  id: 1,
  email: "user@example.com",
  role: "user",
};

export const unauthenticatedAuthErrorFixture: ApiErrorPayload = {
  detail: "Not authenticated.",
};

export const logoutResponseFixture: LogoutResponse = {
  status: "logged_out",
};

export const profileFixture: ProfileResponse = {
  user: {
    id: 1,
    email: "user@example.com",
    display_name: null,
  },
  plan: {
    name: "Starter",
    status: "demo",
    is_demo: true,
  },
  usage: {
    tokens_remaining: 7500,
    tokens_total: 10000,
    reset_at: null,
    is_demo: true,
  },
  preferences: {
    locale: "en",
    email_notifications: true,
    audit_completed_notifications: true,
    provider_error_notifications: false,
  },
};

export const auditListFixture: AuditListItem[] = [
  {
    audit_id: 42,
    audit_number: 1,
    brand_name: "Acme AI",
    brand_domain: "acme.example",
    status: "created",
    scdl_level: "L1",
    providers: ["mock"],
    runs_per_query: 1,
    created_at: "2026-04-29T09:30:00Z",
    updated_at: "2026-04-29T09:30:00Z",
    archived_at: null,
  },
];

export const auditCreateResponseFixture: AuditCreateResponse = {
  audit_id: 42,
  audit_number: 1,
  brand_id: 7,
  status: "created",
  providers: ["mock"],
  runs_per_query: 1,
  scdl_level: "L1",
  seed_queries: ["best ai visibility tools"],
  seed_query_items: [
    {
      text: "best ai visibility tools",
      type: null,
      source: "user",
    },
  ],
};

export const auditTargetWireFixture: AuditTargetWire = {
  target_id: 10,
  ai_family: "chatgpt",
  execution_provider: "openrouter",
  model_provider: "openai",
  model_id: "openai/gpt-4o-mini",
  display_name: "GPT-4o mini",
  level: "L1",
  gateway: true,
  gateway_l2_experimental: false,
};

export const openRouterL2AuditTargetWireFixture: AuditTargetWire = {
  target_id: 11,
  ai_family: "chatgpt",
  execution_provider: "openrouter",
  model_provider: "openai",
  model_id: "openai/gpt-4o-mini",
  display_name: "GPT-4o mini with web",
  level: "L2",
  gateway: true,
  gateway_l2_experimental: true,
};

export const auditTargetFixture: AuditTarget = {
  targetId: auditTargetWireFixture.target_id,
  aiFamily: auditTargetWireFixture.ai_family,
  executionProvider: auditTargetWireFixture.execution_provider,
  modelProvider: auditTargetWireFixture.model_provider,
  modelId: auditTargetWireFixture.model_id,
  displayName: auditTargetWireFixture.display_name,
  level: auditTargetWireFixture.level,
  gateway: auditTargetWireFixture.gateway,
  gatewayL2Experimental: auditTargetWireFixture.gateway_l2_experimental,
};

export const openRouterL2AuditTargetFixture: AuditTarget = {
  targetId: openRouterL2AuditTargetWireFixture.target_id,
  aiFamily: openRouterL2AuditTargetWireFixture.ai_family,
  executionProvider: openRouterL2AuditTargetWireFixture.execution_provider,
  modelProvider: openRouterL2AuditTargetWireFixture.model_provider,
  modelId: openRouterL2AuditTargetWireFixture.model_id,
  displayName: openRouterL2AuditTargetWireFixture.display_name,
  level: openRouterL2AuditTargetWireFixture.level,
  gateway: openRouterL2AuditTargetWireFixture.gateway,
  gatewayL2Experimental: openRouterL2AuditTargetWireFixture.gateway_l2_experimental,
};

export const auditDetailFixture: AuditDetail = {
  ...auditListFixture[0],
  brand_id: 7,
  brand_description: "AI visibility monitoring platform.",
  language: "en",
  country: "US",
  locale: "en-US",
  max_queries: 20,
  seed_queries: ["best ai visibility tools"],
  seed_query_items: [
    {
      text: "best ai visibility tools",
      type: null,
      source: "user",
    },
  ],
  enable_query_expansion: false,
  enable_source_intelligence: false,
  follow_up_depth: 0,
};

export const auditDetailWithModelTargetsFixture: AuditDetail = {
  ...auditDetailFixture,
  providers: ["openrouter"],
  scdl_level: "L2",
  model_targets: [auditTargetWireFixture, openRouterL2AuditTargetWireFixture],
};

export const legacyAuditDetailWithoutModelTargetsFixture: AuditDetail = {
  ...auditDetailFixture,
};

export const createAuditModelTargetsPayloadFixture: AuditCreateRequest = {
  brand_name: "Acme AI",
  brand_domain: "acme.example",
  runs_per_query: 1,
  seed_query_items: [
    {
      text: "best ai visibility tools",
      type: "category_discovery",
      source: "user",
    },
  ],
  modelTargets: [auditTargetFixture, openRouterL2AuditTargetFixture],
};

export const createAuditModelTargetsWireFixture = {
  brand_name: "Acme AI",
  brand_domain: "acme.example",
  runs_per_query: 1,
  seed_query_items: [
    {
      text: "best ai visibility tools",
      type: "category_discovery",
      source: "user",
    },
  ],
  model_targets: [auditTargetWireFixture, openRouterL2AuditTargetWireFixture],
};

export const auditEstimateFixture: AuditEstimateResponse = {
  query_count: 2,
  target_count: 2,
  model_count: 1,
  estimated_runs: 4,
  caps: {
    max_audit_targets: 10,
    max_models_per_audit: 5,
    max_queries_per_audit: 20,
    max_total_runs_per_audit: 100,
  },
  over_cap: false,
  violations: [],
  warnings: [],
};

export const modelCatalogWireFixture: ModelCatalogResponseWire = {
  families: [
    {
      id: "chatgpt",
      label: "ChatGPT",
      models: [
        {
          model_id: "openai/gpt-4o-mini",
          display_name: "GPT-4o mini",
          model_provider: "openai",
          execution_provider: "openrouter",
          ai_family: "chatgpt",
          supports_l1: true,
          supports_l2_gateway: true,
          l2_experimental: true,
          context_length: 128000,
        },
      ],
    },
    {
      id: "gemini",
      label: "Gemini",
      models: [
        {
          model_id: "google/gemini-2.0-flash-001",
          display_name: "Gemini 2.0 Flash",
          model_provider: "google",
          execution_provider: "openrouter",
          ai_family: "gemini",
          supports_l1: true,
          supports_l2_gateway: true,
          l2_experimental: true,
        },
      ],
    },
  ],
  cached_at: "2026-05-05T00:00:00Z",
  expires_at: "2026-05-06T00:00:00Z",
  warnings: [],
};

export const emptyModelCatalogWireFixture: ModelCatalogResponseWire = {
  families: [],
  cached_at: "2026-05-05T00:00:00Z",
  expires_at: "2026-05-06T00:00:00Z",
  warnings: [],
};

export const warningModelCatalogWireFixture: ModelCatalogResponseWire = {
  ...modelCatalogWireFixture,
  warnings: ["OpenRouter catalog refresh failed."],
};

export const extendedModelCatalogWireFixture: ModelCatalogResponseWire = {
  families: [
    {
      id: "chatgpt",
      label: "ChatGPT",
      models: [
        {
          model_id: "openai/gpt-4o-mini",
          display_name: "GPT-4o mini",
          model_provider: "openai",
          execution_provider: "openrouter",
          ai_family: "chatgpt",
          supports_l1: true,
          supports_l2_gateway: true,
          l2_experimental: true,
          context_length: 128000,
        },
        {
          model_id: "openai/gpt-4.1-nano",
          display_name: "GPT-4.1 nano",
          model_provider: "openai",
          execution_provider: "openrouter",
          ai_family: "chatgpt",
          supports_l1: true,
          supports_l2_gateway: false,
          l2_experimental: false,
          context_length: 100000,
        },
      ],
    },
    {
      id: "gemini",
      label: "Gemini",
      models: [
        {
          model_id: "google/gemini-2.0-flash-001",
          display_name: "Gemini 2.0 Flash",
          model_provider: "google",
          execution_provider: "openrouter",
          ai_family: "gemini",
          supports_l1: true,
          supports_l2_gateway: true,
          l2_experimental: true,
        },
      ],
    },
    {
      id: "claude",
      label: "Claude",
      models: [
        {
          model_id: "anthropic/claude-3.5-sonnet",
          display_name: "Claude 3.5 Sonnet",
          model_provider: "anthropic",
          execution_provider: "openrouter",
          ai_family: "claude",
          supports_l1: true,
          supports_l2_gateway: true,
          l2_experimental: true,
        },
      ],
    },
  ],
  cached_at: "2026-05-05T00:00:00Z",
  expires_at: "2026-05-06T00:00:00Z",
  warnings: ["OpenRouter catalog refresh failed."],
};

export const auditStatusFixture: AuditStatusResponse = {
  audit_id: 42,
  audit_number: 1,
  status: "created",
  scdl_level: "L1",
  total_runs: 4,
  completed_runs: 1,
  failed_runs: 0,
  completion_ratio: 0.25,
  updated_at: "2026-04-29T09:35:00Z",
  provider_diagnostics: [],
};

export const auditRunTriggerFixture: AuditRunTriggerResponse = {
  audit_id: 42,
  audit_number: 1,
  status: "running",
  scheduled_jobs: 4,
  total_jobs: 4,
};

export const auditPipelineRunFixture: AuditPipelineRunResponse = {
  audit_id: 42,
  scheduling: {
    audit_id: 42,
    scheduled_jobs: 4,
    total_jobs: 4,
    fatal_error: null,
  },
  execution: {
    audit_id: 42,
    total_jobs_inspected: 4,
    jobs_executed: 4,
    jobs_skipped: 0,
    success_count: 4,
    error_count: 0,
    timeout_count: 0,
    rate_limited_count: 0,
    errors: [],
    fatal_error: null,
  },
  post_processing: {
    audit_id: 42,
    total_runs_inspected: 4,
    runs_processed: 4,
    skipped_already_processed: 0,
    skipped_missing_raw_response: 0,
    skipped_non_successful_run: 0,
    audit_status: "completed",
    errors: [],
    fatal_error: null,
  },
  final_audit_status: "completed",
  fatal_error: null,
  provider_diagnostics: [],
};

export const rerunEvaluationFixture = {
  audit_id: 42,
  evaluated_runs: 2,
  skipped_runs: 1,
  status: "completed",
  warnings: ["No brand facts were available for answer evaluation."],
};

export const providerDiagnosticFixture: ProviderDiagnostic = {
  code: "TIMEOUT",
  message: "OpenAI request timed out.",
  provider: "openai",
  model: "gpt-test",
  level: "L2",
  retryable: true,
  run_id: 1003,
  query_id: 103,
};

export const criticalQueriesFixture: AuditSummaryResponse["critical_queries"] = [
  {
    query: "best ai visibility tools",
    reason: "Brand not visible",
    query_score: 0.2,
  },
];

export const competitorsSummaryFixture: AuditSummaryResponse["competitors"] = [
  {
    name: "Contoso Monitor",
    mention_count: 4,
    visibility_ratio: 0.5,
    average_score: 0.66,
  },
];

export const sourcesSummaryFixture: AuditSummaryResponse["sources"] = [
  {
    title: "AI visibility benchmarks",
    url: "https://example.com/benchmarks",
    domain: "example.com",
    provider: "openai",
    source_type: "article",
    citation_count: 3,
    related_query_count: 2,
    source_quality_score: 0.7,
  },
];

export const auditSummaryFixture: AuditSummaryResponse = {
  audit_id: 42,
  audit_number: 1,
  status: "completed",
  total_queries: 3,
  total_runs: 6,
  successful_runs: 5,
  failed_runs: 1,
  completion_ratio: 1,
  visibility_ratio: 0.67,
  average_score: 0.74,
  weighted_visibility_score: 0.76,
  critical_query_count: 1,
  provider_scores: {
    mock: 0.8,
    openai: 0.68,
  },
  critical_queries: criticalQueriesFixture,
  query_type_coverage: [
    {
      type: "category_discovery",
      total_queries: 2,
      processed_runs: 4,
      failed_runs: 1,
      brand_found_count: 3,
      brand_found_rate: 0.75,
      average_score: 0.74,
    },
  ],
  competitors: competitorsSummaryFixture,
  sources: sourcesSummaryFixture,
  provider_diagnostics: [],
};

export const auditSummaryV2Fixture: AuditSummaryV2Response = {
  audit_id: 42,
  status: "partial",
  totals: {
    query_count: 2,
    target_count: 2,
    run_count: 3,
    completed_runs: 2,
    failed_runs: 1,
    partial_runs: 0,
    levels: ["L1", "L2"],
  },
  overall: {
    mentionability_l1: {
      found: 1,
      total: 1,
      percentage: 100,
    },
    mentionability_l2: {
      found: 0,
      total: 1,
      percentage: 0,
    },
    accuracy_l1: null,
    accuracy_l2: null,
    verdict_counts: {
      correct: 0,
      partial: 0,
      incorrect: 0,
      unknown: 0,
      not_applicable: 0,
    },
    tone: {
      positive: 1,
      neutral: 0,
      negative: 1,
      unknown: 0,
    },
  },
  model_summaries: [
    {
      target_group_label: "GPT-4o mini",
      ai_family: "chatgpt",
      execution_provider: "openrouter",
      model_provider: "openai",
      model_id: "openai/gpt-4o-mini",
      mr_l1: 100,
      mr_l2: 0,
      delta_mr: -100,
      accuracy_l1: null,
      accuracy_l2: null,
      delta_accuracy: null,
      verdict_counts: {
        correct: 0,
        partial: 0,
        incorrect: 0,
        unknown: 0,
        not_applicable: 0,
      },
      tone_l1: "positive",
      tone_l2: "negative",
      concepts: [],
      competitor_candidates: [],
    },
  ],
  concepts: [],
  competitor_candidates: [],
  provider_diagnostics: [providerDiagnosticFixture],
};

export const completedAuditSummaryV2Fixture: AuditSummaryV2Response = {
  ...auditSummaryV2Fixture,
  status: "completed",
  totals: {
    ...auditSummaryV2Fixture.totals,
    completed_runs: 4,
    failed_runs: 0,
    partial_runs: 0,
    run_count: 4,
  },
  overall: {
    ...auditSummaryV2Fixture.overall,
    accuracy_l1: 0.75,
    accuracy_l2: 0.5,
    verdict_counts: {
      correct: 2,
      partial: 1,
      incorrect: 1,
      unknown: 0,
      not_applicable: 0,
    },
  },
  model_summaries: [
    {
      ...auditSummaryV2Fixture.model_summaries[0]!,
      accuracy_l1: 0.75,
      accuracy_l2: 0.5,
      delta_accuracy: -0.25,
    },
  ],
  provider_diagnostics: [],
};

export const failedAuditSummaryV2Fixture: AuditSummaryV2Response = {
  ...auditSummaryV2Fixture,
  status: "failed",
  totals: {
    ...auditSummaryV2Fixture.totals,
    completed_runs: 0,
    failed_runs: 2,
    partial_runs: 0,
    run_count: 2,
  },
  overall: {
    ...auditSummaryV2Fixture.overall,
    mentionability_l1: { found: 0, total: 0, percentage: null },
    mentionability_l2: { found: 0, total: 0, percentage: null },
  },
  model_summaries: [],
  provider_diagnostics: [providerDiagnosticFixture],
};

export const l1OnlyAuditSummaryV2Fixture: AuditSummaryV2Response = {
  ...completedAuditSummaryV2Fixture,
  totals: {
    ...completedAuditSummaryV2Fixture.totals,
    target_count: 1,
    levels: ["L1"],
  },
  overall: {
    ...completedAuditSummaryV2Fixture.overall,
    mentionability_l2: { found: 0, total: 0, percentage: null },
    accuracy_l2: null,
  },
  model_summaries: [
    {
      ...completedAuditSummaryV2Fixture.model_summaries[0]!,
      mr_l2: null,
      delta_mr: null,
      accuracy_l2: null,
      delta_accuracy: null,
      tone_l2: null,
    },
  ],
};

export const auditAnswerMatrixFixture: AnswerMatrixResponse = {
  audit_id: 42,
  columns: [
    {
      target_id: "10",
      label: "GPT-4o mini / L1",
      ai_family: "chatgpt",
      execution_provider: "openrouter",
      model_provider: "openai",
      model_id: "openai/gpt-4o-mini",
      level: "L1",
      gateway: true,
      gateway_l2_experimental: false,
    },
    {
      target_id: "11",
      label: "GPT-4o mini with web / L2",
      ai_family: "chatgpt",
      execution_provider: "openrouter",
      model_provider: "openai",
      model_id: "openai/gpt-4o-mini",
      level: "L2",
      gateway: true,
      gateway_l2_experimental: true,
    },
  ],
  rows: [
    {
      query_id: "101",
      query_text: "best ai visibility tools",
      query_type: "category_discovery",
      cells: [
        {
          target_id: "10",
          run_id: 1001,
          status: "completed",
          answer_excerpt: "Acme AI is visible in this answer.",
          brand_mentioned: true,
          score: 0.82,
          evaluation: {
            verdict: "partial",
            rationale: "Answer includes useful information but misses exact details.",
            confidence: 0.72,
            evaluation_version: "eval-v1",
            evaluated_at: "2026-05-06T00:00:00Z",
          },
          sources_count: 1,
          provider_error: null,
          concepts: [],
          competitor_candidates: [],
        },
        {
          target_id: "11",
          run_id: 1002,
          status: "failed",
          answer_excerpt: null,
          brand_mentioned: null,
          score: null,
          evaluation: null,
          sources_count: 0,
          provider_error: providerDiagnosticFixture,
          concepts: [],
          competitor_candidates: [],
        },
      ],
    },
  ],
  provider_diagnostics: [providerDiagnosticFixture],
};

export const sourceDomainsFixture: SourceDomainsResponse = {
  audit_id: 42,
  domains: [
    {
      domain: "example.com",
      source_count: 3,
      unique_url_count: 2,
      query_count: 2,
      target_count: 1,
      levels: ["L2"],
      models: ["openai/gpt-4o-mini"],
      providers: ["openrouter"],
      urls: [
        {
          url: "https://docs.example.com/path?utm_source=test",
          normalized_url: "https://docs.example.com/path",
          title: "Example docs",
          snippet: "Evidence snippet for the cited source.",
          query_id: "101",
          query_text: "best ai visibility tools",
          target_id: "11",
          model_id: "openai/gpt-4o-mini",
          model_provider: "openai",
          execution_provider: "openrouter",
          level: "L2",
          source_type: "web",
          gateway: true,
          gateway_l2_experimental: true,
        },
        {
          url: "https://blog.example.com/article",
          normalized_url: "https://blog.example.com/article",
          title: "Example blog",
          snippet: null,
          query_id: "102",
          query_text: "brand monitoring platforms",
          target_id: "11",
          model_id: "openai/gpt-4o-mini",
          model_provider: "openai",
          execution_provider: "openrouter",
          level: "L2",
          source_type: "web",
          gateway: true,
          gateway_l2_experimental: true,
        },
      ],
    },
  ],
  warnings: ["Skipped 1 invalid source URL(s)."],
};

export const emptyAuditSummaryFixture: AuditSummaryResponse = {
  ...auditSummaryFixture,
  status: "created",
  total_queries: 0,
  total_runs: 0,
  successful_runs: 0,
  failed_runs: 0,
  completion_ratio: 0,
  visibility_ratio: 0,
  average_score: null,
  weighted_visibility_score: null,
  critical_query_count: 0,
  critical_queries: [],
  query_type_coverage: [],
  provider_scores: {},
  competitors: [],
  sources: [],
  provider_diagnostics: [],
};

export const partialAuditSummaryFixture: AuditSummaryResponse = {
  ...auditSummaryFixture,
  status: "partial",
  completion_ratio: 0.5,
  successful_runs: 3,
  failed_runs: 3,
};

export const failedAuditSummaryFixture: AuditSummaryResponse = {
  ...emptyAuditSummaryFixture,
  status: "failed",
  total_queries: 3,
  total_runs: 6,
  failed_runs: 6,
};

export const auditResultsFixture: AuditResultsResponse = {
  audit_id: 42,
  audit_number: 1,
  total: 3,
  rows: [
    {
      audit_id: 42,
      scdl_level: "L1",
      query_id: 101,
      query: "best ai visibility tools",
      provider: "mock",
      run_id: 1001,
      run_number: 1,
      run_status: "success",
      visible_brand: true,
      brand_position_rank: 2,
      final_score: 0.82,
      component_scores: {
        visibility_score: 1,
        prominence_score: 0.7,
        sentiment_score: 0.8,
        recommendation_score: 0.6,
        source_quality_score: 0.75,
      },
      competitors: ["Contoso Monitor"],
      concepts: [
        {
          text: "AI visibility benchmarks",
          type: "concept",
          category: "legacy_phrase",
          count: 2,
          evidence_count: 2,
        },
      ],
      competitor_candidates: [
        {
          name: "Contoso Monitor",
          domain: "contoso.example",
          confidence: 0.82,
          evidence_type: "comparison",
          evidence_count: 1,
        },
      ],
      sources: [
        {
          title: "AI visibility benchmarks",
          url: "https://example.com/benchmarks",
          domain: "example.com",
          provider: "mock",
          source_type: "article",
          citation_count: 2,
          related_query_count: 1,
          source_quality_score: 0.75,
        },
      ],
      raw_answer_ref: 501,
      error_code: null,
      error_message: null,
      provider_error: null,
    },
    {
      audit_id: 42,
      scdl_level: "L2",
      query_id: 102,
      query: "brand monitoring platforms with a very long query that should stay contained inside the table layout",
      provider: "openai",
      run_id: 1002,
      run_number: 1,
      run_status: "error",
      visible_brand: false,
      brand_position_rank: null,
      final_score: null,
      component_scores: null,
      competitors: [],
      concepts: [],
      competitor_candidates: [],
      sources: [],
      raw_answer_ref: null,
      error_code: "PROVIDER_REQUEST_FAILED",
      error_message: "Provider failed.",
      provider_error: {
        code: "PROVIDER_REQUEST_FAILED",
        message: "OpenAI request failed.",
        provider: "openai",
        model: "gpt-test",
        level: "L2",
        retryable: true,
        run_id: 1002,
        query_id: 102,
      },
    },
    {
      audit_id: 42,
      scdl_level: "L2",
      query_id: 103,
      query: "ai answer with timeout",
      provider: "anthropic",
      run_id: 1003,
      run_number: 2,
      run_status: "timeout",
      visible_brand: null,
      brand_position_rank: null,
      final_score: null,
      component_scores: null,
      competitors: [],
      concepts: [],
      competitor_candidates: [],
      sources: [],
      raw_answer_ref: null,
      error_code: "TIMEOUT",
      error_message: "Provider timed out.",
      provider_error: providerDiagnosticFixture,
    },
  ],
  provider_diagnostics: [providerDiagnosticFixture],
};

export const emptyAuditResultsFixture: AuditResultsResponse = {
  audit_id: 42,
  audit_number: 1,
  total: 0,
  rows: [],
  provider_diagnostics: [],
};
