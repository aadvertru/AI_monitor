import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import {
  auditComparisonFixture,
  auditTrendsFixture,
  comparisonCandidatesFixture,
} from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";
import { renderWithClient } from "../../test/render";
import { AuditLongitudinalPanel } from "./AuditLongitudinalPanel";

describe("AuditLongitudinalPanel", () => {
  it("stays idle until history is requested", () => {
    renderWithClient(
      <AuditLongitudinalPanel auditId={42} brandId={7} auditStatus="completed" />,
    );

    expect(screen.getByText("Historical comparison")).toBeInTheDocument();
    expect(screen.getByText("History is loaded on demand to keep the audit page fast.")).toBeInTheDocument();
  });

  it("loads candidates, comparison, and trends on demand", async () => {
    const fetchMock = mockFetchSequence([
      { body: comparisonCandidatesFixture },
      { body: auditTrendsFixture },
      { body: auditComparisonFixture },
    ]);
    const user = userEvent.setup();

    renderWithClient(
      <AuditLongitudinalPanel auditId={42} brandId={7} auditStatus="completed" />,
    );

    await user.click(screen.getByRole("button", { name: "Load history" }));

    expect(await screen.findByText("Compared by normalized domain.")).toBeInTheDocument();
    expect(screen.getByText("Audit #4")).toBeInTheDocument();
    expect(screen.getAllByText("+50.0 pts").length).toBeGreaterThan(0);
    expect(screen.getByText("GPT-4o mini")).toBeInTheDocument();
    expect(screen.getByText("example.com")).toBeInTheDocument();
    expect(screen.getByText("AI visibility")).toBeInTheDocument();
    expect(screen.getByText("Contoso Monitor")).toBeInTheDocument();
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/audits/42/comparison-candidates",
        expect.objectContaining({ credentials: "include" }),
      );
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/brands/7/audit-trends",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/audits/42/compare?previous_audit_id=41",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("shows empty state for audits without candidates", async () => {
    mockFetchSequence([
      { body: { audit_id: 42, candidates: [] } },
      { body: { brand_id: 7, points: [], warnings: [] } },
    ]);
    const user = userEvent.setup();

    renderWithClient(
      <AuditLongitudinalPanel auditId={42} brandId={7} auditStatus="completed" />,
    );

    await user.click(screen.getByRole("button", { name: "Load history" }));

    expect(await screen.findByText("No comparable previous audits were found.")).toBeInTheDocument();
  });

  it("does not render for non-terminal audits", () => {
    const { container } = renderWithClient(
      <AuditLongitudinalPanel auditId={42} brandId={7} auditStatus="created" />,
    );

    expect(container).toBeEmptyDOMElement();
  });
});
