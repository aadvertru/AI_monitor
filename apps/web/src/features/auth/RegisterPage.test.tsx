import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { auditListFixture, currentUserFixture } from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";
import { renderRoute } from "../../test/render";

describe("register page", () => {
  it("renders registration form", async () => {
    mockFetchSequence([{ body: { detail: "Unauthorized" }, status: 401 }]);

    renderRoute("/register");

    expect(
      await screen.findByRole("heading", { name: "Create account" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByLabelText("Confirm password")).toBeInTheDocument();
  });

  it("redirects authenticated users away from register", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: auditListFixture },
    ]);

    renderRoute("/register");

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Audits" })).toBeInTheDocument();
    });
  });

  it("blocks missing required fields", async () => {
    mockFetchSequence([{ body: { detail: "Unauthorized" }, status: 401 }]);
    const user = userEvent.setup();

    renderRoute("/register");

    await user.click(await screen.findByRole("button", { name: "Create account" }));

    expect(await screen.findByText("Enter a valid email address.")).toBeInTheDocument();
    expect(screen.getByText("Enter a password.")).toBeInTheDocument();
  });

  it("shows register API errors", async () => {
    mockFetchSequence([
      { body: { detail: "Unauthorized" }, status: 401 },
      { body: { detail: "Email is already registered." }, status: 409 },
    ]);
    const user = userEvent.setup();

    renderRoute("/register");

    await user.type(await screen.findByLabelText("Email"), "user@example.com");
    await user.type(screen.getByLabelText("Password"), "secret");
    await user.type(screen.getByLabelText("Confirm password"), "secret");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    expect(await screen.findByText("Email is already registered.")).toBeInTheDocument();
  });

  it("redirects successful register to login", async () => {
    mockFetchSequence([
      { body: { detail: "Unauthorized" }, status: 401 },
      { body: currentUserFixture },
    ]);
    const user = userEvent.setup();

    renderRoute("/register");

    await user.type(await screen.findByLabelText("Email"), "new@example.com");
    await user.type(screen.getByLabelText("Password"), "secret");
    await user.type(screen.getByLabelText("Confirm password"), "secret");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    });
    expect(screen.getByText("Account created. Sign in to continue.")).toBeInTheDocument();
  });
});
