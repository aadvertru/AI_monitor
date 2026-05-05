import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  auditCreateResponseFixture,
  auditDetailFixture,
  auditEstimateFixture,
  auditPipelineRunFixture,
  auditResultsFixture,
  auditSummaryFixture,
  currentUserFixture,
  modelCatalogWireFixture,
  unauthenticatedAuthErrorFixture,
} from "./fixtures";
import { renderRoute } from "./render";

const apiBaseUrl = "http://localhost:8000";

type SmokeResponse = {
  body: unknown;
  method?: string;
  path: string;
  status?: number;
};

function mockSmokeBackend(responses: SmokeResponse[]) {
  const queue = [...responses];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const requestMethod = init?.method ?? "GET";
    const next = queue.shift();

    if (!url.startsWith(apiBaseUrl)) {
      throw new Error(`Unexpected external request in smoke flow: ${url}`);
    }
    if (!next) {
      throw new Error(`Unexpected API request in smoke flow: ${requestMethod} ${url}`);
    }

    expect(url).toBe(`${apiBaseUrl}${next.path}`);
    expect(requestMethod).toBe(next.method ?? "GET");

    return {
      json: async () => next.body,
      ok: !next.status || (next.status >= 200 && next.status < 300),
      status: next.status ?? 200,
      statusText: next.status ? "Error" : "OK",
    } satisfies Partial<Response>;
  });

  vi.stubGlobal("fetch", fetchMock);
  return { fetchMock, remainingResponses: queue };
}

describe("authenticated SCDL smoke flow", () => {
  it("logs in, creates an audit, triggers a run, and inspects summary and results", async () => {
    const { fetchMock, remainingResponses } = mockSmokeBackend([
      { path: "/auth/me", body: unauthenticatedAuthErrorFixture, status: 401 },
      { path: "/auth/me", body: unauthenticatedAuthErrorFixture, status: 401 },
      { path: "/auth/login", method: "POST", body: currentUserFixture },
      { path: "/audits", body: [] },
      { path: "/model-catalog", body: modelCatalogWireFixture },
      { path: "/audits/estimate", method: "POST", body: auditEstimateFixture },
      { path: "/audits", method: "POST", body: auditCreateResponseFixture },
      { path: "/audits/42", body: auditDetailFixture },
      { path: "/audits/42/summary", body: auditSummaryFixture },
      { path: "/audits/42/run-pipeline", method: "POST", body: auditPipelineRunFixture },
      { path: "/audits/42", body: { ...auditDetailFixture, status: "completed" } },
      { path: "/audits/42/summary", body: { ...auditSummaryFixture, status: "completed" } },
      { path: "/audits/42/results", body: auditResultsFixture },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits");

    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument();

    await user.type(screen.getByLabelText("Email"), "user@example.com");
    await user.type(screen.getByLabelText("Password"), "secret");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("heading", { name: "Audits" })).toBeInTheDocument();
    expect(await screen.findByText("No audits yet")).toBeInTheDocument();

    await user.click(screen.getAllByRole("link", { name: "New audit" })[0]);
    await user.type(await screen.findByLabelText("Brand name"), "Acme AI");
    await user.type(screen.getByLabelText("Brand domain"), "acme.example");
    await user.type(await screen.findByLabelText("Seed query 1"), "best ai visibility tools");
    await user.click(await screen.findByLabelText("GPT-4o mini"));
    await waitFor(() => {
      expect(screen.queryByText("Estimating checks...")).not.toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    expect(await screen.findByRole("heading", { name: "Acme AI" })).toBeInTheDocument();
    expect(screen.getAllByText(/Audit #1/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/acme\.example/).length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: "Start audit" }));
    expect((await screen.findAllByText("Completed")).length).toBeGreaterThan(0);

    expect(screen.getByRole("link", { name: "Summary" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByText("Contoso Monitor")).toBeInTheDocument();
    expect(screen.getAllByText("best ai visibility tools").length).toBeGreaterThan(0);

    await user.click(screen.getByRole("link", { name: "View related rows" }));
    expect(await screen.findByRole("heading", { name: "Audit results" })).toBeInTheDocument();
    expect(screen.getAllByText("mock").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Success").length).toBeGreaterThan(0);
    expect(screen.getByText("Provider failed.")).toBeInTheDocument();

    await waitFor(() => {
      expect(remainingResponses).toHaveLength(0);
    });
    expect(fetchMock).not.toHaveBeenCalledWith(
      expect.stringMatching(/^https?:\/\/(api\.openai|api\.anthropic|generativelanguage)/),
      expect.anything(),
    );
  });
});
