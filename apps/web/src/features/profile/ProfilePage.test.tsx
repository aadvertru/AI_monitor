import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { currentUserFixture, profileFixture } from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";
import { renderRoute } from "../../test/render";

describe("ProfilePage", () => {
  it("is protected from unauthenticated visitors", async () => {
    mockFetchSequence([{ body: { detail: "Unauthorized" }, status: 401 }]);

    renderRoute("/profile");

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    });
  });

  it("renders authenticated profile identity, demo plan, usage, and notifications", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: profileFixture },
    ]);

    renderRoute("/profile");

    expect(await screen.findByRole("heading", { name: "Profile" })).toBeInTheDocument();
    expect(screen.getAllByText("user@example.com").length).toBeGreaterThan(0);
    expect(screen.getByText("Starter")).toBeInTheDocument();
    expect(screen.getByText("Demo usage data")).toBeInTheDocument();
    expect(screen.getByText("7,500")).toBeInTheDocument();
    expect(screen.getByText("10,000")).toBeInTheDocument();
    expect(screen.getByText("Actual provider usage")).toBeInTheDocument();
    expect(screen.getByText("1,234")).toBeInTheDocument();
    expect(screen.getByText("Audits with usage")).toBeInTheDocument();
    expect(screen.getByText("Runs with usage")).toBeInTheDocument();
    expect(screen.getByText("Email notifications")).toBeInTheDocument();
    expect(screen.getByText("Audit completed notifications")).toBeInTheDocument();
    expect(screen.getByText("Provider error notifications")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Profile" })).toBeInTheDocument();
  });

  it("renders a loading state while profile data loads", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        json: async () => currentUserFixture,
        ok: true,
        status: 200,
        statusText: "OK",
      } satisfies Partial<Response>)
      .mockReturnValueOnce(new Promise(() => undefined));
    vi.stubGlobal("fetch", fetchMock);

    renderRoute("/profile");

    expect(await screen.findByRole("status")).toHaveTextContent("Loading profile...");
  });

  it("renders a safe error state when the profile request fails", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: { detail: "Profile failed" }, status: 500 },
    ]);

    renderRoute("/profile");

    expect(await screen.findByText("Unable to load profile.")).toBeInTheDocument();
  });

  it("handles missing optional display name and reset date safely", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      {
        body: {
          ...profileFixture,
          user: { ...profileFixture.user, display_name: null },
          usage: { ...profileFixture.usage, reset_at: null },
        },
      },
    ]);

    renderRoute("/profile");

    expect(await screen.findByText("Not set")).toBeInTheDocument();
    expect(screen.getByText("No reset scheduled")).toBeInTheDocument();
  });

  it("does not render unsafe extra fields from the profile response", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      {
        body: {
          ...profileFixture,
          password: "unsafe-password",
          hashed_password: "unsafe-hash",
          jwt: "unsafe-jwt",
          secret: "unsafe-secret",
          api_key: "unsafe-key",
          OPENAI_API_KEY: "unsafe-openai-key",
          OPENROUTER_API_KEY: "unsafe-openrouter-key",
          usage: {
            ...profileFixture.usage,
            actual_usage: {
              ...profileFixture.usage.actual_usage,
              raw_prompt: "unsafe-prompt",
              authorization: "unsafe-auth",
              api_key: "unsafe-api-key",
            },
          },
        },
      },
    ]);

    renderRoute("/profile");

    expect(await screen.findByRole("heading", { name: "Profile" })).toBeInTheDocument();
    for (const unsafeValue of [
      "unsafe-password",
      "unsafe-hash",
      "unsafe-jwt",
      "unsafe-secret",
      "unsafe-key",
      "unsafe-openai-key",
      "unsafe-openrouter-key",
      "unsafe-prompt",
      "unsafe-auth",
      "unsafe-api-key",
    ]) {
      expect(screen.queryByText(unsafeValue)).not.toBeInTheDocument();
    }
  });

  it("saves preferences-only payload", async () => {
    const updatedProfile = {
      ...profileFixture,
      preferences: {
        ...profileFixture.preferences,
        email_notifications: false,
        provider_error_notifications: true,
        locale: "ru" as const,
      },
    };
    const fetchMock = mockFetchSequence([
      { body: currentUserFixture },
      { body: profileFixture },
      { body: updatedProfile },
    ]);
    const user = userEvent.setup();

    renderRoute("/profile");

    await screen.findByRole("heading", { name: "Profile" });
    await user.click(screen.getByRole("checkbox", { name: /Email notifications/ }));
    await user.click(
      screen.getByRole("checkbox", { name: /Provider error notifications/ }),
    );
    await user.selectOptions(screen.getByLabelText("Language preference"), "ru");
    await user.click(screen.getByRole("button", { name: "Save preferences" }));

    await screen.findByText("Настройки сохранены.");
    const request = fetchMock.mock.calls[2]?.[1] as RequestInit | undefined;
    const body = JSON.parse(String(request?.body));
    expect(fetchMock.mock.calls[2]?.[0]).toBe("http://localhost:8000/profile/preferences");
    expect(request).toMatchObject({ method: "PUT", credentials: "include" });
    expect(body).toEqual({
      locale: "ru",
      email_notifications: false,
      audit_completed_notifications: true,
      provider_error_notifications: true,
    });
    expect(body).not.toHaveProperty("email");
    expect(body).not.toHaveProperty("display_name");
    expect(body).not.toHaveProperty("plan");
    expect(body).not.toHaveProperty("tokens_remaining");
    expect(body).not.toHaveProperty("tokens_total");
    expect(window.localStorage.getItem("ai-monitor.locale")).toBe("ru");
  });

  it("cancels unsaved preference changes", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: profileFixture },
    ]);
    const user = userEvent.setup();

    renderRoute("/profile");

    await screen.findByRole("heading", { name: "Profile" });
    const emailToggle = screen.getByRole("checkbox", { name: /Email notifications/ });
    await user.click(emailToggle);
    expect(emailToggle).not.toBeChecked();

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(emailToggle).toBeChecked();
    expect(screen.getByRole("button", { name: "Save preferences" })).toBeDisabled();
  });

  it("shows loading and safe error states while saving preferences", async () => {
    let rejectSave: ((value: Response) => void) | undefined;
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        json: async () => currentUserFixture,
        ok: true,
        status: 200,
        statusText: "OK",
      } satisfies Partial<Response>)
      .mockResolvedValueOnce({
        json: async () => profileFixture,
        ok: true,
        status: 200,
        statusText: "OK",
      } satisfies Partial<Response>)
      .mockReturnValueOnce(
        new Promise((resolve) => {
          rejectSave = resolve;
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    renderRoute("/profile");

    await screen.findByRole("heading", { name: "Profile" });
    await user.click(screen.getByRole("checkbox", { name: /Provider error notifications/ }));
    await user.click(screen.getByRole("button", { name: "Save preferences" }));

    expect(screen.getByRole("button", { name: "Saving..." })).toBeDisabled();

    rejectSave?.({
      json: async () => ({ detail: "Failed" }),
      ok: false,
      status: 500,
      statusText: "Server Error",
    } as Response);

    expect(await screen.findByText("Unable to save preferences.")).toBeInTheDocument();
  });

  it("keeps identity and billing fields non-editable", async () => {
    mockFetchSequence([
      { body: currentUserFixture },
      { body: profileFixture },
    ]);

    renderRoute("/profile");

    await screen.findByRole("heading", { name: "Profile" });
    expect(screen.queryByRole("textbox", { name: /Email/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("textbox", { name: /Display name/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("textbox", { name: /Current plan/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("spinbutton", { name: /Tokens remaining/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("spinbutton", { name: /Token quota/ })).not.toBeInTheDocument();
  });
});
