import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  auditDetailFixture,
  auditStatusFixture,
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
    { body: { ...auditStatusFixture, status } },
  ]);
  renderRoute("/audits/42");
}

describe("audit detail page", () => {
  it("renders audit metadata with mocked API data", async () => {
    renderDetail();

    expect(await screen.findByRole("heading", { name: "Acme AI" })).toBeInTheDocument();
    expect(screen.getByText("Audit #42 · acme.example")).toBeInTheDocument();
    expect(screen.getByText("AI visibility monitoring platform.")).toBeInTheDocument();
    expect(screen.getByText("mock")).toBeInTheDocument();
    expect(screen.getByText("25%")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Summary" })).toHaveAttribute(
      "href",
      "/audits/42/summary",
    );
    expect(screen.getByRole("link", { name: "Results" })).toHaveAttribute(
      "href",
      "/audits/42/results",
    );
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
      { body: { detail: "Audit was not found." }, status: 404 },
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
      { body: auditStatusFixture },
      { body: { ...auditDetailFixture, brand_name: "Acme Refreshed" } },
      { body: { ...auditStatusFixture, status: "completed", completion_ratio: 1 } },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/42");

    await screen.findByRole("heading", { name: "Acme AI" });
    await user.click(screen.getByRole("button", { name: "Refresh" }));

    expect(await screen.findByRole("heading", { name: "Acme Refreshed" })).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(5);
  });

  it("starts an audit when the run endpoint is supported", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailFixture },
      { body: auditStatusFixture },
      { body: { audit_id: 42, status: "running", scheduled_jobs: 4, total_jobs: 4 } },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/42");

    await user.click(await screen.findByRole("button", { name: "Start audit" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/audits/42/run",
        expect.objectContaining({ method: "POST" }),
      );
    });
    expect(await screen.findByRole("button", { name: "Running" })).toBeDisabled();
  });

  it("disables the run action while the audit is running", async () => {
    renderDetail("running");

    expect(await screen.findByRole("button", { name: "Running" })).toBeDisabled();
  });
});
