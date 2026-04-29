import type {
  AuditDetail,
  AuditListItem,
  AuditResultsResponse,
  AuditRunTriggerResponse,
  AuditStatusResponse,
  AuditSummaryResponse,
  CurrentUser,
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

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

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

export function listAudits() {
  return apiFetch<AuditListItem[]>("/audits");
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
