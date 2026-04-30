import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  auditResultsFixture,
  currentUserFixture,
  emptyAuditResultsFixture,
} from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";
import { renderRoute } from "../../test/render";

function renderResults(results = auditResultsFixture) {
  mockFetchSequence([{ body: currentUserFixture }, { body: results }]);
  renderRoute("/audits/42/results");
}

describe("audit results page", () => {
  it("shows loading state while results are being fetched", async () => {
    const fetchMock = vi.fn();
    fetchMock.mockResolvedValueOnce({
      json: async () => currentUserFixture,
      ok: true,
      status: 200,
      statusText: "OK",
    } satisfies Partial<Response>);
    fetchMock.mockReturnValue(new Promise(() => undefined));
    vi.stubGlobal("fetch", fetchMock);

    renderRoute("/audits/42/results");

    expect(await screen.findByRole("status")).toHaveTextContent("Loading results...");
  });

  it("renders successful result rows with mocked API data", async () => {
    renderResults();

    expect(await screen.findByRole("heading", { name: "Audit results" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Results" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Summary" })).toHaveAttribute(
      "href",
      "/audits/42",
    );
    expect(screen.getByRole("link", { name: "Sources" })).toHaveAttribute(
      "href",
      "/audits/42/sources",
    );
    expect(screen.getByText("best ai visibility tools")).toBeInTheDocument();
    expect(screen.getAllByText("mock").length).toBeGreaterThan(0);
    expect(screen.getAllByText("#1").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Success").length).toBeGreaterThan(0);
    expect(screen.getAllByText("L1").length).toBeGreaterThan(0);
  });

  it("renders failed and timeout rows without crashing", async () => {
    renderResults();

    expect((await screen.findAllByText("Error")).length).toBeGreaterThan(0);
    expect(screen.getByText("Provider failed.")).toBeInTheDocument();
    expect(screen.getAllByText("Timeout").length).toBeGreaterThan(0);
    expect(screen.getByText("Provider timed out.")).toBeInTheDocument();
  });

  it("renders an empty results state", async () => {
    renderResults(emptyAuditResultsFixture);

    expect(await screen.findByText("No results yet")).toBeInTheDocument();
    expect(screen.getByText("Run the audit before inspecting per-run outputs.")).toBeInTheDocument();
  });

  it("shows an API error state", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: { detail: "Failed to load audit results." }, status: 500 },
    ]);

    renderRoute("/audits/42/results");

    expect(await screen.findByText("Unable to load results.")).toBeInTheDocument();
  });

  it("distinguishes brand visible and not-visible rows", async () => {
    renderResults();

    expect((await screen.findAllByText("Visible")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Not visible").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Unknown").length).toBeGreaterThan(0);
  });

  it("renders final and component scores in the expandable detail panel", async () => {
    const user = userEvent.setup();
    renderResults();

    expect(await screen.findByText("0.82")).toBeInTheDocument();
    await user.click(screen.getAllByRole("button", { name: "Details" })[0]);

    expect(screen.getByText(/Prominence 0.70/)).toBeInTheDocument();
    expect(screen.getByText(/Sentiment 0.80/)).toBeInTheDocument();
    expect(screen.getByText(/Recommendation 0.60/)).toBeInTheDocument();
    expect(screen.getByText(/Source quality 0.75/)).toBeInTheDocument();
    expect(screen.getByText("Competitors: Contoso Monitor")).toBeInTheDocument();
    expect(screen.getByText("Sources: example.com")).toBeInTheDocument();
  });

  it("filters by provider and status", async () => {
    const user = userEvent.setup();
    renderResults();

    await screen.findByText("best ai visibility tools");
    await user.selectOptions(screen.getByLabelText("Provider"), "openai");

    expect(screen.queryByText("best ai visibility tools")).not.toBeInTheDocument();
    expect(screen.getByText(/brand monitoring platforms/)).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Run status"), "success");

    expect(screen.getByText("No results match the current filters.")).toBeInTheDocument();
  });

  it("filters by brand visibility", async () => {
    const user = userEvent.setup();
    renderResults();

    await screen.findByText("best ai visibility tools");
    await user.selectOptions(screen.getByLabelText("Visibility"), "not_visible");

    await waitFor(() => {
      expect(screen.queryByText("best ai visibility tools")).not.toBeInTheDocument();
    });
    expect(screen.getByText(/brand monitoring platforms/)).toBeInTheDocument();
  });

  it("does not expose raw provider answers", async () => {
    renderResults();

    await screen.findByText("best ai visibility tools");
    expect(screen.queryByText("raw_answer")).not.toBeInTheDocument();
    expect(screen.queryByText("501")).not.toBeInTheDocument();
  });
});
