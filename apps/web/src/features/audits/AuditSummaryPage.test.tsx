import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  auditDetailFixture,
  auditDetailWithModelTargetsFixture,
  auditAnswerMatrixFixture,
  auditCreateResponseFixture,
  auditSummaryV2Fixture,
  auditSummaryFixture,
  currentUserFixture,
  emptyAuditSummaryFixture,
  partialAuditSummaryFixture,
  providerDiagnosticFixture,
  rerunEvaluationFixture,
} from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";
import { renderRoute } from "../../test/render";

const originalCreateObjectURL = URL.createObjectURL;
const originalRevokeObjectURL = URL.revokeObjectURL;

function renderSummary(summary = auditSummaryFixture, detail = auditDetailFixture) {
  mockFetchSequence([
    { body: currentUserFixture },
    { body: detail },
    { body: summary },
    { body: auditSummaryV2Fixture },
    { body: auditAnswerMatrixFixture },
  ]);
  renderRoute("/audits/42");
}

function jsonResponse(body: unknown, status = 200): Partial<Response> {
  return {
    json: async () => body,
    ok: status >= 200 && status < 300,
    status,
    statusText: status >= 200 && status < 300 ? "OK" : "Error",
  };
}

function exportBlobResponse(filename: string): Partial<Response> {
  return {
    blob: async () => new Blob(["safe export"]),
    headers: new Headers({ "Content-Disposition": `attachment; filename="${filename}"` }),
    ok: true,
    status: 200,
    statusText: "OK",
  };
}

function mockSummaryExportResponse(exportResponse: Partial<Response>) {
  const fetchMock = vi.fn();
  for (const body of [
    currentUserFixture,
    auditDetailFixture,
    auditSummaryFixture,
    auditSummaryV2Fixture,
    auditAnswerMatrixFixture,
  ]) {
    fetchMock.mockResolvedValueOnce(jsonResponse(body));
  }
  fetchMock.mockResolvedValueOnce(exportResponse);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function installDownloadMocks() {
  const createObjectURL = vi.fn(() => "blob:audit-export");
  const revokeObjectURL = vi.fn();
  Object.defineProperty(URL, "createObjectURL", { configurable: true, value: createObjectURL });
  Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: revokeObjectURL });
  const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
  return { click, createObjectURL, revokeObjectURL };
}

const emptyAuditSummaryV2Fixture = {
  ...auditSummaryV2Fixture,
  status: "created",
  totals: {
    query_count: 0,
    target_count: 0,
    run_count: 0,
    completed_runs: 0,
    failed_runs: 0,
    partial_runs: 0,
    levels: [],
  },
  model_summaries: [],
  provider_diagnostics: [],
};

describe("audit summary page", () => {
  afterEach(() => {
    if (originalCreateObjectURL) {
      Object.defineProperty(URL, "createObjectURL", {
        configurable: true,
        value: originalCreateObjectURL,
      });
    } else {
      Reflect.deleteProperty(URL, "createObjectURL");
    }

    if (originalRevokeObjectURL) {
      Object.defineProperty(URL, "revokeObjectURL", {
        configurable: true,
        value: originalRevokeObjectURL,
      });
    } else {
      Reflect.deleteProperty(URL, "revokeObjectURL");
    }

    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("shows loading state while summary is being fetched", async () => {
    const fetchMock = vi.fn();
    fetchMock.mockResolvedValueOnce({
      json: async () => currentUserFixture,
      ok: true,
      status: 200,
      statusText: "OK",
    } satisfies Partial<Response>);
    fetchMock.mockReturnValue(new Promise(() => undefined));
    vi.stubGlobal("fetch", fetchMock);

    renderRoute("/audits/42");

    expect(await screen.findByRole("status")).toHaveTextContent("Loading audit...");
  });

  it("renders summary cards on the canonical audit detail route", async () => {
    renderSummary();

    expect(await screen.findByRole("heading", { name: "Acme AI" })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Web5 summary" })).toBeInTheDocument();
    expect(screen.getAllByText("Data source:").length).toBeGreaterThan(0);
    expect(screen.getByText("summary-v2")).toBeInTheDocument();
    expect(screen.getByText("2 queries · 2 model targets · 3 runs")).toBeInTheDocument();
    expect(screen.getByText("Mentionability L1")).toBeInTheDocument();
    expect(screen.getByText("Mentionability L2")).toBeInTheDocument();
    expect(screen.getAllByText("Accuracy L1").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Accuracy L2").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Tone").length).toBeGreaterThan(0);
    expect(screen.getByText("1/1 found")).toBeInTheDocument();
    expect(screen.getByText("Positive 1 · Neutral 0 · Negative 1 · Unknown 0")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Some audit runs need attention. Completed metrics are shown from backend data that is already available.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("No answer evaluations are available yet, so accuracy is shown as N/A."),
    ).toBeInTheDocument();
    expect(screen.getByText("Model summary")).toBeInTheDocument();
    expect(screen.getByText("GPT-4o mini")).toBeInTheDocument();
    expect(screen.getAllByText("openai/gpt-4o-mini").length).toBeGreaterThan(0);
    expect(screen.getByText("MR L1")).toBeInTheDocument();
    expect(screen.getByText("MR L2")).toBeInTheDocument();
    expect(screen.getAllByText("-100%").length).toBeGreaterThan(0);
    expect(screen.getByText("positive / negative")).toBeInTheDocument();
    expect(screen.getByText("Actions")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Export DOCX" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Export Excel" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Repeat audit" })).toBeEnabled();
    expect(screen.getByRole("link", { name: "Summary" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Summary" })).toHaveAttribute("href", "/audits/42");
    expect(screen.getByRole("link", { name: "Results" })).toHaveAttribute("href", "/audits/42/results");
    expect(screen.getByRole("link", { name: "Sources" })).toHaveAttribute("href", "/audits/42/sources");
    expect(screen.getAllByText("Completed").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Queries").length).toBeGreaterThan(0);
    expect(screen.getAllByText("3").length).toBeGreaterThan(0);
    expect(screen.getByText("Runs")).toBeInTheDocument();
    expect(screen.getByText("6")).toBeInTheDocument();
    expect(screen.getAllByText("100%").length).toBeGreaterThan(0);
    expect(screen.getByText("67%")).toBeInTheDocument();
    expect(screen.getAllByText("0.74").length).toBeGreaterThan(0);
    expect(screen.getByText("Weighted")).toBeInTheDocument();
    expect(screen.getByText("0.76")).toBeInTheDocument();
  });

  it.each([
    ["Export Excel", "excel", "audit-42-summary-20260506T120000Z.xlsx"],
    ["Export DOCX", "docx", "audit-42-report-20260506T120000Z.docx"],
  ])("downloads the %s report through the export endpoint", async (buttonName, kind, filename) => {
    const user = userEvent.setup();
    const fetchMock = mockSummaryExportResponse(exportBlobResponse(filename));
    const download = installDownloadMocks();

    renderRoute("/audits/42");

    await user.click(await screen.findByRole("button", { name: buttonName }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        `http://localhost:8000/audits/42/exports/${kind}`,
        expect.objectContaining({ credentials: "include" }),
      );
    });
    expect(download.createObjectURL).toHaveBeenCalledWith(expect.any(Blob));
    expect(download.click).toHaveBeenCalledTimes(1);
    expect(download.revokeObjectURL).toHaveBeenCalledWith("blob:audit-export");
  });

  it("shows a safe export error without leaking backend details", async () => {
    const user = userEvent.setup();
    mockSummaryExportResponse(jsonResponse({ detail: "raw_prompt sk-hidden" }, 500));

    renderRoute("/audits/42");

    await user.click(await screen.findByRole("button", { name: "Export DOCX" }));

    expect(await screen.findByText("Unable to export this audit right now.")).toBeInTheDocument();
    expect(screen.queryByText(/raw_prompt|sk-hidden/i)).not.toBeInTheDocument();
  });

  it("duplicates an audit and navigates to the new audit without starting it", async () => {
    const user = userEvent.setup();
    const repeatedDetail = {
      ...auditDetailFixture,
      audit_id: 99,
      audit_number: 2,
      brand_name: "Repeated Acme",
    };
    const fetchMock = vi.fn();
    for (const body of [
      currentUserFixture,
      auditDetailFixture,
      auditSummaryFixture,
      auditSummaryV2Fixture,
      auditAnswerMatrixFixture,
      { ...auditCreateResponseFixture, audit_id: 99, audit_number: 2 },
      repeatedDetail,
      { ...auditSummaryFixture, audit_id: 99, audit_number: 2 },
      { ...auditSummaryV2Fixture, audit_id: 99 },
      { ...auditAnswerMatrixFixture, audit_id: 99 },
    ]) {
      fetchMock.mockResolvedValueOnce(jsonResponse(body));
    }
    vi.stubGlobal("fetch", fetchMock);

    renderRoute("/audits/42");

    await user.click(await screen.findByRole("button", { name: "Repeat audit" }));

    expect(await screen.findByRole("heading", { name: "Repeated Acme" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/audits/42/duplicate",
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/audits/99",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(fetchMock).not.toHaveBeenCalledWith(
      "http://localhost:8000/audits/99/run-pipeline",
      expect.anything(),
    );
  });

  it("disables the repeat action while the duplicate request is pending", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn();
    for (const body of [
      currentUserFixture,
      auditDetailFixture,
      auditSummaryFixture,
      auditSummaryV2Fixture,
      auditAnswerMatrixFixture,
    ]) {
      fetchMock.mockResolvedValueOnce(jsonResponse(body));
    }
    fetchMock.mockReturnValueOnce(new Promise(() => undefined));
    vi.stubGlobal("fetch", fetchMock);

    renderRoute("/audits/42");

    await user.click(await screen.findByRole("button", { name: "Repeat audit" }));

    expect(await screen.findByRole("button", { name: "Repeating..." })).toBeDisabled();
  });

  it("shows a safe repeat error without leaking backend details", async () => {
    const user = userEvent.setup();
    mockSummaryExportResponse(jsonResponse({ detail: "raw_prompt sk-hidden" }, 500));

    renderRoute("/audits/42");

    await user.click(await screen.findByRole("button", { name: "Repeat audit" }));

    expect(await screen.findByText("Unable to repeat this audit right now.")).toBeInTheDocument();
    expect(screen.queryByText(/raw_prompt|sk-hidden/i)).not.toBeInTheDocument();
  });

  it("calls the summary-v2 endpoint for the Web5 shell", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailFixture },
      { body: auditSummaryFixture },
      { body: auditSummaryV2Fixture },
      { body: auditAnswerMatrixFixture },
    ]);

    renderRoute("/audits/42");

    expect(await screen.findByRole("heading", { name: "Web5 summary" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/audits/42/summary-v2",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("renders header metadata and a collapsible tested scope", async () => {
    const user = userEvent.setup();
    renderSummary(auditSummaryFixture, auditDetailWithModelTargetsFixture);

    expect(await screen.findByRole("heading", { name: "Web5 summary" })).toBeInTheDocument();
    expect(screen.getByText(/Audit #1 · updated/i)).toBeInTheDocument();
    expect(screen.getByText(/completed 2 · failed 1 · partial 0/i)).toBeInTheDocument();

    const disclosure = screen.getByText("What was tested").closest("details");
    expect(disclosure).not.toHaveAttribute("open");

    await user.click(screen.getByText("What was tested"));

    expect(disclosure).toHaveAttribute("open");
    expect(screen.getByText("Levels")).toBeInTheDocument();
    expect(screen.getByText("L1 / L2")).toBeInTheDocument();
    expect(screen.getByText("Model families")).toBeInTheDocument();
    expect(screen.getAllByText("chatgpt").length).toBeGreaterThan(0);
    expect(screen.getAllByText("OpenRouter").length).toBeGreaterThan(0);
    expect(screen.getAllByText("L2 experimental").length).toBeGreaterThan(0);
  });

  it("reruns fact-checking and refreshes the Web5 summary", async () => {
    const user = userEvent.setup();
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailFixture },
      { body: auditSummaryFixture },
      { body: auditSummaryV2Fixture },
      { body: auditAnswerMatrixFixture },
      { body: rerunEvaluationFixture },
      { body: { ...auditSummaryV2Fixture, overall: { ...auditSummaryV2Fixture.overall, accuracy_l1: 1 } } },
    ]);

    renderRoute("/audits/42");

    await user.click(await screen.findByRole("button", { name: "Rerun fact-checking" }));

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/audits/42/rerun-evaluation",
      expect.objectContaining({ method: "POST" }),
    );
    expect(
      await screen.findByText("Fact-checking rerun complete: 2 evaluated, 1 skipped."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("No brand facts were available for answer evaluation."),
    ).toBeInTheDocument();
  });

  it("shows a Web5 loading state while summary-v2 is being fetched", async () => {
    const fetchMock = vi.fn();
    for (const body of [currentUserFixture, auditDetailFixture, auditSummaryFixture]) {
      fetchMock.mockResolvedValueOnce({
        json: async () => body,
        ok: true,
        status: 200,
        statusText: "OK",
      } satisfies Partial<Response>);
    }
    fetchMock.mockReturnValueOnce(new Promise(() => undefined));
    vi.stubGlobal("fetch", fetchMock);

    renderRoute("/audits/42");

    expect(await screen.findByText("Loading Web5 summary...")).toBeInTheDocument();
  });

  it("shows a safe Web5 error state without leaking backend details", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailFixture },
      { body: auditSummaryFixture },
      { body: { detail: "raw prompt sk-hidden" }, status: 500 },
    ]);

    renderRoute("/audits/42");

    expect(await screen.findByText("Web5 summary unavailable")).toBeInTheDocument();
    expect(screen.getByText("Unable to load the Web5 summary right now.")).toBeInTheDocument();
    expect(screen.queryByText(/raw prompt|sk-hidden/i)).not.toBeInTheDocument();
  });

  it("renders an empty Web5 summary state safely", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailFixture },
      { body: emptyAuditSummaryFixture },
      { body: emptyAuditSummaryV2Fixture },
      { body: auditAnswerMatrixFixture },
    ]);

    renderRoute("/audits/42");

    expect(await screen.findByText("No Web5 summary data is available yet.")).toBeInTheDocument();
    expect(screen.getByText("No model summaries are available yet.")).toBeInTheDocument();
  });

  it("renders an empty or newly created audit summary safely", async () => {
    renderSummary(emptyAuditSummaryFixture);

    expect((await screen.findAllByText("Created")).length).toBeGreaterThan(0);
    expect(screen.getByText("No run data is available yet.")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Query-type diagnostics will appear after the audit has processed typed seed queries.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("No provider scores yet.")).toBeInTheDocument();
    expect(screen.getByText("No critical queries detected.")).toBeInTheDocument();
    expect(screen.getByText("No competitors detected.")).toBeInTheDocument();
    expect(screen.getByText("No source citations yet.")).toBeInTheDocument();
    expect(screen.getAllByText("N/A").length).toBeGreaterThan(0);
  });

  it("renders partial or failed audit summary states safely", async () => {
    renderSummary({
      ...partialAuditSummaryFixture,
      query_type_coverage: [
        {
          type: "recommendation",
          total_queries: 2,
          processed_runs: 1,
          failed_runs: 1,
          brand_found_count: 0,
          brand_found_rate: 0,
          average_score: 0.24,
        },
      ],
    });

    expect(await screen.findByText("Partial")).toBeInTheDocument();
    expect(screen.getAllByText("50%").length).toBeGreaterThan(0);
    expect(screen.getByText("Recommendation")).toBeInTheDocument();
    expect(screen.getByText("0.24")).toBeInTheDocument();
  });

  it("renders provider diagnostics without unsafe fields", async () => {
    renderSummary({
      ...partialAuditSummaryFixture,
      provider_diagnostics: [
        {
          ...providerDiagnosticFixture,
          details: { traceback: "hidden-stack" },
        } as never,
      ],
    });

    expect(await screen.findByText("Provider issue")).toBeInTheDocument();
    expect(screen.getByText("OpenAI request timed out.")).toBeInTheDocument();
    expect(screen.getByText(/openai - L2 - gpt-test - retryable/)).toBeInTheDocument();
    expect(screen.queryByText(/traceback|hidden-stack|sk-/i)).not.toBeInTheDocument();
  });

  it("handles missing optional summary fields", async () => {
    renderSummary({
      ...auditSummaryFixture,
      average_score: null,
      weighted_visibility_score: null,
      provider_scores: { mock: null },
      competitors: [
        {
          name: "Unknown competitor",
          mention_count: null,
          visibility_ratio: null,
          average_score: null,
        },
      ],
      sources: [
        {
          title: null,
          url: null,
          domain: null,
          provider: null,
          source_type: null,
          citation_count: null,
          related_query_count: null,
          source_quality_score: null,
        },
      ],
    });

    expect((await screen.findAllByText("N/A")).length).toBeGreaterThan(0);
    expect(screen.getByText("Unknown competitor")).toBeInTheDocument();
    expect(screen.getByText("Untitled source")).toBeInTheDocument();
    expect(screen.getAllByText("N/A").length).toBeGreaterThan(1);
  });

  it("renders provider summary and chart when provider data exists", async () => {
    renderSummary();

    expect(await screen.findByText("Provider summary")).toBeInTheDocument();
    expect(screen.getByTestId("provider-score-chart")).toBeInTheDocument();
    expect(screen.getAllByText("mock").length).toBeGreaterThan(0);
    expect(screen.getAllByText("openai").length).toBeGreaterThan(0);
  });

  it("renders query-type diagnostics when backend metrics are present", async () => {
    renderSummary();

    expect(await screen.findByText("Query-type diagnostics")).toBeInTheDocument();
    expect(screen.getByText("Category discovery")).toBeInTheDocument();
    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getAllByText("0.74").length).toBeGreaterThan(0);
  });

  it("handles legacy unknown query types without crashing", async () => {
    renderSummary({
      ...auditSummaryFixture,
      query_type_coverage: [
        {
          type: "unknown",
          total_queries: 1,
          processed_runs: 1,
          failed_runs: 0,
          brand_found_count: 1,
          brand_found_rate: 1,
          average_score: 0.5,
        },
      ],
    });

    expect(await screen.findByText("Unknown")).toBeInTheDocument();
    expect(screen.getAllByText("100%").length).toBeGreaterThan(0);
  });

  it("renders critical queries with backend-provided reasons", async () => {
    renderSummary();

    expect(await screen.findByText("Critical queries")).toBeInTheDocument();
    expect(screen.getAllByText("best ai visibility tools").length).toBeGreaterThan(0);
    expect(screen.getByText("Brand not visible")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "View related rows" })).toHaveAttribute(
      "href",
      "/audits/42/results",
    );
  });

  it("renders competitor visibility when data exists", async () => {
    renderSummary();

    expect(await screen.findByText("Competitor visibility")).toBeInTheDocument();
    expect(screen.getByText("Contoso Monitor")).toBeInTheDocument();
    expect(screen.getByText("50%")).toBeInTheDocument();
    expect(screen.getByText("0.66")).toBeInTheDocument();
  });

  it("renders top sources when citation data exists", async () => {
    renderSummary();

    expect(await screen.findByText("Top sources")).toBeInTheDocument();
    expect(screen.getByText("AI visibility benchmarks")).toBeInTheDocument();
    expect(screen.getByText("example.com")).toBeInTheDocument();
    expect(screen.getAllByText("3").length).toBeGreaterThan(0);
    expect(screen.getByText("0.70")).toBeInTheDocument();
  });

  it("shows an API error state", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailFixture },
      { body: { detail: "Failed to load audit summary." }, status: 500 },
    ]);

    renderRoute("/audits/42");

    expect(await screen.findByText("Audit unavailable.")).toBeInTheDocument();
  });

  it("does not request raw results or scoring inputs", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailFixture },
      { body: auditSummaryFixture },
      { body: auditSummaryV2Fixture },
      { body: auditAnswerMatrixFixture },
    ]);

    renderRoute("/audits/42");
    await screen.findByRole("heading", { name: "Acme AI" });

    expect(fetchMock).not.toHaveBeenCalledWith(
      "http://localhost:8000/audits/42/results",
      expect.anything(),
    );
  });

  it("redirects the legacy summary URL to the canonical audit page", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailFixture },
      { body: auditSummaryFixture },
      { body: auditSummaryV2Fixture },
      { body: auditAnswerMatrixFixture },
    ]);

    renderRoute("/audits/42/summary");

    expect(await screen.findByRole("heading", { name: "Acme AI" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Summary" })).toHaveAttribute("href", "/audits/42");
  });
});
