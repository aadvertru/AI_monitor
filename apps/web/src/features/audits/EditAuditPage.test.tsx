import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import {
  auditDetailFixture,
  auditDetailWithModelTargetsFixture,
  auditEstimateFixture,
  auditTargetWireFixture,
  currentUserFixture,
  modelCatalogWireFixture,
} from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";
import { renderRoute } from "../../test/render";

describe("edit audit page", () => {
  const selectedGptL1Target = {
    ai_family: "chatgpt",
    execution_provider: "openrouter",
    model_provider: "openai",
    model_id: "openai/gpt-4o-mini",
    display_name: "GPT-4o mini",
    level: "L1",
    gateway: true,
    gateway_l2_experimental: false,
  };
  const selectedGptL2Target = {
    ...selectedGptL1Target,
    level: "L2",
    gateway_l2_experimental: true,
  };

  function jsonRequestBodyFor(
    fetchMock: ReturnType<typeof mockFetchSequence>,
    url: string,
    method: string,
  ) {
    const call = fetchMock.mock.calls.find(
      ([callUrl, init]) => callUrl === url && (init as RequestInit | undefined)?.method === method,
    );
    return JSON.parse(String((call?.[1] as RequestInit | undefined)?.body));
  }

  it("loads a created audit setup and saves updates", async () => {
    const updatedAudit = {
      ...auditDetailWithModelTargetsFixture,
      brand_name: "Acme Updated",
      brand_domain: "updated.example",
      seed_queries: ["updated query"],
      seed_query_items: [{ text: "updated query", type: null, source: "user" }],
      model_targets: [selectedGptL1Target, selectedGptL2Target],
    };
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailWithModelTargetsFixture },
      { body: modelCatalogWireFixture },
      { body: auditEstimateFixture },
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
    expect(await screen.findByLabelText("GPT-4o mini")).toBeChecked();
    expect(screen.getByLabelText("GPT-4o mini L2")).toBeChecked();
    await user.clear(screen.getByLabelText("Seed query 1"));
    await user.type(screen.getByLabelText("Seed query 1"), "updated query");
    await user.click(screen.getByRole("button", { name: "Save setup" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/audits/42",
        expect.objectContaining({ method: "PUT" }),
      );
    });
    const body = jsonRequestBodyFor(fetchMock, "http://localhost:8000/audits/42", "PUT");
    expect(body).toMatchObject({
      brand_name: "Acme Updated",
      brand_domain: "updated.example",
      seed_query_items: [{ text: "updated query", type: null, source: "user" }],
      model_targets: [selectedGptL1Target, selectedGptL2Target],
    });
    expect(body).not.toHaveProperty("seed_queries");
    expect(body).not.toHaveProperty("providers");
    expect(body).not.toHaveProperty("scdl_level");
    expect(body).not.toHaveProperty("modelTargets");
  });

  it("validates edited brand domain format before API submission", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailWithModelTargetsFixture },
      { body: modelCatalogWireFixture },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/42/edit");

    expect(await screen.findByRole("heading", { name: "Edit audit setup" })).toBeInTheDocument();
    await user.clear(screen.getByLabelText("Brand domain"));
    await user.type(screen.getByLabelText("Brand domain"), "https://updated.example/page");
    await user.click(screen.getByRole("button", { name: "Save setup" }));

    expect(await screen.findByText("Invalid domain format")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalledWith(
      "http://localhost:8000/audits/42",
      expect.objectContaining({ method: "PUT" }),
    );
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
      { body: auditDetailWithModelTargetsFixture },
      { body: modelCatalogWireFixture },
      { body: auditEstimateFixture },
      { body: auditEstimateFixture },
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
      { body: auditEstimateFixture },
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
    expect(jsonRequestBodyFor(fetchMock, "http://localhost:8000/audits/42", "PUT")).toMatchObject({
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
      { body: modelCatalogWireFixture },
      { body: auditEstimateFixture },
      { body: { ...l1AuditWithLegacySourceIntelligence, enable_source_intelligence: false } },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/42/edit");

    expect(await screen.findByRole("heading", { name: "Edit audit setup" })).toBeInTheDocument();
    expect(await screen.findByLabelText("GPT-4o mini")).not.toBeChecked();
    expect(screen.queryByLabelText("Source intelligence")).not.toBeInTheDocument();
    await user.click(screen.getByLabelText("GPT-4o mini"));
    await user.click(screen.getByRole("button", { name: "Save setup" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/audits/42",
        expect.objectContaining({ method: "PUT" }),
      );
    });
    const body = jsonRequestBodyFor(fetchMock, "http://localhost:8000/audits/42", "PUT");
    expect(body).toMatchObject({
      enable_source_intelligence: false,
      model_targets: [selectedGptL1Target],
    });
    expect(body).not.toHaveProperty("scdl_level");
  });

  it("shows source intelligence for L2 audits", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailWithModelTargetsFixture },
      { body: modelCatalogWireFixture },
    ]);

    renderRoute("/audits/42/edit");

    expect(await screen.findByRole("heading", { name: "Edit audit setup" })).toBeInTheDocument();
    expect(await screen.findByLabelText("Source intelligence")).toBeInTheDocument();
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
