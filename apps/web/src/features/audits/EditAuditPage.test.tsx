import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import {
  auditDetailFixture,
  currentUserFixture,
} from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";
import { renderRoute } from "../../test/render";

describe("edit audit page", () => {
  it("loads a created audit setup and saves updates", async () => {
    const updatedAudit = {
      ...auditDetailFixture,
      brand_name: "Acme Updated",
      brand_domain: "updated.example",
      providers: ["mock", "openai"],
      seed_queries: ["updated query"],
      seed_query_items: [{ text: "updated query", type: null, source: "user" }],
    };
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailFixture },
      { body: updatedAudit },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/42/edit");

    expect(await screen.findByRole("heading", { name: "Edit audit setup" })).toBeInTheDocument();
    expect(screen.getByLabelText("Brand description")).toHaveAttribute("maxLength", "500");
    expect(screen.getByText("34 / 500")).toBeInTheDocument();
    await user.clear(screen.getByLabelText("Brand name"));
    await user.type(screen.getByLabelText("Brand name"), "Acme Updated");
    await user.clear(screen.getByLabelText("Brand domain"));
    await user.type(screen.getByLabelText("Brand domain"), "updated.example");
    await user.click(screen.getByLabelText("OpenAI"));
    await user.clear(screen.getByLabelText("Seed query 1"));
    await user.type(screen.getByLabelText("Seed query 1"), "updated query");
    await user.click(screen.getByRole("button", { name: "Save setup" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/audits/42",
        expect.objectContaining({ method: "PUT" }),
      );
    });
    const [, request] = fetchMock.mock.calls[2];
    expect(JSON.parse(String(request?.body))).toMatchObject({
      brand_name: "Acme Updated",
      brand_domain: "updated.example",
      providers: ["mock", "openai"],
      seed_query_items: [{ text: "updated query", type: null, source: "user" }],
    });
    expect(JSON.parse(String(request?.body))).not.toHaveProperty("seed_queries");
  });

  it("validates edited brand domain format before API submission", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailFixture },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/42/edit");

    expect(await screen.findByRole("heading", { name: "Edit audit setup" })).toBeInTheDocument();
    await user.clear(screen.getByLabelText("Brand domain"));
    await user.type(screen.getByLabelText("Brand domain"), "https://updated.example/page");
    await user.click(screen.getByRole("button", { name: "Save setup" }));

    expect(await screen.findByText("Invalid domain format")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("generates additional seed queries before saving a created audit", async () => {
    const updatedAudit = {
      ...auditDetailFixture,
      seed_queries: ["best ai visibility tools", "best acme alternatives"],
      seed_query_items: [
        { text: "best ai visibility tools", type: null, source: "user" },
        { text: "best acme alternatives", type: "alternative", source: "ai" },
      ],
    };
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailFixture },
      {
        body: {
          suggestions: [
            {
              text: "best acme alternatives",
              type: "alternative",
              source: "ai",
            },
          ],
        },
      },
      { body: updatedAudit },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/42/edit");

    expect(await screen.findByRole("heading", { name: "Edit audit setup" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Generate seed queries" }));
    await user.click(screen.getByRole("button", { name: "Generate 10 queries" }));
    expect(await screen.findByDisplayValue("best acme alternatives")).toBeInTheDocument();
    expect(screen.getByLabelText("Query type 2")).toHaveValue("alternative");
    await user.click(screen.getByRole("button", { name: "Save setup" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/audits/42",
        expect.objectContaining({ method: "PUT" }),
      );
    });
    const [, request] = fetchMock.mock.calls[3];
    expect(JSON.parse(String(request?.body))).toMatchObject({
      seed_query_items: [
        { text: "best ai visibility tools", type: null, source: "user" },
        { text: "best acme alternatives", type: "alternative", source: "ai" },
      ],
    });
  });

  it("hides source intelligence for L1 audits and saves it as disabled", async () => {
    const l1AuditWithLegacySourceIntelligence = {
      ...auditDetailFixture,
      enable_source_intelligence: true,
      scdl_level: "L1",
    };
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: l1AuditWithLegacySourceIntelligence },
      { body: { ...l1AuditWithLegacySourceIntelligence, enable_source_intelligence: false } },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/42/edit");

    expect(await screen.findByRole("heading", { name: "Edit audit setup" })).toBeInTheDocument();
    expect(screen.queryByLabelText("Source intelligence")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Save setup" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/audits/42",
        expect.objectContaining({ method: "PUT" }),
      );
    });
    const [, request] = fetchMock.mock.calls[2];
    expect(JSON.parse(String(request?.body))).toMatchObject({
      scdl_level: "L1",
      enable_source_intelligence: false,
    });
  });

  it("shows source intelligence for L2 audits", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: { ...auditDetailFixture, scdl_level: "L2" } },
    ]);

    renderRoute("/audits/42/edit");

    expect(await screen.findByRole("heading", { name: "Edit audit setup" })).toBeInTheDocument();
    expect(screen.getByLabelText("Source intelligence")).toBeInTheDocument();
  });

  it("does not render editable form controls for completed audits", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: { ...auditDetailFixture, status: "completed" } },
    ]);

    renderRoute("/audits/42/edit");

    expect(
      await screen.findByText(/Only audits in Created status can be edited./),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Save setup" })).not.toBeInTheDocument();
  });
});
