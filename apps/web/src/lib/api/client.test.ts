import { describe, expect, it, vi } from "vitest";

import { ApiError, getAuditDetail, getCurrentUser, loginUser, listAudits } from "./client";
import { auditListFixture, currentUserFixture } from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";

describe("api client", () => {
  it("loads the current user with credentialed requests", async () => {
    const fetchMock = mockFetchSequence([{ body: currentUserFixture }]);

    await expect(getCurrentUser()).resolves.toEqual(currentUserFixture);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/auth/me",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("parses API errors into a predictable shape", async () => {
    mockFetchSequence([
      { body: { detail: "Invalid authentication credentials." }, status: 401 },
    ]);

    await expect(loginUser({ email: "user@example.com", password: "bad" })).rejects.toMatchObject({
      message: "Invalid authentication credentials.",
      status: 401,
    } satisfies Partial<ApiError>);
  });

  it("loads audit list responses", async () => {
    mockFetchSequence([{ body: auditListFixture }]);

    await expect(listAudits()).resolves.toEqual(auditListFixture);
  });

  it("loads audit detail responses", async () => {
    const detail = {
      ...auditListFixture[0],
      brand_id: 7,
      brand_description: null,
      language: null,
      country: null,
      locale: null,
      max_queries: null,
      seed_queries: ["best ai visibility monitor"],
      enable_query_expansion: false,
      enable_source_intelligence: false,
      follow_up_depth: 0,
    };
    mockFetchSequence([{ body: detail }]);

    await expect(getAuditDetail(42)).resolves.toEqual(detail);
  });

  it("does not use browser token storage during credentialed API calls", async () => {
    const storageSpy = vi.spyOn(Storage.prototype, "setItem");
    mockFetchSequence([{ body: currentUserFixture }]);

    await expect(getCurrentUser()).resolves.toEqual(currentUserFixture);

    expect(storageSpy).not.toHaveBeenCalled();

    storageSpy.mockRestore();
  });
});
