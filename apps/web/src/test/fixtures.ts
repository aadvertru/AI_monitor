import type {
  AuditCreateResponse,
  AuditDetail,
  AuditListItem,
  AuditResultsResponse,
  AuditRunTriggerResponse,
  AuditSummaryResponse,
  AuditStatusResponse,
  LogoutResponse,
  CurrentUser,
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
  enable_query_expansion: false,
  enable_source_intelligence: false,
  follow_up_depth: 0,
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
};

export const auditRunTriggerFixture: AuditRunTriggerResponse = {
  audit_id: 42,
  audit_number: 1,
  status: "running",
  scheduled_jobs: 4,
  total_jobs: 4,
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
  critical_query_count: 1,
  provider_scores: {
    mock: 0.8,
    openai: 0.68,
  },
  critical_queries: criticalQueriesFixture,
  competitors: competitorsSummaryFixture,
  sources: sourcesSummaryFixture,
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
  critical_query_count: 0,
  critical_queries: [],
  provider_scores: {},
  competitors: [],
  sources: [],
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
      sources: [],
      raw_answer_ref: null,
      error_code: "provider_error",
      error_message: "Provider failed.",
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
      sources: [],
      raw_answer_ref: null,
      error_code: "timeout",
      error_message: "Provider timed out.",
    },
  ],
};

export const emptyAuditResultsFixture: AuditResultsResponse = {
  audit_id: 42,
  audit_number: 1,
  total: 0,
  rows: [],
};
