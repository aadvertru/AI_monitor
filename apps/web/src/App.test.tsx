import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { renderRoute } from "./test/render";
import { auditListFixture, currentUserFixture } from "./test/fixtures";
import { mockFetchSequence } from "./test/mockFetch";

describe("app shell", () => {
  it("renders the protected audits route when a session exists", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: auditListFixture },
    ]);

    renderRoute("/audits");

    expect(await screen.findByRole("heading", { name: "Audits" })).toBeInTheDocument();
    expect(await screen.findByText("Acme AI")).toBeInTheDocument();
  });

  it("redirects an unauthenticated visitor to login", async () => {
    mockFetchSequence([{ body: { detail: "Unauthorized" }, status: 401 }]);

    renderRoute("/audits");

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    });
  });

  it("logs out from the protected shell and returns to login", async () => {
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: auditListFixture },
      { body: { status: "logged_out" } },
    ]);
    const user = userEvent.setup();

    renderRoute("/audits");

    await screen.findByRole("heading", { name: "Audits" });
    await user.click(screen.getByRole("button", { name: "Sign out" }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/auth/logout",
      expect.objectContaining({ method: "POST", credentials: "include" }),
    );
  });
});
