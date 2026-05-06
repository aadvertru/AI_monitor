import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  auditDetailFixture,
  auditEstimateFixture,
  auditSummaryFixture,
  auditTargetWireFixture,
  currentUserFixture,
  modelCatalogWireFixture,
  openRouterL2AuditTargetWireFixture,
} from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";
import { renderRoute } from "../../test/render";

const createAuditResponse = {
  audit_id: 88,
  audit_number: 2,
  brand_id: 12,
  status: "created",
  providers: ["mock", "openai"],
  runs_per_query: 2,
  scdl_level: "L2",
  seed_queries: ["best ai visibility tools", "brand monitoring platforms"],
  seed_query_items: [
    { text: "best ai visibility tools", type: null, source: "user" },
    { text: "brand monitoring platforms", type: null, source: "user" },
  ],
  model_targets: [auditTargetWireFixture, openRouterL2AuditTargetWireFixture],
};

async function openCreatePage() {
  mockFetchSequence([{ body: currentUserFixture }, { body: modelCatalogWireFixture }]);
  renderRoute("/audits/new");
  await screen.findByRole("heading", { name: "Create audit" });
  await screen.findByLabelText("GPT-4o mini");
}

async function selectGptL1() {
  await userEvent.setup().click(await screen.findByLabelText("GPT-4o mini"));
}

async function selectGptL2() {
  const user = userEvent.setup();
  await user.click(await screen.findByLabelText("GPT-4o mini"));
  await user.click(screen.getByLabelText("GPT-4o mini L2"));
}

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

describe("create audit page", () => {
  it("renders the manual audit form", async () => {
    await openCreatePage();

    expect(screen.getByLabelText("Brand name")).toBeInTheDocument();
    expect(screen.getByLabelText("Brand domain")).toBeInTheDocument();
    expect(screen.getByText("Seed queries")).toBeInTheDocument();
    expect(screen.getByLabelText("Seed query 1")).toBeInTheDocument();
    expect(screen.getByLabelText("Query type 1")).toBeInTheDocument();
    expect(screen.getByLabelText("Language")).toBeInTheDocument();
    expect(screen.getByLabelText("Country")).toBeInTheDocument();
    expect(screen.getByText("AI model targets")).toBeInTheDocument();
    expect(screen.getByLabelText("GPT-4o mini")).toBeInTheDocument();
    expect(screen.getByLabelText("Brand description")).toHaveAttribute("maxLength", "500");
    expect(screen.getByText("0 / 500")).toBeInTheDocument();
    expect(screen.queryByLabelText("Locale")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Runs per query")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Follow-up depth")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Source intelligence")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Generate seed queries" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Query expansion/ })).not.toBeInTheDocument();
    expect(screen.getByText(/Estimated audit cost:/)).toHaveTextContent("0 tokens");
    expect(screen.getByRole("button", { name: "Create audit" })).toBeInTheDocument();
  });

  it("validates required brand name before API submission", async () => {
    await openCreatePage();
    const user = userEvent.setup();

    await user.clear(screen.getByLabelText("Brand name"));
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    expect(await screen.findByText("Enter a brand name.")).toBeInTheDocument();
  });

  it("renders create labels and validation in Russian without translating raw input", async () => {
    await openCreatePage();
    const user = userEvent.setup();

    await user.selectOptions(screen.getByLabelText("Interface language"), "ru");
    expect(await screen.findByRole("heading", { name: "Создать аудит" })).toBeInTheDocument();
    expect(screen.getByLabelText("Название бренда")).toBeInTheDocument();
    await user.type(screen.getByLabelText("Стартовый запрос 1"), "Nike raw query");
    await user.click(screen.getByRole("button", { name: "Создать аудит" }));

    expect(await screen.findByText("Введите название бренда.")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Nike raw query")).toBeInTheDocument();
  });

  it("validates required brand domain before API submission", async () => {
    await openCreatePage();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText("Brand name"), "Acme AI");
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    expect(await screen.findByText("Enter a brand domain.")).toBeInTheDocument();
  });

  it("validates brand domain format before API submission", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: modelCatalogWireFixture },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand name"), "Acme AI");
    await user.type(screen.getByLabelText("Brand domain"), "https://acme.ai/page");
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    expect(await screen.findByText("Invalid domain format")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("shows a live brand description counter and blocks over-limit values", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: modelCatalogWireFixture },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    const description = await screen.findByLabelText("Brand description");
    await user.type(description, "short");
    expect(screen.getByText("5 / 500")).toBeInTheDocument();

    fireEvent.change(description, { target: { value: "x".repeat(501) } });
    await user.type(screen.getByLabelText("Brand name"), "Acme AI");
    await user.type(screen.getByLabelText("Brand domain"), "acme.ai");
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    expect(await screen.findByText("501 / 500")).toBeInTheDocument();
    expect(
      await screen.findByText(/Brand description must be 500 characters or fewer./),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("generates editable seed query rows from current unsaved form values", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: modelCatalogWireFixture },
      {
        body: {
          suggestions: [
            {
              text: "best acme alternatives",
              type: "alternative",
              source: "ai",
            },
          ],
          warnings: ["Duplicate suggestions were skipped."],
        },
      },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand name"), "Acme AI Draft");
    await user.type(screen.getByLabelText("Brand domain"), "acme.example");
    await user.type(screen.getByLabelText("Brand description"), "Draft description.");
    await user.type(screen.getByLabelText("Seed query 1"), "best ai visibility tools");
    await user.click(screen.getByRole("button", { name: "Generate seed queries" }));
    await user.click(screen.getByRole("button", { name: "Generate 10 queries" }));

    await waitFor(() => {
      expect(screen.getByDisplayValue("best acme alternatives")).toBeInTheDocument();
    });
    expect(screen.getByLabelText("Query type 2")).toHaveValue("alternative");
    expect(screen.getByText("Duplicate suggestions were skipped.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/audit-seed-query-suggestions",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          brand_name: "Acme AI Draft",
          brand_domain: "acme.example",
          brand_description: "Draft description.",
          use_domain: true,
          use_description: true,
          use_paa: false,
          language: "en",
          country: "US",
          paa_seed_query: null,
          count: 10,
          existing_queries: [
            {
              text: "best ai visibility tools",
              type: null,
              source: "user",
            },
          ],
        }),
      }),
    );
    expect(fetchMock).not.toHaveBeenCalledWith(
      "http://localhost:8000/audits",
      expect.anything(),
    );
  });

  it("preserves generated query type and source after text edits when saved", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: modelCatalogWireFixture },
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
      { body: createAuditResponse },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand name"), "Acme AI");
    await user.type(screen.getByLabelText("Brand domain"), "acme.example");
    await user.click(screen.getByRole("button", { name: "Generate seed queries" }));
    await user.click(screen.getByRole("button", { name: "Generate 10 queries" }));
    const generatedQuery = await screen.findByDisplayValue("best acme alternatives");
    await user.clear(generatedQuery);
    await user.type(generatedQuery, "edited acme alternatives");
    await user.click(screen.getByLabelText("GPT-4o mini"));
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/audits",
        expect.objectContaining({ method: "POST" }),
      );
    });
    expect(jsonRequestBodyFor(fetchMock, "http://localhost:8000/audits", "POST")).toMatchObject({
      seed_query_items: [
        {
          text: "edited acme alternatives",
          type: "alternative",
          source: "ai",
        },
      ],
    });
  });

  it("generates PAA suggestions, preserves source, and does not save removed rows", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: modelCatalogWireFixture },
      {
        body: {
          suggestions: [
            { text: "manual seed", type: "brand_direct", source: "paa" },
            {
              text: "How does Acme compare with alternatives?",
              type: "alternative",
              source: "paa",
              metadata: { paa_provider: "serpapi", raw_response: "unsafe raw" },
            },
            {
              text: "What is Acme known for?",
              type: "brand_direct",
              source: "paa",
            },
          ],
          warnings: ["People Also Ask enrichment returned fewer results."],
        },
      },
      { body: auditEstimateFixture },
      { body: createAuditResponse },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand name"), "Acme AI");
    await user.type(screen.getByLabelText("Brand domain"), "acme.example");
    await user.type(screen.getByLabelText("Seed query 1"), "manual seed");
    await user.selectOptions(screen.getByLabelText("Language"), "uk");
    await user.selectOptions(screen.getByLabelText("Country"), "UA");
    await user.click(screen.getByRole("button", { name: "Generate seed queries" }));
    expect(screen.getByLabelText("Include People Also Ask questions")).toBeInTheDocument();
    await user.click(screen.getByLabelText("Include People Also Ask questions"));
    await user.click(screen.getByRole("button", { name: "Generate 10 queries" }));

    const paaQuery = await screen.findByDisplayValue(
      "How does Acme compare with alternatives?",
    );
    expect(paaQuery).toBeInTheDocument();
    expect(screen.getAllByText("PAA")).toHaveLength(2);
    expect(
      screen.getByText("People Also Ask enrichment returned fewer results."),
    ).toBeInTheDocument();
    expect(screen.queryByText("unsafe raw")).not.toBeInTheDocument();
    expect(jsonRequestBodyFor(
      fetchMock,
      "http://localhost:8000/audit-seed-query-suggestions",
      "POST",
    )).toMatchObject({
      use_paa: true,
      language: "uk",
      country: "UA",
      paa_seed_query: "manual seed",
      existing_queries: [{ text: "manual seed", type: null, source: "user" }],
    });

    await user.clear(paaQuery);
    await user.type(paaQuery, "edited PAA query");
    await user.click(screen.getByRole("button", { name: "Remove seed query 3" }));
    await user.click(await screen.findByLabelText("GPT-4o mini"));
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/audits",
        expect.objectContaining({ method: "POST" }),
      );
    });
    expect(jsonRequestBodyFor(fetchMock, "http://localhost:8000/audits", "POST"))
      .toMatchObject({
        seed_query_items: [
          { text: "manual seed", type: null, source: "user" },
          { text: "edited PAA query", type: "alternative", source: "paa" },
        ],
      });
  });

  it("requires at least one seed query before creating an audit", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: modelCatalogWireFixture },
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
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand name"), "Acme AI");
    await user.type(screen.getByLabelText("Brand domain"), "acme.example");
    await user.click(screen.getByRole("button", { name: "Generate seed queries" }));
    await user.click(screen.getByRole("button", { name: "Generate 10 queries" }));
    await screen.findByDisplayValue("best acme alternatives");
    await user.click(screen.getByRole("button", { name: "Remove seed query 1" }));
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    expect(await screen.findByText("Add at least one seed query.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("keeps generation disabled when no source is selected or available", async () => {
    await openCreatePage();
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "Generate seed queries" }));

    expect(screen.getByRole("button", { name: "Generate 10 queries" })).toBeDisabled();
    expect(screen.getByLabelText("Use brand domain")).toBeDisabled();
    expect(screen.getByLabelText("Use brand description")).toBeDisabled();
  });

  it("checks brand domain availability and renders reachable status", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: modelCatalogWireFixture },
      {
        body: {
          input: "acme.example",
          normalized_domain: "acme.example",
          status: "reachable",
          http_status: 200,
          checked_at: "2026-01-01T00:00:00Z",
          query_generation_allowed: true,
          reason: null,
          cache_ttl_seconds: 86400,
          raw_html: "<html>unsafe</html>",
        },
      },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand domain"), "acme.example");
    await user.click(screen.getByRole("button", { name: "Check domain" }));

    expect(await screen.findByText("Domain is reachable")).toBeInTheDocument();
    expect(screen.queryByText("<html>unsafe</html>")).not.toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/brand-domain/check",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ domain: "acme.example" }),
      }),
    );
  });

  it("soft-blocks domain generation when domain is unavailable but keeps manual save available", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: modelCatalogWireFixture },
      {
        body: {
          input: "missing.example",
          normalized_domain: "missing.example",
          status: "dns_failed",
          http_status: null,
          checked_at: "2026-01-01T00:00:00Z",
          query_generation_allowed: false,
          reason: "dns_failed",
          cache_ttl_seconds: 86400,
          stack_trace: "unsafe-stack",
        },
      },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand domain"), "missing.example");
    await user.type(screen.getByLabelText("Seed query 1"), "manual query");
    await user.click(screen.getByRole("button", { name: "Check domain" }));
    expect(await screen.findByText("Domain DNS could not be resolved")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Generate seed queries" }));
    expect(screen.getByLabelText("Use brand domain")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Generate 10 queries" })).toBeDisabled();
    expect(screen.getByLabelText("Seed query 1")).toHaveValue("manual query");
    expect(screen.getByRole("button", { name: "Create audit" })).toBeEnabled();
    expect(screen.queryByText("unsafe-stack")).not.toBeInTheDocument();
  });

  it("keeps description generation available when domain check soft-blocks domain generation", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: modelCatalogWireFixture },
      {
        body: {
          input: "missing.example",
          normalized_domain: "missing.example",
          status: "timeout",
          http_status: null,
          checked_at: "2026-01-01T00:00:00Z",
          query_generation_allowed: false,
          reason: "http_timeout",
          cache_ttl_seconds: 86400,
        },
      },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand domain"), "missing.example");
    await user.type(screen.getByLabelText("Brand description"), "Useful description.");
    await user.click(screen.getByRole("button", { name: "Check domain" }));
    expect(await screen.findByText("Domain check timed out")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Generate seed queries" }));
    expect(screen.getByLabelText("Use brand domain")).toBeDisabled();
    expect(screen.getByLabelText("Use brand description")).toBeEnabled();
    expect(screen.getByRole("button", { name: "Generate 10 queries" })).toBeEnabled();
  });

  it("shows safe domain check network errors", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: modelCatalogWireFixture },
      { body: { detail: "stack trace with secret" }, status: 500 },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand domain"), "acme.example");
    await user.click(screen.getByRole("button", { name: "Check domain" }));

    expect(await screen.findByText("Unable to check domain availability.")).toBeInTheDocument();
    expect(screen.queryByText("stack trace with secret")).not.toBeInTheDocument();
  });

  it("lets the user select and clear available generation sources", async () => {
    await openCreatePage();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText("Brand domain"), "acme.example");
    await user.type(screen.getByLabelText("Brand description"), "Draft description.");
    await user.click(screen.getByRole("button", { name: "Generate seed queries" }));

    expect(screen.getByLabelText("Use brand domain")).toBeChecked();
    expect(screen.getByLabelText("Use brand description")).toBeChecked();
    expect(screen.getByRole("button", { name: "Generate 10 queries" })).toBeEnabled();

    await user.click(screen.getByLabelText("Use brand domain"));
    await user.click(screen.getByLabelText("Use brand description"));

    expect(screen.getByRole("button", { name: "Generate 10 queries" })).toBeDisabled();
  });

  it("shows frontend duplicate warnings when visible form state changed defensively", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: modelCatalogWireFixture },
      {
        body: {
          suggestions: [
            {
              text: "Best AI visibility tools",
              type: "category_discovery",
              source: "ai",
            },
          ],
        },
      },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand domain"), "acme.example");
    await user.type(screen.getByLabelText("Seed query 1"), "best ai visibility tools");
    await user.click(screen.getByRole("button", { name: "Generate seed queries" }));
    await user.click(screen.getByRole("button", { name: "Generate 10 queries" }));

    expect(await screen.findByText("1 duplicate queries were skipped.")).toBeInTheDocument();
    expect(screen.getAllByDisplayValue("best ai visibility tools")).toHaveLength(1);
  });

  it("respects the 20 query limit and shows frontend limit warnings", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: modelCatalogWireFixture },
      {
        body: {
          suggestions: [
            { text: "generated query one", type: "recommendation", source: "ai" },
            { text: "generated query two", type: "recommendation", source: "ai" },
          ],
        },
      },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand domain"), "acme.example");
    fireEvent.change(screen.getByLabelText("Seed query 1"), {
      target: { value: "manual query 1" },
    });
    for (let index = 2; index <= 20; index += 1) {
      await user.click(screen.getByRole("button", { name: "Add query" }));
      fireEvent.change(screen.getByLabelText(`Seed query ${index}`), {
        target: { value: `manual query ${index}` },
      });
    }
    await user.click(screen.getByRole("button", { name: "Generate seed queries" }));
    await user.click(screen.getByRole("button", { name: "Generate 10 queries" }));

    expect(
      await screen.findByText(
        "Only 0 queries were added because the audit limit is 20 seed queries.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByDisplayValue("generated query one")).not.toBeInTheDocument();
  });

  it("shows seed query generation loading state", async () => {
    const fetchMock = vi.fn();
    fetchMock.mockResolvedValueOnce({
      json: async () => currentUserFixture,
      ok: true,
      status: 200,
      statusText: "OK",
    } satisfies Partial<Response>);
    fetchMock.mockResolvedValueOnce({
      json: async () => modelCatalogWireFixture,
      ok: true,
      status: 200,
      statusText: "OK",
    } satisfies Partial<Response>);
    fetchMock.mockReturnValueOnce(new Promise(() => undefined));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand domain"), "acme.example");
    await user.click(screen.getByRole("button", { name: "Generate seed queries" }));
    await user.click(screen.getByRole("button", { name: "Generate 10 queries" }));

    expect(screen.getByRole("button", { name: "Generating..." })).toBeDisabled();
  });

  it("shows safe generation errors", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: modelCatalogWireFixture },
      { body: { detail: "Seed query generation is unavailable." }, status: 503 },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand domain"), "acme.example");
    await user.click(screen.getByRole("button", { name: "Generate seed queries" }));
    await user.click(screen.getByRole("button", { name: "Generate 10 queries" }));

    expect(
      await screen.findByText(
        "Could not generate seed queries. Please try again or enter queries manually.",
      ),
    ).toBeInTheDocument();
  });

  it("updates the estimated audit token cost from selected parameters", async () => {
    await openCreatePage();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText("Seed query 1"), "query one");
    await user.click(screen.getByRole("button", { name: "Add query" }));
    await user.type(screen.getByLabelText("Seed query 2"), "query two");
    expect(screen.getByText(/Estimated audit cost:/)).toHaveTextContent("0 tokens");

    await user.click(screen.getByLabelText("GPT-4o mini"));
    expect(screen.getByText(/Estimated audit cost:/)).toHaveTextContent("20 tokens");

    await user.click(screen.getByLabelText("GPT-4o mini L2"));
    expect(screen.getByText(/Estimated audit cost:/)).toHaveTextContent("50 tokens");

    await user.click(screen.getByLabelText("Source intelligence"));
    expect(screen.getByText(/Estimated audit cost:/)).toHaveTextContent("60 tokens");

    await user.type(screen.getByLabelText("Max queries"), "1");
    expect(screen.getByText(/Estimated audit cost:/)).toHaveTextContent("30 tokens");
  });

  it("shows backend estimated run counts for selected queries and targets", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: modelCatalogWireFixture },
      { body: auditEstimateFixture },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Seed query 1"), "query one");
    await user.click(await screen.findByLabelText("GPT-4o mini"));

    expect(await screen.findByText("This audit will run 4 checks.")).toBeInTheDocument();
    const body = jsonRequestBodyFor(fetchMock, "http://localhost:8000/audits/estimate", "POST");
    expect(body).toMatchObject({
      runs_per_query: 1,
      seed_query_items: [{ text: "query one", type: null, source: "user" }],
      model_targets: [
        expect.objectContaining({
          model_id: "openai/gpt-4o-mini",
          level: "L1",
        }),
      ],
    });
    expect(body).not.toHaveProperty("brand_name");
  });

  it("only shows source intelligence for L2 and clears it before L1 submission", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: modelCatalogWireFixture },
      { body: auditEstimateFixture },
      { body: auditEstimateFixture },
      { body: auditEstimateFixture },
      { body: auditEstimateFixture },
      { body: createAuditResponse },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand name"), "Acme AI");
    await user.type(screen.getByLabelText("Brand domain"), "acme.ai");
    await user.type(screen.getByLabelText("Seed query 1"), "best nike shoes");

    expect(screen.queryByLabelText("Source intelligence")).not.toBeInTheDocument();
    await user.click(await screen.findByLabelText("GPT-4o mini"));
    await user.click(screen.getByLabelText("GPT-4o mini L2"));
    await user.click(screen.getByLabelText("Source intelligence"));
    expect(screen.getByLabelText("Source intelligence")).toBeChecked();

    await user.click(screen.getByLabelText("GPT-4o mini L2"));
    expect(screen.queryByLabelText("Source intelligence")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/audits",
        expect.objectContaining({ method: "POST" }),
      );
    });
    const body = jsonRequestBodyFor(fetchMock, "http://localhost:8000/audits", "POST");
    expect(body).toMatchObject({
      enable_source_intelligence: false,
    });
    expect(body).not.toHaveProperty("scdl_level");
  });

  it("submits seed queries, location fields, and hidden defaults in the backend contract format", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: modelCatalogWireFixture },
      { body: auditEstimateFixture },
      { body: createAuditResponse },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand name"), "Acme AI");
    await user.type(screen.getByLabelText("Brand domain"), " Acme.AI/ ");
    await user.selectOptions(screen.getByLabelText("Language"), "uk");
    await user.selectOptions(screen.getByLabelText("Country"), "UA");
    await user.type(screen.getByLabelText("Seed query 1"), " best ai visibility tools ");
    await user.click(screen.getByRole("button", { name: "Add query" }));
    await user.type(screen.getByLabelText("Seed query 2"), "brand monitoring platforms");
    await user.click(screen.getByRole("button", { name: "Add query" }));
    await user.type(screen.getByLabelText("Seed query 3"), "Best AI Visibility Tools ");
    await user.click(await screen.findByLabelText("GPT-4o mini"));
    await user.click(screen.getByLabelText("GPT-4o mini L2"));
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/audits",
        expect.objectContaining({ method: "POST" }),
      );
    });
    const body = jsonRequestBodyFor(fetchMock, "http://localhost:8000/audits", "POST");
    expect(body).toMatchObject({
      brand_name: "Acme AI",
      brand_domain: "acme.ai",
      runs_per_query: 1,
      model_targets: [
        {
          ai_family: "chatgpt",
          execution_provider: "openrouter",
          model_provider: "openai",
          model_id: "openai/gpt-4o-mini",
          display_name: "GPT-4o mini",
          level: "L1",
          gateway: true,
        },
        {
          ai_family: "chatgpt",
          execution_provider: "openrouter",
          model_provider: "openai",
          model_id: "openai/gpt-4o-mini",
          display_name: "GPT-4o mini",
          level: "L2",
          gateway: true,
          gateway_l2_experimental: true,
        },
      ],
      seed_query_items: [
        { text: "best ai visibility tools", type: null, source: "user" },
        { text: "brand monitoring platforms", type: null, source: "user" },
      ],
      language: "uk",
      country: "UA",
      locale: "uk-UA",
      enable_query_expansion: false,
      follow_up_depth: 0,
    });
    expect(body).not.toHaveProperty("seed_queries");
    expect(body).not.toHaveProperty("providers");
    expect(body).not.toHaveProperty("scdl_level");
    expect(body).not.toHaveProperty("modelTargets");
  });

  it("redirects to audit detail after successful creation", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: modelCatalogWireFixture },
      { body: auditEstimateFixture },
      { body: createAuditResponse },
      { body: { ...auditDetailFixture, audit_id: 88 } },
      { body: { ...auditSummaryFixture, audit_id: 88 } },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand name"), "Acme AI");
    await user.type(screen.getByLabelText("Brand domain"), "acme.ai");
    await user.type(screen.getByLabelText("Seed query 1"), "best nike shoes");
    await user.click(await screen.findByLabelText("GPT-4o mini"));
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Acme AI" })).toBeInTheDocument();
    });
    expect(screen.getByText(/Audit #1.*acme\.example/)).toBeInTheDocument();
  });

  it("displays API validation errors", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: modelCatalogWireFixture },
      { body: auditEstimateFixture },
      { body: { detail: "providers contains unsupported provider codes." }, status: 422 },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand name"), "Acme AI");
    await user.type(screen.getByLabelText("Brand domain"), "acme.ai");
    await user.type(screen.getByLabelText("Seed query 1"), "best nike shoes");
    await user.click(await screen.findByLabelText("GPT-4o mini"));
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    expect(
      await screen.findByText("providers contains unsupported provider codes."),
    ).toBeInTheDocument();
  });
});
