import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import {
  auditDetailFixture,
  auditStatusFixture,
  currentUserFixture,
} from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";
import { renderRoute } from "../../test/render";

const createAuditResponse = {
  audit_id: 88,
  brand_id: 12,
  status: "created",
  providers: ["mock", "openai"],
  runs_per_query: 2,
  scdl_level: "L2",
  seed_queries: ["best ai visibility tools", "brand monitoring platforms"],
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
    expect(screen.getByLabelText("Seed queries")).toBeInTheDocument();
    expect(screen.getByLabelText("SCDL level")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create audit" })).toBeInTheDocument();
  });

  it("validates required brand name before API submission", async () => {
    await openCreatePage();
    const user = userEvent.setup();

    await user.clear(screen.getByLabelText("Brand name"));
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    expect(await screen.findByText("Enter a brand name.")).toBeInTheDocument();
  });

  it("blocks invalid runs-per-query values before API submission", async () => {
    await openCreatePage();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText("Brand name"), "Acme AI");
    await user.clear(screen.getByLabelText("Runs per query"));
    await user.type(screen.getByLabelText("Runs per query"), "6");
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    expect(await screen.findByText("Runs per query cannot exceed 5.")).toBeInTheDocument();
  });

  it("submits seed queries and SCDL level in the backend contract format", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: createAuditResponse },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand name"), "Acme AI");
    await user.type(screen.getByLabelText("Brand domain"), " acme.ai ");
    await user.clear(screen.getByLabelText("Runs per query"));
    await user.type(screen.getByLabelText("Runs per query"), "2");
    await user.click(screen.getByLabelText("OpenAI"));
    await user.selectOptions(screen.getByLabelText("SCDL level"), "L2");
    await user.type(
      screen.getByLabelText("Seed queries"),
      " best ai visibility tools\n\nbrand monitoring platforms\nBest AI Visibility Tools ",
    );
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
      runs_per_query: 2,
      seed_queries: ["best ai visibility tools", "brand monitoring platforms"],
      scdl_level: "L2",
    });
  });

  it("redirects to audit detail after successful creation", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: createAuditResponse },
      { body: { ...auditDetailFixture, audit_id: 88 } },
      { body: { ...auditStatusFixture, audit_id: 88 } },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand name"), "Acme AI");
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Acme AI" })).toBeInTheDocument();
    });
    expect(screen.getByText("Audit #88 · acme.example")).toBeInTheDocument();
  });

  it("displays API validation errors", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: { detail: "providers contains unsupported provider codes." }, status: 422 },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/new");
    await user.type(await screen.findByLabelText("Brand name"), "Acme AI");
    await user.click(screen.getByRole("button", { name: "Create audit" }));

    expect(
      await screen.findByText("providers contains unsupported provider codes."),
    ).toBeInTheDocument();
  });
});
