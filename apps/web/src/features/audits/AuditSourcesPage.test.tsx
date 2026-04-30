import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  auditSummaryFixture,
  currentUserFixture,
  emptyAuditSummaryFixture,
} from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";
import { renderRoute } from "../../test/render";

function renderSources(summary = auditSummaryFixture) {
  const fetchMock = mockFetchSequence([{ body: currentUserFixture }, { body: summary }]);
  renderRoute("/audits/42/sources");
  return fetchMock;
}

describe("audit sources page", () => {
  it("shows loading state while sources are being fetched", async () => {
    const fetchMock = vi.fn();
    fetchMock.mockResolvedValueOnce({
      json: async () => currentUserFixture,
      ok: true,
      status: 200,
      statusText: "OK",
    } satisfies Partial<Response>);
    fetchMock.mockReturnValue(new Promise(() => undefined));
    vi.stubGlobal("fetch", fetchMock);

    renderRoute("/audits/42/sources");

    expect(await screen.findByRole("status")).toHaveTextContent("Loading sources...");
  });

  it("renders source summary data with citation counts", async () => {
    renderSources();

    expect(await screen.findByRole("heading", { name: "Source intelligence" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Sources" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Summary" })).toHaveAttribute(
      "href",
      "/audits/42",
    );
    expect(screen.getByRole("link", { name: "Results" })).toHaveAttribute(
      "href",
      "/audits/42/results",
    );
    expect(screen.getByText("AI visibility benchmarks")).toBeInTheDocument();
    expect(screen.getByText("example.com")).toBeInTheDocument();
    expect(screen.getByText("openai")).toBeInTheDocument();
    expect(screen.getByText("article")).toBeInTheDocument();
    expect(screen.getAllByText("3").length).toBeGreaterThan(0);
    expect(screen.getByText("0.70")).toBeInTheDocument();
  });

  it("renders an empty sources state", async () => {
    renderSources(emptyAuditSummaryFixture);

    expect(await screen.findByText("No sources yet")).toBeInTheDocument();
    expect(
      screen.getByText("Source citations appear after audit runs return cited answers."),
    ).toBeInTheDocument();
  });

  it("safely renders malformed or partially missing source fields", async () => {
    renderSources({
      ...auditSummaryFixture,
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

    expect(await screen.findByText("Untitled source")).toBeInTheDocument();
    expect(screen.getByText("No URL")).toBeInTheDocument();
    expect(screen.getAllByText("N/A").length).toBeGreaterThan(1);
  });

  it("sorts sources by provider when selected", async () => {
    const user = userEvent.setup();
    renderSources({
      ...auditSummaryFixture,
      sources: [
        auditSummaryFixture.sources[0],
        {
          title: "Anthropic source",
          url: "https://anthropic.example/source",
          domain: "anthropic.example",
          provider: "anthropic",
          source_type: "docs",
          citation_count: 1,
          related_query_count: 1,
          source_quality_score: 0.6,
        },
      ],
    });

    await screen.findByText("AI visibility benchmarks");
    await user.selectOptions(screen.getByLabelText("Sort sources"), "provider");

    const anthropic = screen.getByText("Anthropic source");
    const openai = screen.getByText("AI visibility benchmarks");
    expect(
      anthropic.compareDocumentPosition(openai) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it("shows an API error state", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: { detail: "Failed to load audit summary." }, status: 500 },
    ]);

    renderRoute("/audits/42/sources");

    expect(await screen.findByText("Unable to load sources.")).toBeInTheDocument();
  });

  it("does not crawl source URLs or calculate quality client-side", async () => {
    const fetchMock = renderSources();

    await screen.findByText("AI visibility benchmarks");
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock).not.toHaveBeenCalledWith("https://example.com/benchmarks", expect.anything());
  });
});
