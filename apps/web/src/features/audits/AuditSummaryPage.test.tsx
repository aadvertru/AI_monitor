import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  auditDetailFixture,
  auditSummaryFixture,
  currentUserFixture,
  emptyAuditSummaryFixture,
  partialAuditSummaryFixture,
} from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";
import { renderRoute } from "../../test/render";

function renderSummary(summary = auditSummaryFixture) {
  mockFetchSequence([{ body: currentUserFixture }, { body: auditDetailFixture }, { body: summary }]);
  renderRoute("/audits/42");
}

describe("audit summary page", () => {
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
    expect(screen.getByRole("link", { name: "Summary" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Summary" })).toHaveAttribute("href", "/audits/42");
    expect(screen.getByRole("link", { name: "Results" })).toHaveAttribute("href", "/audits/42/results");
    expect(screen.getByRole("link", { name: "Sources" })).toHaveAttribute("href", "/audits/42/sources");
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("Queries")).toBeInTheDocument();
    expect(screen.getAllByText("3").length).toBeGreaterThan(0);
    expect(screen.getByText("Runs")).toBeInTheDocument();
    expect(screen.getByText("6")).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
    expect(screen.getByText("67%")).toBeInTheDocument();
    expect(screen.getByText("0.74")).toBeInTheDocument();
  });

  it("renders an empty or newly created audit summary safely", async () => {
    renderSummary(emptyAuditSummaryFixture);

    expect(await screen.findByText("Created")).toBeInTheDocument();
    expect(screen.getByText("No run data is available yet.")).toBeInTheDocument();
    expect(screen.getByText("No provider scores yet.")).toBeInTheDocument();
    expect(screen.getByText("No critical queries detected.")).toBeInTheDocument();
    expect(screen.getByText("No competitors detected.")).toBeInTheDocument();
    expect(screen.getByText("No source citations yet.")).toBeInTheDocument();
    expect(screen.getByText("N/A")).toBeInTheDocument();
  });

  it("renders partial or failed audit summary states safely", async () => {
    renderSummary(partialAuditSummaryFixture);

    expect(await screen.findByText("Partial")).toBeInTheDocument();
    expect(screen.getAllByText("50%").length).toBeGreaterThan(0);
  });

  it("handles missing optional summary fields", async () => {
    renderSummary({
      ...auditSummaryFixture,
      average_score: null,
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

  it("renders critical queries with backend-provided reasons", async () => {
    renderSummary();

    expect(await screen.findByText("Critical queries")).toBeInTheDocument();
    expect(screen.getByText("best ai visibility tools")).toBeInTheDocument();
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
    ]);

    renderRoute("/audits/42");
    await screen.findByRole("heading", { name: "Acme AI" });

    expect(fetchMock).not.toHaveBeenCalledWith(
      "http://localhost:8000/audits/42/results",
      expect.anything(),
    );
  });

  it("redirects the legacy summary URL to the canonical audit page", async () => {
    mockFetchSequence([{ body: currentUserFixture }, { body: auditDetailFixture }, { body: auditSummaryFixture }]);

    renderRoute("/audits/42/summary");

    expect(await screen.findByRole("heading", { name: "Acme AI" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Summary" })).toHaveAttribute("href", "/audits/42");
  });
});
