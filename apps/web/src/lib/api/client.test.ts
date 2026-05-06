import { describe, expect, it, vi } from "vitest";

import {
  ApiError,
  archiveAudit,
  createAudit,
  deleteArchivedAudit,
  estimateAudit,
  generateSeedQuerySuggestions,
  getAuditAnswerMatrix,
  getAuditDetail,
  getAuditResults,
  getAuditSourceDomains,
  getAuditSummary,
  getAuditSummaryV2,
  getCurrentUser,
  getModelCatalog,
  loginUser,
  listAudits,
  resolveApiBaseUrl,
  restoreAudit,
  runAuditPipeline,
  updateAudit,
} from "./client";
import {
  auditDetailFixture,
  auditDetailWithModelTargetsFixture,
  auditEstimateFixture,
  auditAnswerMatrixFixture,
  auditListFixture,
  auditPipelineRunFixture,
  auditResultsFixture,
  auditSummaryV2Fixture,
  auditSummaryFixture,
  auditTargetFixture,
  auditTargetWireFixture,
  createAuditModelTargetsPayloadFixture,
  createAuditModelTargetsWireFixture,
  currentUserFixture,
  legacyAuditDetailWithoutModelTargetsFixture,
  modelCatalogWireFixture,
  openRouterL2AuditTargetFixture,
  openRouterL2AuditTargetWireFixture,
  sourceDomainsFixture,
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

  it("loads archived audit list responses", async () => {
    const fetchMock = mockFetchSequence([{ body: auditListFixture }]);

    await expect(listAudits({ archived: true })).resolves.toEqual(auditListFixture);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/audits?archived=true",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("loads and maps authenticated model catalog responses", async () => {
    const fetchMock = mockFetchSequence([{ body: modelCatalogWireFixture }]);

    await expect(getModelCatalog()).resolves.toEqual({
      families: [
        {
          id: "chatgpt",
          label: "ChatGPT",
          models: [
            {
              modelId: "openai/gpt-4o-mini",
              displayName: "GPT-4o mini",
              modelProvider: "openai",
              executionProvider: "openrouter",
              aiFamily: "chatgpt",
              supportsL1: true,
              supportsL2Gateway: true,
              l2Experimental: true,
              contextLength: 128000,
            },
          ],
        },
        {
          id: "gemini",
          label: "Gemini",
          models: [
            {
              modelId: "google/gemini-2.0-flash-001",
              displayName: "Gemini 2.0 Flash",
              modelProvider: "google",
              executionProvider: "openrouter",
              aiFamily: "gemini",
              supportsL1: true,
              supportsL2Gateway: true,
              l2Experimental: true,
              contextLength: undefined,
            },
          ],
        },
      ],
      cachedAt: "2026-05-05T00:00:00Z",
      expiresAt: "2026-05-06T00:00:00Z",
      warnings: [],
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/model-catalog",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("handles empty model catalog warnings and missing optional fields", async () => {
    mockFetchSequence([
      {
        body: {
          families: [
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
                },
              ],
            },
          ],
          warnings: ["Showing stale catalog."],
        },
      },
    ]);

    await expect(getModelCatalog()).resolves.toEqual({
      families: [
        {
          id: "claude",
          label: "Claude",
          models: [
            {
              modelId: "anthropic/claude-3.5-sonnet",
              displayName: "Claude 3.5 Sonnet",
              modelProvider: "anthropic",
              executionProvider: "openrouter",
              aiFamily: "claude",
              supportsL1: true,
              supportsL2Gateway: false,
              l2Experimental: false,
              contextLength: undefined,
            },
          ],
        },
      ],
      cachedAt: undefined,
      expiresAt: undefined,
      warnings: ["Showing stale catalog."],
    });

    mockFetchSequence([{ body: {} }]);
    await expect(getModelCatalog()).resolves.toEqual({
      families: [],
      cachedAt: undefined,
      expiresAt: undefined,
      warnings: [],
    });
  });

  it("loads audit detail responses", async () => {
    mockFetchSequence([{ body: legacyAuditDetailWithoutModelTargetsFixture }]);

    await expect(getAuditDetail(42)).resolves.toEqual({
      ...auditDetailFixture,
      modelTargets: [],
    });
  });

  it("maps audit detail model_targets from snake_case wire fixtures", async () => {
    mockFetchSequence([{ body: auditDetailWithModelTargetsFixture }]);

    await expect(getAuditDetail(42)).resolves.toEqual({
      ...auditDetailWithModelTargetsFixture,
      modelTargets: [auditTargetFixture, openRouterL2AuditTargetFixture],
    });
  });

  it("updates audit setup with a credentialed PUT request", async () => {
    const fetchMock = mockFetchSequence([{ body: auditDetailFixture }]);

    await expect(
      updateAudit(42, {
        brand_name: "Acme AI",
        brand_domain: "acme.example",
        providers: ["mock"],
        runs_per_query: 1,
        seed_queries: ["best ai visibility tools"],
        scdl_level: "L1",
      }),
    ).resolves.toEqual({ ...auditDetailFixture, modelTargets: [] });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/audits/42",
      expect.objectContaining({
        credentials: "include",
        method: "PUT",
      }),
    );
  });

  it("maps create payload modelTargets to backend model_targets", async () => {
    const fetchMock = mockFetchSequence([
      {
        body: {
          audit_id: 42,
          audit_number: 1,
          brand_id: 7,
          status: "created",
          providers: ["openrouter"],
          runs_per_query: 1,
          scdl_level: "L1",
          seed_queries: ["best ai visibility tools"],
          seed_query_items: [{ text: "best ai visibility tools", source: "user" }],
          model_targets: [auditTargetWireFixture, openRouterL2AuditTargetWireFixture],
        },
      },
    ]);

    const result = await createAudit(createAuditModelTargetsPayloadFixture);

    const request = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(request.body).toBe(JSON.stringify(createAuditModelTargetsWireFixture));
    expect(String(request.body)).not.toContain("modelTargets");
    expect(result.modelTargets?.[0]?.gatewayL2Experimental).toBe(false);
    expect(result.modelTargets?.[1]?.gatewayL2Experimental).toBe(true);
  });

  it("estimates audit runs with backend wire model_targets", async () => {
    const fetchMock = mockFetchSequence([{ body: auditEstimateFixture }]);

    await expect(
      estimateAudit({
        runs_per_query: createAuditModelTargetsPayloadFixture.runs_per_query,
        seed_query_items: createAuditModelTargetsPayloadFixture.seed_query_items,
        modelTargets: createAuditModelTargetsPayloadFixture.modelTargets,
      }),
    ).resolves.toEqual(auditEstimateFixture);

    const request = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/audits/estimate",
      expect.objectContaining({ credentials: "include", method: "POST" }),
    );
    expect(JSON.parse(String(request.body))).toEqual({
      runs_per_query: createAuditModelTargetsWireFixture.runs_per_query,
      seed_query_items: createAuditModelTargetsWireFixture.seed_query_items,
      model_targets: createAuditModelTargetsWireFixture.model_targets,
    });
    expect(String(request.body)).not.toContain("brand_name");
    expect(String(request.body)).not.toContain("brand_domain");
    expect(String(request.body)).not.toContain("modelTargets");
  });

  it("generates seed query suggestions with the documented endpoint and payload", async () => {
    const rawResponse = {
      suggestions: [
        {
          text: "best acme alternatives",
          type: "alternative",
          source: "ai",
        },
      ],
      skipped_duplicates: 2,
      skipped_limit: 1,
      warnings: ["Duplicate suggestions were skipped."],
    };
    const fetchMock = mockFetchSequence([{ body: rawResponse }]);

    await expect(
      generateSeedQuerySuggestions({
        brandName: "Acme AI",
        brandDomain: "acme.example",
        brandDescription: "AI visibility monitoring platform.",
        useDomain: true,
        useDescription: true,
        count: 10,
        existingQueries: [
          {
            text: "best ai visibility tools",
            type: "category_discovery",
            source: "user",
          },
        ],
      }),
    ).resolves.toEqual({
      suggestions: rawResponse.suggestions,
      skippedDuplicates: 2,
      skippedLimit: 1,
      warnings: rawResponse.warnings,
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/audit-seed-query-suggestions",
      expect.objectContaining({
        credentials: "include",
        method: "POST",
        body: JSON.stringify({
          brand_name: "Acme AI",
          brand_domain: "acme.example",
          brand_description: "AI visibility monitoring platform.",
          use_domain: true,
          use_description: true,
          count: 10,
          existing_queries: [
            {
              text: "best ai visibility tools",
              type: "category_discovery",
              source: "user",
            },
          ],
        }),
      }),
    );
  });

  it("loads audit results responses", async () => {
    mockFetchSequence([{ body: auditResultsFixture }]);

    await expect(getAuditResults(42)).resolves.toEqual(auditResultsFixture);
  });

  it("loads audit summary responses", async () => {
    mockFetchSequence([{ body: auditSummaryFixture }]);

    await expect(getAuditSummary(42)).resolves.toEqual(auditSummaryFixture);
  });

  it("loads audit summary v2 responses with safe empty placeholders", async () => {
    const fetchMock = mockFetchSequence([{ body: auditSummaryV2Fixture }]);

    await expect(getAuditSummaryV2(42)).resolves.toEqual(auditSummaryV2Fixture);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/audits/42/summary-v2",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(auditSummaryV2Fixture.overall.accuracy_l1).toBeNull();
    expect(auditSummaryV2Fixture.concepts).toEqual([]);
    expect(auditSummaryV2Fixture.competitor_candidates).toEqual([]);
  });

  it("loads answer matrix responses with nullable evaluation and provider errors", async () => {
    const fetchMock = mockFetchSequence([{ body: auditAnswerMatrixFixture }]);

    await expect(getAuditAnswerMatrix(42)).resolves.toEqual(auditAnswerMatrixFixture);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/audits/42/answer-matrix",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(auditAnswerMatrixFixture.columns[1]?.gateway_l2_experimental).toBe(true);
    expect(auditAnswerMatrixFixture.rows[0]?.cells[0]?.evaluation).toBeNull();
    expect(auditAnswerMatrixFixture.rows[0]?.cells[1]?.provider_error?.code).toBe("TIMEOUT");
  });

  it("loads source domains strict placeholder responses", async () => {
    const fetchMock = mockFetchSequence([{ body: sourceDomainsFixture }]);

    await expect(getAuditSourceDomains(42)).resolves.toEqual(sourceDomainsFixture);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/audits/42/source-domains",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("normalizes partial results v2 payloads to safe arrays", async () => {
    mockFetchSequence([
      {
        body: {
          audit_id: 42,
          status: "created",
          totals: {
            query_count: 0,
            target_count: 0,
            run_count: 0,
            completed_runs: 0,
            failed_runs: 0,
            levels: [],
          },
          overall: {
            mentionability_l1: { found: 0, total: 0, percentage: null },
            mentionability_l2: { found: 0, total: 0, percentage: null },
            accuracy_l1: null,
            accuracy_l2: null,
            tone: { positive: 0, neutral: 0, negative: 0, unknown: 0 },
          },
        },
      },
      {
        body: {
          audit_id: 42,
          columns: [],
          rows: [{ query_id: "1", query_text: "legacy query" }],
        },
      },
      {
        body: { audit_id: 42 },
      },
    ]);

    await expect(getAuditSummaryV2(42)).resolves.toMatchObject({
      model_summaries: [],
      concepts: [],
      competitor_candidates: [],
      provider_diagnostics: [],
    });
    await expect(getAuditAnswerMatrix(42)).resolves.toMatchObject({
      rows: [{ cells: [] }],
      provider_diagnostics: [],
    });
    await expect(getAuditSourceDomains(42)).resolves.toEqual({
      audit_id: 42,
      domains: [],
      warnings: [],
    });
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

  it("archives, restores, and deletes audits with credentialed requests", async () => {
    const actionResponse = {
      audit_id: 42,
      status: "created",
      archived_at: "2026-05-02T10:00:00Z",
    };
    const fetchMock = mockFetchSequence([
      { body: actionResponse },
      { body: { ...actionResponse, archived_at: null } },
      { body: undefined, status: 204 },
    ]);

    await expect(archiveAudit(42)).resolves.toEqual(actionResponse);
    await expect(restoreAudit(42)).resolves.toEqual({ ...actionResponse, archived_at: null });
    await expect(deleteArchivedAudit(42)).resolves.toBeUndefined();
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/audits/42/archive",
      expect.objectContaining({ credentials: "include", method: "POST" }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/audits/42/restore",
      expect.objectContaining({ credentials: "include", method: "POST" }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/audits/42",
      expect.objectContaining({ credentials: "include", method: "DELETE" }),
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

  it("propagates seed query generation errors safely", async () => {
    mockFetchSequence([{ body: { detail: "Seed query generation is unavailable." }, status: 503 }]);

    await expect(
      generateSeedQuerySuggestions({
        brandName: "Acme AI",
        useDomain: false,
        useDescription: false,
        existingQueries: [],
      }),
    ).rejects.toMatchObject({
      message: "Seed query generation is unavailable.",
      status: 503,
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
