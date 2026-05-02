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
    };
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: auditDetailFixture },
      { body: updatedAudit },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits/42/edit");

    expect(await screen.findByRole("heading", { name: "Edit audit setup" })).toBeInTheDocument();
    await user.clear(screen.getByLabelText("Brand name"));
    await user.type(screen.getByLabelText("Brand name"), "Acme Updated");
    await user.clear(screen.getByLabelText("Brand domain"));
    await user.type(screen.getByLabelText("Brand domain"), "updated.example");
    await user.click(screen.getByLabelText("OpenAI"));
    await user.clear(screen.getByLabelText("Seed queries"));
    await user.type(screen.getByLabelText("Seed queries"), "updated query");
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
      seed_queries: ["updated query"],
    });
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
