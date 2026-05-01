import { describe, expect, it, vi } from "vitest";

import {
  ApiError,
  getAuditDetail,
  getAuditResults,
  getAuditSummary,
  getCurrentUser,
  loginUser,
  listAudits,
  resolveApiBaseUrl,
  runAuditPipeline,
} from "./client";
import {
  auditDetailFixture,
  auditListFixture,
  auditPipelineRunFixture,
  auditResultsFixture,
  auditSummaryFixture,
  currentUserFixture,
  unauthenticatedAuthErrorFixture,
} from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";

describe("api client", () => {
  it("defaults API origin to the current browser hostname", () => {
    expect(resolveApiBaseUrl(undefined, { protocol: "http:", hostname: "127.0.0.1" })).toBe(
      "http://127.0.0.1:8000",
    );
    expect(resolveApiBaseUrl(undefined, { protocol: "http:", hostname: "localhost" })).toBe(
      "http://localhost:8000",
    );
  });

  it("uses configured API base URL when provided", () => {
    expect(resolveApiBaseUrl("http://api.local:9000/", undefined)).toBe(
      "http://api.local:9000",
    );
  });

  it("loads the current user with credentialed requests", async () => {
    const fetchMock = mockFetchSequence([{ body: currentUserFixture }]);

    await expect(getCurrentUser()).resolves.toEqual(currentUserFixture);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/auth/me",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("parses API errors into a predictable shape", async () => {
    mockFetchSequence([{ body: unauthenticatedAuthErrorFixture, status: 401 }]);
    const expectedMessage =
      typeof unauthenticatedAuthErrorFixture.detail === "string"
        ? unauthenticatedAuthErrorFixture.detail
        : "Request failed.";

    await expect(loginUser({ email: "user@example.com", password: "bad" })).rejects.toMatchObject({
      message: expectedMessage,
      status: 401,
    } satisfies Partial<ApiError>);
  });

  it("loads audit list responses", async () => {
    mockFetchSequence([{ body: auditListFixture }]);

    await expect(listAudits()).resolves.toEqual(auditListFixture);
  });

  it("loads audit detail responses", async () => {
    mockFetchSequence([{ body: auditDetailFixture }]);

    await expect(getAuditDetail(42)).resolves.toEqual(auditDetailFixture);
  });

  it("loads audit results responses", async () => {
    mockFetchSequence([{ body: auditResultsFixture }]);

    await expect(getAuditResults(42)).resolves.toEqual(auditResultsFixture);
  });

  it("loads audit summary responses", async () => {
    mockFetchSequence([{ body: auditSummaryFixture }]);

    await expect(getAuditSummary(42)).resolves.toEqual(auditSummaryFixture);
  });

  it("starts the owner audit pipeline with a credentialed request", async () => {
    const fetchMock = mockFetchSequence([{ body: auditPipelineRunFixture }]);

    await expect(runAuditPipeline(42)).resolves.toEqual(auditPipelineRunFixture);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/audits/42/run-pipeline",
      expect.objectContaining({
        credentials: "include",
        method: "POST",
      }),
    );
    expect(fetchMock).not.toHaveBeenCalledWith(
      expect.stringContaining("/dev/"),
      expect.anything(),
    );
  });

  it.each([
    [401, "Not authenticated."],
    [403, "Real provider execution is disabled."],
    [404, "Audit was not found."],
    [409, "Audit is already running."],
    [500, "Failed to run audit pipeline."],
  ])("normalizes pipeline start error %s", async (status, detail) => {
    mockFetchSequence([{ body: { detail }, status }]);

    await expect(runAuditPipeline(42)).rejects.toMatchObject({
      message: detail,
      status,
    } satisfies Partial<ApiError>);
  });

  it("does not expect raw answers or secrets in pipeline response data", () => {
    const dumped = JSON.stringify(auditPipelineRunFixture);

    expect(dumped).not.toContain("raw_answer");
    expect(dumped).not.toContain("request_snapshot");
    expect(dumped).not.toContain("api_key");
    expect(dumped).not.toContain("authorization");
    expect(dumped).not.toContain("cookie");
    expect(dumped).not.toContain("token");
  });

  it("does not use browser token storage during credentialed API calls", async () => {
    const storageSpy = vi.spyOn(Storage.prototype, "setItem");
    mockFetchSequence([{ body: currentUserFixture }, { body: auditPipelineRunFixture }]);

    await expect(getCurrentUser()).resolves.toEqual(currentUserFixture);
    await expect(runAuditPipeline(42)).resolves.toEqual(auditPipelineRunFixture);

    expect(storageSpy).not.toHaveBeenCalled();

    storageSpy.mockRestore();
  });
});
