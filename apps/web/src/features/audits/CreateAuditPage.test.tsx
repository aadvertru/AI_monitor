import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  auditDetailFixture,
  auditSummaryFixture,
  currentUserFixture,
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
};

async function openCreatePage() {
  mockFetchSequence([{ body: currentUserFixture }]);
  renderRoute("/audits/new");
  await screen.findByRole("heading", { name: "Create audit" });
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
    expect(screen.getByLabelText("SCDL level")).toBeInTheDocument();
    expect(screen.getByLabelText("Brand description")).toHaveAttribute("maxLength", "500");
    expect(screen.getByText("0 / 500")).toBeInTheDocument();
    expect(screen.queryByLabelText("Locale")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Runs per query")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Follow-up depth")).not.toBeInTheDocument();
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

  it("validates required brand domain before API submission", async () => {
    await openCreatePage();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText("Brand name"), "Acme AI");
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    expect(await screen.findByText("Enter a brand domain.")).toBeInTheDocument();
  });

  it("validates brand domain format before API submission", async () => {
    const fetchMock = mockFetchSequence([{ body: currentUserFixture }]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand name"), "Acme AI");
    await user.type(screen.getByLabelText("Brand domain"), "https://acme.ai/page");
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    expect(await screen.findByText("Invalid domain format")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("shows a live brand description counter and blocks over-limit values", async () => {
    const fetchMock = mockFetchSequence([{ body: currentUserFixture }]);
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
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("generates editable seed query rows from current unsaved form values", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
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
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/audits",
        expect.objectContaining({ method: "POST" }),
      );
    });
    const [, , request] = fetchMock.mock.calls;
    expect(JSON.parse(String(request?.[1]?.body))).toMatchObject({
      seed_query_items: [
        {
          text: "edited acme alternatives",
          type: "alternative",
          source: "ai",
        },
      ],
    });
  });

  it("requires at least one seed query before creating an audit", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
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
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("keeps generation disabled when no source is selected or available", async () => {
    await openCreatePage();
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "Generate seed queries" }));

    expect(screen.getByRole("button", { name: "Generate 10 queries" })).toBeDisabled();
    expect(screen.getByLabelText("Use brand domain")).toBeDisabled();
    expect(screen.getByLabelText("Use brand description")).toBeDisabled();
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
    expect(screen.getByText(/Estimated audit cost:/)).toHaveTextContent("20 tokens");

    await user.click(screen.getByLabelText("OpenAI"));
    expect(screen.getByText(/Estimated audit cost:/)).toHaveTextContent("40 tokens");

    await user.selectOptions(screen.getByLabelText("SCDL level"), "L2");
    expect(screen.getByText(/Estimated audit cost:/)).toHaveTextContent("60 tokens");

    await user.click(screen.getByLabelText("Source intelligence"));
    expect(screen.getByText(/Estimated audit cost:/)).toHaveTextContent("80 tokens");

    await user.type(screen.getByLabelText("Max queries"), "1");
    expect(screen.getByText(/Estimated audit cost:/)).toHaveTextContent("40 tokens");
  });

  it("submits seed queries, location fields, and hidden defaults in the backend contract format", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: createAuditResponse },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand name"), "Acme AI");
    await user.type(screen.getByLabelText("Brand domain"), " Acme.AI/ ");
    await user.click(screen.getByLabelText("OpenAI"));
    await user.selectOptions(screen.getByLabelText("Language"), "uk");
    await user.selectOptions(screen.getByLabelText("Country"), "UA");
    await user.selectOptions(screen.getByLabelText("SCDL level"), "L2");
    await user.type(screen.getByLabelText("Seed query 1"), " best ai visibility tools ");
    await user.click(screen.getByRole("button", { name: "Add query" }));
    await user.type(screen.getByLabelText("Seed query 2"), "brand monitoring platforms");
    await user.click(screen.getByRole("button", { name: "Add query" }));
    await user.type(screen.getByLabelText("Seed query 3"), "Best AI Visibility Tools ");
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/audits",
        expect.objectContaining({ method: "POST" }),
      );
    });
    const [, request] = fetchMock.mock.calls[1];
    expect(JSON.parse(String(request?.body))).toMatchObject({
      brand_name: "Acme AI",
      brand_domain: "acme.ai",
      providers: ["mock", "openai"],
      runs_per_query: 1,
      seed_query_items: [
        { text: "best ai visibility tools", type: null, source: "user" },
        { text: "brand monitoring platforms", type: null, source: "user" },
      ],
      language: "uk",
      country: "UA",
      locale: "uk-UA",
      enable_query_expansion: false,
      follow_up_depth: 0,
      scdl_level: "L2",
    });
    expect(JSON.parse(String(request?.body))).not.toHaveProperty("seed_queries");
  });

  it("redirects to audit detail after successful creation", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: createAuditResponse },
      { body: { ...auditDetailFixture, audit_id: 88 } },
      { body: { ...auditSummaryFixture, audit_id: 88 } },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand name"), "Acme AI");
    await user.type(screen.getByLabelText("Brand domain"), "acme.ai");
    await user.type(screen.getByLabelText("Seed query 1"), "best nike shoes");
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Acme AI" })).toBeInTheDocument();
    });
    expect(screen.getByText(/Audit #1.*acme\.example/)).toBeInTheDocument();
  });

  it("displays API validation errors", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: { detail: "providers contains unsupported provider codes." }, status: 422 },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand name"), "Acme AI");
    await user.type(screen.getByLabelText("Brand domain"), "acme.ai");
    await user.type(screen.getByLabelText("Seed query 1"), "best nike shoes");
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    expect(
      await screen.findByText("providers contains unsupported provider codes."),
    ).toBeInTheDocument();
  });
});
