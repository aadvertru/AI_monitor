export type UserRole = "user" | "admin";
export type AuditStatus = "created" | "running" | "partial" | "completed" | "failed";
export type RunStatus = "pending" | "success" | "error" | "timeout" | "rate_limited";
export type SCDLLevel = "L1" | "L2";

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
};

export type AuditCreateRequest = {
  brand_name: string;
  providers: string[];
  runs_per_query: number;
  brand_domain?: string | null;
  brand_description?: string | null;
  language?: string | null;
  country?: string | null;
  locale?: string | null;
  max_queries?: number | null;
  seed_queries?: string[] | null;
  enable_query_expansion?: boolean;
  enable_source_intelligence?: boolean;
  follow_up_depth?: number;
  scdl_level?: SCDLLevel;
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
};

export type AuditDetail = AuditListItem & {
  brand_id: number;
  brand_description: string | null;
  language: string | null;
  country: string | null;
  locale: string | null;
  max_queries: number | null;
  seed_queries: string[];
  enable_query_expansion: boolean;
  enable_source_intelligence: boolean;
  follow_up_depth: number;
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
};

export type AuditRunTriggerResponse = {
  audit_id: number;
  audit_number: number;
  status: AuditStatus;
  scheduled_jobs: number;
  total_jobs: number;
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
};

export type AuditResultsResponse = {
  audit_id: number;
  audit_number: number;
  rows: AuditResultRow[];
  total: number;
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
  critical_query_count: number;
  provider_scores: Record<string, number | null>;
  critical_queries: CriticalQueryItem[];
  competitors: CompetitorSummaryItem[];
  sources: SourceSummaryItem[];
};
