export type UserRole = "user" | "admin";
export type AuditStatus = "created" | "running" | "partial" | "completed" | "failed";
export type RunStatus = "pending" | "success" | "error" | "timeout" | "rate_limited";
export type SCDLLevel = "L1" | "L2";
export type ProviderDiagnosticCode =
  | "PROVIDER_DISABLED"
  | "NO_API_KEY"
  | "INVALID_API_KEY"
  | "INVALID_MODEL"
  | "UNSUPPORTED_L2"
  | "TIMEOUT"
  | "RATE_LIMIT"
  | "EMPTY_RESPONSE"
  | "INVALID_RESPONSE"
  | "PROVIDER_UNAVAILABLE"
  | "PROVIDER_REQUEST_FAILED"
  | "CONFIGURATION_ERROR"
  | "UNKNOWN_PROVIDER_ERROR";
export type SeedQueryType =
  | "brand_direct"
  | "category_discovery"
  | "recommendation"
  | "comparison"
  | "alternative"
  | "problem_solution";
export type SeedQuerySource = "user" | "ai";

export type AuditTarget = {
  id?: string | number;
  targetId?: string | number;
  aiFamily: string;
  executionProvider: string;
  modelProvider: string;
  modelId: string;
  displayName: string;
  level: SCDLLevel;
  gateway?: boolean;
  gatewayL2Experimental?: boolean;
};

export type AuditTargetWire = {
  id?: string | number;
  target_id?: string | number;
  ai_family: string;
  execution_provider: string;
  model_provider: string;
  model_id: string;
  display_name: string;
  level: SCDLLevel;
  gateway?: boolean;
  gateway_l2_experimental?: boolean;
};

export type ModelCatalogModelWire = {
  model_id: string;
  display_name: string;
  model_provider: string;
  execution_provider: "openrouter" | string;
  ai_family: string;
  supports_l1?: boolean;
  supports_l2_gateway?: boolean;
  l2_experimental?: boolean;
  context_length?: number | null;
};

export type ModelCatalogFamilyWire = {
  id: string;
  label: string;
  models: ModelCatalogModelWire[];
};

export type ModelCatalogResponseWire = {
  families?: ModelCatalogFamilyWire[];
  cached_at?: string | null;
  expires_at?: string | null;
  warnings?: string[];
};

export type ModelCatalogModel = {
  modelId: string;
  displayName: string;
  modelProvider: string;
  executionProvider: "openrouter" | string;
  aiFamily: string;
  supportsL1: boolean;
  supportsL2Gateway: boolean;
  l2Experimental: boolean;
  contextLength?: number | null;
};

export type ModelCatalogFamily = {
  id: string;
  label: string;
  models: ModelCatalogModel[];
};

export type ModelCatalogResponse = {
  families: ModelCatalogFamily[];
  cachedAt?: string | null;
  expiresAt?: string | null;
  warnings: string[];
};

export type CurrentUser = {
  id: number;
  email: string;
  role: UserRole;
};

export type LoginRequest = {
  email: string;
  password: string;
};

export type RegisterRequest = LoginRequest;

export type LogoutResponse = {
  status: string;
};

export type AuditListItem = {
  audit_id: number;
  audit_number: number;
  brand_name: string;
  brand_domain: string | null;
  status: AuditStatus;
  scdl_level: SCDLLevel;
  providers: string[];
  runs_per_query: number;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
};

export type AuditCreateRequest = {
  brand_name: string;
  providers?: string[];
  modelTargets?: AuditTarget[] | null;
  model_targets?: AuditTargetWire[] | null;
  runs_per_query: number;
  brand_domain?: string | null;
  brand_description?: string | null;
  language?: string | null;
  country?: string | null;
  locale?: string | null;
  max_queries?: number | null;
  seed_queries?: string[] | null;
  seed_query_items?: SeedQueryDraft[] | null;
  enable_query_expansion?: boolean;
  enable_source_intelligence?: boolean;
  follow_up_depth?: number;
  scdl_level?: SCDLLevel;
};

export type AuditEstimateRequest = {
  providers?: string[];
  modelTargets?: AuditTarget[] | null;
  model_targets?: AuditTargetWire[] | null;
  runs_per_query?: number;
  seed_queries?: string[] | null;
  seed_query_items?: SeedQueryDraft[] | null;
  scdl_level?: SCDLLevel;
};

export type AuditCaps = {
  max_audit_targets: number;
  max_models_per_audit: number;
  max_queries_per_audit: number;
  max_total_runs_per_audit: number;
};

export type AuditCapViolation = {
  code: string;
  message: string;
};

export type AuditEstimateResponse = {
  query_count: number;
  target_count: number;
  model_count: number;
  estimated_runs: number;
  caps: AuditCaps;
  over_cap: boolean;
  violations: AuditCapViolation[];
  warnings: string[];
};

export type SeedQueryDraft = {
  text: string;
  type?: SeedQueryType | null;
  source?: SeedQuerySource;
};

export type AuditCreateResponse = {
  audit_id: number;
  audit_number: number;
  brand_id: number;
  status: AuditStatus;
  providers: string[];
  runs_per_query: number;
  scdl_level: SCDLLevel;
  seed_queries: string[];
  seed_query_items: SeedQueryDraft[];
  model_targets?: AuditTargetWire[];
  modelTargets?: AuditTarget[];
};

export type AuditDetail = AuditListItem & {
  brand_id: number;
  brand_description: string | null;
  language: string | null;
  country: string | null;
  locale: string | null;
  max_queries: number | null;
  seed_queries: string[];
  seed_query_items: SeedQueryDraft[];
  model_targets?: AuditTargetWire[];
  modelTargets?: AuditTarget[];
  enable_query_expansion: boolean;
  enable_source_intelligence: boolean;
  follow_up_depth: number;
};

export type GenerateSeedQuerySuggestionsRequest = {
  brandName?: string | null;
  brandDomain?: string | null;
  brandDescription?: string | null;
  useDomain: boolean;
  useDescription: boolean;
  count?: number;
  existingQueries: SeedQueryDraft[];
};

export type GeneratedSeedQuerySuggestion = {
  text: string;
  type: SeedQueryType;
  source: "ai";
};

export type GenerateSeedQuerySuggestionsResponse = {
  suggestions: GeneratedSeedQuerySuggestion[];
  skippedDuplicates?: number;
  skippedLimit?: number;
  warnings?: string[];
};

export type AuditActionResponse = {
  audit_id: number;
  status: AuditStatus;
  archived_at: string | null;
};

export type AuditStatusResponse = {
  audit_id: number;
  audit_number: number;
  status: AuditStatus;
  scdl_level: SCDLLevel;
  total_runs: number;
  completed_runs: number;
  failed_runs: number;
  completion_ratio: number;
  updated_at: string | null;
  model_targets?: AuditTargetWire[];
  modelTargets?: AuditTarget[];
  provider_diagnostics?: ProviderDiagnostic[];
};

export type AuditRunTriggerResponse = {
  audit_id: number;
  audit_number: number;
  status: AuditStatus;
  scheduled_jobs: number;
  total_jobs: number;
};

export type AuditPipelineSchedulingResponse = {
  audit_id: number;
  scheduled_jobs: number;
  total_jobs: number;
  fatal_error: string | null;
};

export type AuditPipelineExecutionError = {
  job_id: number;
  code: string;
  message: string;
};

export type AuditPipelineExecutionResponse = {
  audit_id: number;
  total_jobs_inspected: number;
  jobs_executed: number;
  jobs_skipped: number;
  success_count: number;
  error_count: number;
  timeout_count: number;
  rate_limited_count: number;
  errors: AuditPipelineExecutionError[];
  fatal_error: string | null;
};

export type AuditPipelinePostProcessingError = {
  run_id: number;
  code: string;
  message: string;
};

export type AuditPipelinePostProcessingResponse = {
  audit_id: number;
  total_runs_inspected: number;
  runs_processed: number;
  skipped_already_processed: number;
  skipped_missing_raw_response: number;
  skipped_non_successful_run: number;
  audit_status: AuditStatus | null;
  errors: AuditPipelinePostProcessingError[];
  fatal_error: string | null;
};

export type AuditPipelineRunResponse = {
  audit_id: number;
  scheduling: AuditPipelineSchedulingResponse;
  execution: AuditPipelineExecutionResponse | null;
  post_processing: AuditPipelinePostProcessingResponse | null;
  final_audit_status: AuditStatus | null;
  fatal_error: string | null;
  provider_diagnostics?: ProviderDiagnostic[];
};

export type ProviderDiagnostic = {
  code: ProviderDiagnosticCode;
  message: string;
  provider: string;
  model?: string | null;
  level?: SCDLLevel | null;
  retryable?: boolean;
  run_id?: number | string | null;
  query_id?: number | string | null;
};

export type ComponentScores = {
  visibility_score: number | null;
  prominence_score: number | null;
  sentiment_score: number | null;
  recommendation_score: number | null;
  source_quality_score: number | null;
};

export type SourceSummaryItem = {
  title: string | null;
  url: string | null;
  domain: string | null;
  provider: string | null;
  source_type: string | null;
  citation_count: number | null;
  related_query_count: number | null;
  source_quality_score: number | null;
};

export type AuditResultRow = {
  audit_id: number;
  scdl_level: SCDLLevel;
  target_id?: number | null;
  target?: AuditTargetWire | null;
  targetModel?: AuditTarget | null;
  query_id: number;
  query: string;
  provider: string;
  run_id: number;
  run_number: number;
  run_status: RunStatus;
  visible_brand: boolean | null;
  brand_position_rank: number | null;
  final_score: number | null;
  component_scores: ComponentScores | null;
  competitors: string[];
  sources: SourceSummaryItem[];
  raw_answer_ref: number | null;
  error_code: string | null;
  error_message: string | null;
  provider_error?: ProviderDiagnostic | null;
};

export type AuditResultsResponse = {
  audit_id: number;
  audit_number: number;
  rows: AuditResultRow[];
  total: number;
  provider_diagnostics?: ProviderDiagnostic[];
};

export type CompetitorSummaryItem = {
  name: string;
  mention_count: number | null;
  visibility_ratio: number | null;
  average_score: number | null;
};

export type CriticalQueryItem = {
  query: string;
  reason: string;
  query_score: number | null;
};

export type QueryTypeCoverageItem = {
  type: SeedQueryType | "unknown";
  total_queries: number;
  processed_runs: number;
  failed_runs: number;
  brand_found_count: number;
  brand_found_rate: number;
  average_score: number | null;
};

export type AuditSummaryResponse = {
  audit_id: number;
  audit_number: number;
  status: AuditStatus;
  total_queries: number;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  completion_ratio: number;
  visibility_ratio: number;
  average_score: number | null;
  weighted_visibility_score: number | null;
  critical_query_count: number;
  provider_scores: Record<string, number | null>;
  critical_queries: CriticalQueryItem[];
  query_type_coverage: QueryTypeCoverageItem[];
  competitors: CompetitorSummaryItem[];
  sources: SourceSummaryItem[];
  provider_diagnostics?: ProviderDiagnostic[];
};
