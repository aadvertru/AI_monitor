import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  auditDetailFixture,
  currentUserFixture,
  sourceDomainsFixture,
} from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";
import { renderRoute } from "../../test/render";

function renderSources(domains = sourceDomainsFixture) {
  const fetchMock = mockFetchSequence([
    { body: currentUserFixture },
    { body: auditDetailFixture },
    { body: domains },
  ]);
  renderRoute("/audits/42/sources");
  return fetchMock;
}

describe("audit sources page", () => {
  it("shows loading state while source domains are being fetched", async () => {
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

  it("renders source domain rows with counts", async () => {
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
    expect(screen.getByRole("heading", { name: "example.com" })).toBeInTheDocument();
    expect(screen.getByText("3 citations · 2 URLs · 2 queries")).toBeInTheDocument();
    expect(screen.getByText(/openrouter · L2 · openai\/gpt-4o-mini/)).toBeInTheDocument();
    expect(screen.getByText("Skipped 1 invalid source URL(s).")).toBeInTheDocument();
  });

  it("expands and collapses URL evidence", async () => {
    const user = userEvent.setup();
    renderSources();

    await screen.findByRole("heading", { name: "example.com" });
    expect(screen.queryByText("Example docs")).not.toBeInTheDocument();

    const button = screen.getByRole("button", { name: "Details" });
    await user.click(button);

    expect(button).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("Example docs")).toBeInTheDocument();
    expect(screen.getByText("Evidence snippet for the cited source.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /https:\/\/docs.example.com\/path/ })).toHaveAttribute(
      "rel",
      "noopener noreferrer",
    );

    await user.click(button);
    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByText("Example docs")).not.toBeInTheDocument();
  });

  it("renders an empty sources state", async () => {
    renderSources({ audit_id: 42, domains: [], warnings: [] });

    expect(await screen.findByText("No sources yet")).toBeInTheDocument();
    expect(
      screen.getByText("Source citations appear after audit runs return cited answers."),
    ).toBeInTheDocument();
  });

  it("safely renders partially missing URL evidence fields", async () => {
    renderSources({
      audit_id: 42,
      domains: [
        {
          domain: "example.com",
          source_count: 1,
          unique_url_count: 1,
          query_count: 0,
          target_count: 0,
          levels: [],
          models: [],
          providers: [],
          urls: [
            {
              url: "https://example.com/path",
              normalized_url: "https://example.com/path",
            },
          ],
        },
      ],
      warnings: [],
    });

    await screen.findByRole("heading", { name: "example.com" });
    await userEvent.click(screen.getByRole("button", { name: "Details" }));
    expect(screen.getAllByText("https://example.com/path").length).toBeGreaterThan(0);
    expect(screen.getByText(/N\/A · N\/A · N\/A/)).toBeInTheDocument();
  });

  it("shows an API error state", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailFixture },
      { body: { detail: "Failed to load source domains." }, status: 500 },
    ]);

    renderRoute("/audits/42/sources");

    expect(await screen.findByText("Unable to load sources.")).toBeInTheDocument();
  });

  it("does not crawl source URLs or render unsafe raw fields", async () => {
    const fetchMock = renderSources({
      ...sourceDomainsFixture,
      domains: [
        {
          ...sourceDomainsFixture.domains[0]!,
          urls: [
            {
              ...sourceDomainsFixture.domains[0]!.urls[0]!,
              // @ts-expect-error - fixture intentionally simulates unsafe server drift.
              raw_response: "hidden",
            },
          ],
        },
      ],
    });

    await screen.findByRole("heading", { name: "example.com" });
    await userEvent.click(screen.getByRole("button", { name: "Details" }));
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock).not.toHaveBeenCalledWith(
      "https://docs.example.com/path",
      expect.anything(),
    );
    expect(screen.queryByText("hidden")).not.toBeInTheDocument();
  });
});
