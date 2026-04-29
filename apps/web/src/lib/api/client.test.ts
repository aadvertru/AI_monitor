import { describe, expect, it, vi } from "vitest";

import {
  ApiError,
  getAuditDetail,
  getAuditResults,
  getAuditSummary,
  getCurrentUser,
  loginUser,
  listAudits,
} from "./client";
import {
  auditDetailFixture,
  auditListFixture,
  auditResultsFixture,
  auditSummaryFixture,
  currentUserFixture,
  unauthenticatedAuthErrorFixture,
} from "../../test/fixtures";
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
    mockFetchSequence([{ body: unauthenticatedAuthErrorFixture, status: 401 }]);
    const expectedMessage =
      typeof unauthenticatedAuthErrorFixture.detail === "string"
        ? unauthenticatedAuthErrorFixture.detail
        : "Request failed.";

    await expect(loginUser({ email: "user@example.com", password: "bad" })).rejects.toMatchObject({
      message: expectedMessage,
      status: 401,
    } satisfies Partial<ApiError>);
  });

  it("loads audit list responses", async () => {
    mockFetchSequence([{ body: auditListFixture }]);

    await expect(listAudits()).resolves.toEqual(auditListFixture);
  });

  it("loads audit detail responses", async () => {
    mockFetchSequence([{ body: auditDetailFixture }]);

    await expect(getAuditDetail(42)).resolves.toEqual(auditDetailFixture);
  });

  it("loads audit results responses", async () => {
    mockFetchSequence([{ body: auditResultsFixture }]);

    await expect(getAuditResults(42)).resolves.toEqual(auditResultsFixture);
  });

  it("loads audit summary responses", async () => {
    mockFetchSequence([{ body: auditSummaryFixture }]);

    await expect(getAuditSummary(42)).resolves.toEqual(auditSummaryFixture);
  });

  it("does not use browser token storage during credentialed API calls", async () => {
    const storageSpy = vi.spyOn(Storage.prototype, "setItem");
    mockFetchSequence([{ body: currentUserFixture }]);

    await expect(getCurrentUser()).resolves.toEqual(currentUserFixture);

    expect(storageSpy).not.toHaveBeenCalled();

    storageSpy.mockRestore();
  });
});
