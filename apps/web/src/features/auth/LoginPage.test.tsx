import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { auditListFixture, currentUserFixture } from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";
import { renderRoute } from "../../test/render";

describe("login page", () => {
  it("renders login form", async () => {
    mockFetchSequence([{ body: { detail: "Unauthorized" }, status: 401 }]);

    renderRoute("/login");

    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
  });

  it("redirects authenticated users away from login", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: auditListFixture },
    ]);

    renderRoute("/login");

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Audits" })).toBeInTheDocument();
    });
  });

  it("blocks invalid email", async () => {
    mockFetchSequence([{ body: { detail: "Unauthorized" }, status: 401 }]);
    const user = userEvent.setup();

    renderRoute("/login");

    await user.type(await screen.findByLabelText("Email"), "bad-email");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText("Enter a valid email address.")).toBeInTheDocument();
  });

  it("shows login API errors", async () => {
    mockFetchSequence([
      { body: { detail: "Unauthorized" }, status: 401 },
      { body: { detail: "Invalid authentication credentials." }, status: 401 },
    ]);
    const user = userEvent.setup();

    renderRoute("/login");

    await user.type(await screen.findByLabelText("Email"), "user@example.com");
    await user.type(screen.getByLabelText("Password"), "wrong");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(
      await screen.findByText("Invalid authentication credentials."),
    ).toBeInTheDocument();
  });

  it("redirects successful login to audits", async () => {
    mockFetchSequence([
      { body: { detail: "Unauthorized" }, status: 401 },
      { body: currentUserFixture },
      { body: [] },
    ]);
    const user = userEvent.setup();

    renderRoute("/login");

    await user.type(await screen.findByLabelText("Email"), "user@example.com");
    await user.type(screen.getByLabelText("Password"), "secret");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Audits" })).toBeInTheDocument();
    });
  });
});
