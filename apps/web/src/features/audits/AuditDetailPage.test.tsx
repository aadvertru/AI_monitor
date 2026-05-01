import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  auditDetailFixture,
  auditPipelineRunFixture,
  auditStatusFixture,
  auditSummaryFixture,
  currentUserFixture,
} from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";
import { renderRoute } from "../../test/render";
import type { AuditStatus } from "../../lib/api/types";
import { statusLabels } from "./auditStatusMeta";

function renderDetail(status: AuditStatus = "created") {
  mockFetchSequence([
    { body: currentUserFixture },
    { body: { ...auditDetailFixture, status } },
    { body: { ...auditSummaryFixture, status } },
    ...(status === "running" ? [{ body: { ...auditStatusFixture, status } }] : []),
  ]);
  renderRoute("/audits/42");
}

describe("audit detail page", () => {
  it("renders audit metadata with mocked API data", async () => {
    renderDetail();

    expect(await screen.findByRole("heading", { name: "Acme AI" })).toBeInTheDocument();
    expect(screen.getByText("Audit #1 · acme.example")).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Breadcrumb" })).toHaveTextContent(
      "AuditsAudit #1",
    );
    expect(screen.getByRole("link", { name: "Summary" })).toHaveAttribute("href", "/audits/42");
    expect(screen.getByRole("link", { name: "Summary" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Results" })).toHaveAttribute(
      "href",
      "/audits/42/results",
    );
    expect(screen.getByRole("link", { name: "Sources" })).toHaveAttribute(
      "href",
      "/audits/42/sources",
    );
    expect(screen.getByText("Provider summary")).toBeInTheDocument();
    expect(screen.getByText("Critical queries")).toBeInTheDocument();
    expect(screen.getByText("Competitor visibility")).toBeInTheDocument();
  });

  it.each(["created", "running", "completed", "failed"] as const)(
    "renders %s audit status",
    async (status) => {
      renderDetail(status);

      expect(await screen.findAllByText(statusLabels[status])).not.toHaveLength(0);
    },
  );

  it("keeps partial and failed audits inspectable", async () => {
    renderDetail("partial");

    expect(await screen.findByRole("heading", { name: "Acme AI" })).toBeInTheDocument();
    expect(screen.getByText("Partial")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Results" })).toBeInTheDocument();
  });

  it("shows loading state", async () => {
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

  it("shows API error state for not-found or forbidden responses", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: { detail: "Audit was not found." }, status: 404 },
      { body: { detail: "Audit summary was not found." }, status: 404 },
    ]);

    renderRoute("/audits/42");

    expect(await screen.findByText("Audit unavailable.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to audits" })).toHaveAttribute(
      "href",
      "/audits",
    );
  });

  it("manually refreshes audit detail and status", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailFixture },
      { body: auditSummaryFixture },
      { body: { ...auditDetailFixture, brand_name: "Acme Refreshed" } },
      { body: { ...auditSummaryFixture, status: "completed", completion_ratio: 1 } },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/42");

    await screen.findByRole("heading", { name: "Acme AI" });
    await user.click(screen.getByRole("button", { name: "Refresh" }));

    expect(await screen.findByRole("heading", { name: "Acme Refreshed" })).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(5);
  });

  it("starts an audit through the owner pipeline endpoint", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailFixture },
      { body: auditSummaryFixture },
      { body: auditPipelineRunFixture },
      { body: { ...auditDetailFixture, status: "completed" } },
      { body: { ...auditSummaryFixture, status: "completed", total_runs: 4 } },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/42");

    await user.click(await screen.findByRole("button", { name: "Start audit" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/audits/42/run-pipeline",
        expect.objectContaining({ method: "POST" }),
      );
    });
    expect(fetchMock).not.toHaveBeenCalledWith(
      expect.stringContaining("/dev/"),
      expect.anything(),
    );
    expect(await screen.findByText("Completed")).toBeInTheDocument();
  });

  it("disables the start button while pipeline start is pending", async () => {
    const fetchMock = vi.fn();
    fetchMock
      .mockResolvedValueOnce({
        json: async () => currentUserFixture,
        ok: true,
        status: 200,
        statusText: "OK",
      } satisfies Partial<Response>)
      .mockResolvedValueOnce({
        json: async () => auditDetailFixture,
        ok: true,
        status: 200,
        statusText: "OK",
      } satisfies Partial<Response>)
      .mockResolvedValueOnce({
        json: async () => auditSummaryFixture,
        ok: true,
        status: 200,
        statusText: "OK",
      } satisfies Partial<Response>)
      .mockReturnValue(new Promise(() => undefined));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    renderRoute("/audits/42");

    const button = await screen.findByRole("button", { name: "Start audit" });
    await user.click(button);
    await user.click(await screen.findByRole("button", { name: "Starting" }));

    expect(screen.getByRole("button", { name: "Starting" })).toBeDisabled();
    expect(
      fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/audits/42/run-pipeline")),
    ).toHaveLength(1);
  });

  it.each([
    [403, "Real provider execution is disabled."],
    [404, "Audit was not found."],
    [500, "Failed to run audit pipeline."],
  ])("displays pipeline start error %s", async (status, detail) => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailFixture },
      { body: auditSummaryFixture },
      { body: { detail }, status },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/42");

    await user.click(await screen.findByRole("button", { name: "Start audit" }));

    expect(await screen.findByText(detail)).toBeInTheDocument();
  });

  it("does not render raw answers or secrets from pipeline response", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailFixture },
      { body: auditSummaryFixture },
      { body: auditPipelineRunFixture },
      { body: { ...auditDetailFixture, status: "completed" } },
      { body: { ...auditSummaryFixture, status: "completed" } },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/42");

    await user.click(await screen.findByRole("button", { name: "Start audit" }));

    await screen.findByText("Completed");
    expect(screen.queryByText(/raw_answer|request_snapshot|api_key|secret/i)).not.toBeInTheDocument();
  });

  it("starts status polling after a successful pipeline start returns running", async () => {
    let pipelineStarted = false;
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      let body: unknown = auditSummaryFixture;
      if (url.endsWith("/auth/me")) {
        body = currentUserFixture;
      } else if (url.endsWith("/audits/42") && options?.method !== "POST") {
        body = { ...auditDetailFixture, status: pipelineStarted ? "running" : "created" };
      } else if (url.endsWith("/audits/42/run-pipeline")) {
        pipelineStarted = true;
        body = {
          ...auditPipelineRunFixture,
          final_audit_status: "running",
          post_processing: null,
        };
      } else if (url.endsWith("/audits/42/summary")) {
        body = { ...auditSummaryFixture, status: pipelineStarted ? "running" : "created" };
      } else if (url.endsWith("/audits/42/status")) {
        body = { ...auditStatusFixture, status: "running" };
      }
      return {
        json: async () => body,
        ok: true,
        status: 200,
        statusText: "OK",
      } satisfies Partial<Response>;
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    renderRoute("/audits/42");

    await user.click(await screen.findByRole("button", { name: "Start audit" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/audits/42/status",
        expect.objectContaining({ credentials: "include" }),
      );
    });
    expect(
      fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/audits/42/run-pipeline")),
    ).toHaveLength(1);
  });

  it("disables the run action while the audit is running", async () => {
    renderDetail("running");

    expect(await screen.findByRole("button", { name: "Running" })).toBeDisabled();
  });

  it.each(["completed", "partial", "failed"] as const)(
    "polls audit status while running and stops after %s",
    async (terminalStatus) => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: { ...auditDetailFixture, status: "running" } },
      { body: { ...auditSummaryFixture, status: "running" } },
      { body: { ...auditStatusFixture, status: "running" } },
      { body: { ...auditStatusFixture, status: terminalStatus, completion_ratio: 1 } },
      { body: { ...auditDetailFixture, status: terminalStatus } },
      { body: { ...auditSummaryFixture, status: terminalStatus, completion_ratio: 1 } },
    ]);

    renderRoute("/audits/42");

    expect(await screen.findByRole("button", { name: "Running" })).toBeDisabled();
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/audits/42/status",
        expect.objectContaining({ credentials: "include" }),
      );
    });

    await new Promise((resolve) => window.setTimeout(resolve, 2100));

    expect(await screen.findByText(statusLabels[terminalStatus])).toBeInTheDocument();
    const statusCallsAfterTerminal = fetchMock.mock.calls.filter(([url]) =>
      String(url).endsWith("/audits/42/status"),
    ).length;

    await new Promise((resolve) => window.setTimeout(resolve, 2300));

    expect(
      fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/audits/42/status")),
    ).toHaveLength(statusCallsAfterTerminal);
    expect(fetchMock).not.toHaveBeenCalledWith(
      expect.stringContaining("/dev/"),
      expect.anything(),
    );
    expect(
      fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/audits/42/run-pipeline")),
    ).toHaveLength(0);
    },
    8000,
  );
});
