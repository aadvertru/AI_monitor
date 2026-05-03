import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  auditDetailFixture,
  auditListFixture,
  auditSummaryFixture,
  currentUserFixture,
} from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";
import { renderRoute } from "../../test/render";
import type { AuditListItem, AuditStatus } from "../../lib/api/types";
import { statusLabels } from "./auditStatusMeta";

function renderAudits(audits: AuditListItem[]) {
  mockFetchSequence([{ body: currentUserFixture }, { body: audits }]);
  renderRoute("/audits");
}

describe("audits dashboard page", () => {
  it("renders audits returned by the API", async () => {
    renderAudits(auditListFixture);

    expect(await screen.findByRole("heading", { name: "Audits" })).toBeInTheDocument();
    expect(await screen.findByRole("link", { name: "Acme AI" })).toBeInTheDocument();
    expect(screen.getByText("acme.example")).toBeInTheDocument();
    expect(screen.getByText("#1")).toBeInTheDocument();
    expect(screen.getByText("L1")).toBeInTheDocument();
    expect(screen.getByText("mock")).toBeInTheDocument();
    await userEvent.setup().click(screen.getByRole("button", { name: "Actions for audit #42" }));
    expect(screen.getByRole("menuitem", { name: "Open" })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: "Refresh" })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: "Duplicate" })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: "Archive" })).toBeInTheDocument();
    expect(screen.queryByRole("menuitem", { name: "Delete permanently" })).not.toBeInTheDocument();
  });

  it("renders an empty state with create-audit calls to action", async () => {
    renderAudits([]);

    expect(await screen.findByText("No audits yet")).toBeInTheDocument();
    expect(screen.getByText("Create an audit to track AI visibility.")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "New audit" })).toHaveLength(2);
  });

  it("shows loading state while audits are being fetched", async () => {
    const fetchMock = vi.fn();
    fetchMock.mockResolvedValueOnce({
      json: async () => currentUserFixture,
      ok: true,
      status: 200,
      statusText: "OK",
    } satisfies Partial<Response>);
    fetchMock.mockReturnValueOnce(new Promise(() => undefined));
    vi.stubGlobal("fetch", fetchMock);

    renderRoute("/audits");

    expect(await screen.findByRole("status")).toHaveTextContent("Loading audits...");
  });

  it("shows an error state when the audits API fails", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: { detail: "Server error" }, status: 500 },
    ]);

    renderRoute("/audits");

    expect(await screen.findByText("Unable to load audits.")).toBeInTheDocument();
  });

  it("navigates from an audit row to the detail route", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: auditListFixture },
      { body: auditDetailFixture },
      { body: auditSummaryFixture },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits");

    await user.click(await screen.findByRole("link", { name: "Acme AI" }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Acme AI" })).toBeInTheDocument();
    });
    expect(screen.getByText("Audit #1 · acme.example")).toBeInTheDocument();
  });

  it("navigates to the create audit route", async () => {
    const user = userEvent.setup();
    renderAudits([]);

    const createLinks = await screen.findAllByRole("link", { name: "New audit" });
    await user.click(createLinks[0]);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Create audit" })).toBeInTheDocument();
    });
  });

  it("renders documented audit status values as badges", async () => {
    const statuses = Object.keys(statusLabels) as AuditStatus[];
    const audits = statuses.map((status, index) => ({
      ...auditListFixture[0],
      audit_id: index + 1,
      audit_number: index + 1,
      brand_name: `Brand ${status}`,
      status,
    }));

    renderAudits(audits);

    for (const status of statuses) {
      expect(await screen.findByText(statusLabels[status])).toBeInTheDocument();
    }
  });

  it("archives an audit after confirmation and removes it from active list", async () => {
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: auditListFixture },
      { body: { audit_id: 42, status: "created", archived_at: "2026-05-02T10:00:00Z" } },
      { body: [] },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits");

    await user.click(await screen.findByRole("button", { name: "Actions for audit #42" }));
    await user.click(screen.getByRole("menuitem", { name: "Archive" }));

    expect(confirmSpy).toHaveBeenCalledWith("Вы уверены, что хотите архивировать этот аудит?");
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/audits/42/archive",
        expect.objectContaining({ method: "POST" }),
      );
    });
    expect(await screen.findByText("No audits yet")).toBeInTheDocument();
    confirmSpy.mockRestore();
  });

  it("shows archived audits and restores them", async () => {
    const archivedAudit = {
      ...auditListFixture[0],
      archived_at: "2026-05-02T10:00:00Z",
    };
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: [] },
      { body: [archivedAudit] },
      { body: { audit_id: 42, status: "created", archived_at: null } },
      { body: [] },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits");

    await user.click(await screen.findByRole("button", { name: "Archived" }));
    expect(await screen.findByRole("link", { name: "Acme AI" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Actions for audit #42" }));
    expect(screen.getByRole("menuitem", { name: "Restore" })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: "Delete permanently" })).toBeInTheDocument();
    expect(screen.queryByRole("menuitem", { name: "Archive" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("menuitem", { name: "Restore" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/audits/42/restore",
        expect.objectContaining({ method: "POST" }),
      );
    });
  });

  it("deletes archived audits after confirmation", async () => {
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    const archivedAudit = {
      ...auditListFixture[0],
      archived_at: "2026-05-02T10:00:00Z",
    };
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: [] },
      { body: [archivedAudit] },
      { body: undefined, status: 204 },
      { body: [] },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits");

    await user.click(await screen.findByRole("button", { name: "Archived" }));
    await user.click(await screen.findByRole("button", { name: "Actions for audit #42" }));
    await user.click(screen.getByRole("menuitem", { name: "Delete permanently" }));

    expect(confirmSpy).toHaveBeenCalledWith(
      "Удалить аудит навсегда? Это действие нельзя отменить.",
    );
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/audits/42",
        expect.objectContaining({ method: "DELETE" }),
      );
    });
    confirmSpy.mockRestore();
  });
});
