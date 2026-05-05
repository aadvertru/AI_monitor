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
  AuditTarget,
  AuditTargetWire,
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

export function mapAuditTargetToWire(target: AuditTarget): AuditTargetWire {
  return {
    id: target.id,
    target_id: target.targetId,
    ai_family: target.aiFamily,
    execution_provider: target.executionProvider,
    model_provider: target.modelProvider,
    model_id: target.modelId,
    display_name: target.displayName,
    level: target.level,
    gateway: target.gateway,
    gateway_l2_experimental: target.gatewayL2Experimental,
  };
}

export function mapAuditTargetFromWire(target: AuditTargetWire): AuditTarget {
  return {
    id: target.id,
    targetId: target.target_id,
    aiFamily: target.ai_family,
    executionProvider: target.execution_provider,
    modelProvider: target.model_provider,
    modelId: target.model_id,
    displayName: target.display_name,
    level: target.level,
    gateway: target.gateway,
    gatewayL2Experimental: target.gateway_l2_experimental,
  };
}

function mapAuditPayloadToWire(payload: AuditCreateRequest) {
  const { modelTargets, ...wirePayload } = payload;
  if (modelTargets) {
    const { providers, scdl_level, model_targets, ...canonicalPayload } = wirePayload;
    void providers;
    void scdl_level;
    void model_targets;
    return {
      ...canonicalPayload,
      model_targets: modelTargets.map(mapAuditTargetToWire),
    };
  }
  return wirePayload;
}

function mapAuditDetailFromWire(response: AuditDetail): AuditDetail {
  return {
    ...response,
    modelTargets: response.model_targets?.map(mapAuditTargetFromWire) ?? [],
  };
}

function mapAuditCreateResponseFromWire(response: AuditCreateResponse): AuditCreateResponse {
  return {
    ...response,
    modelTargets: response.model_targets?.map(mapAuditTargetFromWire) ?? [],
  };
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

export async function createAudit(payload: AuditCreateRequest) {
  const response = await apiFetch<AuditCreateResponse>("/audits", {
    method: "POST",
    body: jsonBody(mapAuditPayloadToWire(payload)),
  });
  return mapAuditCreateResponseFromWire(response);
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
    body: jsonBody(mapAuditPayloadToWire(payload)),
  }).then(mapAuditDetailFromWire);
}

export function getAuditDetail(auditId: number) {
  return apiFetch<AuditDetail>(`/audits/${auditId}`).then(mapAuditDetailFromWire);
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
