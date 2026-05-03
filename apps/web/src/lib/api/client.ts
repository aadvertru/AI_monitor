import type {
  AuditCreateRequest,
  AuditCreateResponse,
  AuditActionResponse,
  AuditDetail,
  AuditListItem,
  AuditPipelineRunResponse,
  AuditResultsResponse,
  AuditRunTriggerResponse,
  AuditStatusResponse,
  AuditSummaryResponse,
  CurrentUser,
  GenerateSeedQuerySuggestionsRequest,
  GenerateSeedQuerySuggestionsResponse,
  GeneratedSeedQuerySuggestion,
  LoginRequest,
  LogoutResponse,
  RegisterRequest,
} from "./types";

export type ApiErrorPayload = {
  detail?: unknown;
  message?: string;
};

export class ApiError extends Error {
  readonly payload: ApiErrorPayload | null;
  readonly status: number;

  constructor(status: number, message: string, payload: ApiErrorPayload | null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export function resolveApiBaseUrl(
  configuredUrl = import.meta.env.VITE_API_BASE_URL,
  locationLike: Pick<Location, "protocol" | "hostname"> | undefined = globalThis.location,
) {
  const normalizedConfiguredUrl = configuredUrl?.trim().replace(/\/$/, "");
  if (normalizedConfiguredUrl) {
    return normalizedConfiguredUrl;
  }

  const protocol = locationLike?.protocol || "http:";
  const hostname = locationLike?.hostname || "localhost";
  return `${protocol}//${hostname}:8000`;
}

export const API_BASE_URL = resolveApiBaseUrl();

async function parseError(response: Response): Promise<ApiError> {
  let payload: ApiErrorPayload | null = null;
  try {
    payload = (await response.json()) as ApiErrorPayload;
  } catch {
    payload = null;
  }

  const detail = payload?.detail;
  const message =
    typeof detail === "string"
      ? detail
      : payload?.message || response.statusText || "Request failed.";

  return new ApiError(response.status, message, payload);
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers,
  });

  if (!response.ok) {
    throw await parseError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

function jsonBody(value: unknown) {
  return JSON.stringify(value);
}

type RawGenerateSeedQuerySuggestionsResponse = {
  suggestions: GeneratedSeedQuerySuggestion[];
  skipped_duplicates?: number;
  skipped_limit?: number;
  warnings?: string[];
};

function mapSeedQueryGenerationResponse(
  response: RawGenerateSeedQuerySuggestionsResponse,
): GenerateSeedQuerySuggestionsResponse {
  return {
    suggestions: response.suggestions,
    skippedDuplicates: response.skipped_duplicates,
    skippedLimit: response.skipped_limit,
    warnings: response.warnings,
  };
}

export function getCurrentUser() {
  return apiFetch<CurrentUser>("/auth/me");
}

export function loginUser(payload: LoginRequest) {
  return apiFetch<CurrentUser>("/auth/login", {
    method: "POST",
    body: jsonBody(payload),
  });
}

export function registerUser(payload: RegisterRequest) {
  return apiFetch<CurrentUser>("/auth/register", {
    method: "POST",
    body: jsonBody(payload),
  });
}

export function logoutUser() {
  return apiFetch<LogoutResponse>("/auth/logout", { method: "POST" });
}

export function listAudits({ archived = false }: { archived?: boolean } = {}) {
  const params = archived ? "?archived=true" : "";
  return apiFetch<AuditListItem[]>(`/audits${params}`);
}

export function createAudit(payload: AuditCreateRequest) {
  return apiFetch<AuditCreateResponse>("/audits", {
    method: "POST",
    body: jsonBody(payload),
  });
}

export async function generateSeedQuerySuggestions(
  payload: GenerateSeedQuerySuggestionsRequest,
) {
  const response = await apiFetch<RawGenerateSeedQuerySuggestionsResponse>(
    "/audit-seed-query-suggestions",
    {
      method: "POST",
      body: jsonBody({
        brand_name: payload.brandName,
        brand_domain: payload.brandDomain,
        brand_description: payload.brandDescription,
        use_domain: payload.useDomain,
        use_description: payload.useDescription,
        count: payload.count,
        existing_queries: payload.existingQueries,
      }),
    },
  );

  return mapSeedQueryGenerationResponse(response);
}

export function updateAudit(auditId: number, payload: AuditCreateRequest) {
  return apiFetch<AuditDetail>(`/audits/${auditId}`, {
    method: "PUT",
    body: jsonBody(payload),
  });
}

export function getAuditDetail(auditId: number) {
  return apiFetch<AuditDetail>(`/audits/${auditId}`);
}

export function getAuditStatus(auditId: number) {
  return apiFetch<AuditStatusResponse>(`/audits/${auditId}/status`);
}

export function getAuditResults(auditId: number) {
  return apiFetch<AuditResultsResponse>(`/audits/${auditId}/results`);
}

export function getAuditSummary(auditId: number) {
  return apiFetch<AuditSummaryResponse>(`/audits/${auditId}/summary`);
}

export function runAudit(auditId: number) {
  return apiFetch<AuditRunTriggerResponse>(`/audits/${auditId}/run`, {
    method: "POST",
  });
}

export function runAuditPipeline(auditId: number) {
  return apiFetch<AuditPipelineRunResponse>(`/audits/${auditId}/run-pipeline`, {
    method: "POST",
  });
}

export function archiveAudit(auditId: number) {
  return apiFetch<AuditActionResponse>(`/audits/${auditId}/archive`, {
    method: "POST",
  });
}

export function restoreAudit(auditId: number) {
  return apiFetch<AuditActionResponse>(`/audits/${auditId}/restore`, {
    method: "POST",
  });
}

export function deleteArchivedAudit(auditId: number) {
  return apiFetch<void>(`/audits/${auditId}`, {
    method: "DELETE",
  });
}
