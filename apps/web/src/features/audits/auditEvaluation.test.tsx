import { QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import {
  auditAnswerMatrixQueryKey,
  auditDetailQueryKey,
  auditStatusQueryKey,
  auditSummaryV2QueryKey,
  safeRerunEvaluationErrorMessage,
  useRerunAuditEvaluation,
} from "./auditEvaluation";
import { rerunEvaluationFixture } from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";
import { createTestQueryClient } from "../../test/render";

function wrapper(children: ReactNode, queryClient = createTestQueryClient()) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

describe("useRerunAuditEvaluation", () => {
  it("exposes loading state while the rerun request is pending", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(() => new Promise(() => undefined));

    const { result } = renderHook(() => useRerunAuditEvaluation(42), {
      wrapper: ({ children }) => wrapper(children),
    });

    act(() => {
      result.current.mutate();
    });

    await waitFor(() => expect(result.current.isPending).toBe(true));
    fetchSpy.mockRestore();
  });

  it("invalidates summary, matrix, status, and detail queries on success", async () => {
    mockFetchSequence([{ body: rerunEvaluationFixture }]);
    const queryClient = createTestQueryClient();
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    const { result } = renderHook(() => useRerunAuditEvaluation(42), {
      wrapper: ({ children }) => wrapper(children, queryClient),
    });

    let response: { warnings?: string[] } | undefined;
    await act(async () => {
      response = await result.current.mutateAsync();
    });

    expect(response?.warnings).toEqual(rerunEvaluationFixture.warnings);
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: auditSummaryV2QueryKey(42) });
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: auditAnswerMatrixQueryKey(42) });
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: auditStatusQueryKey(42) });
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: auditDetailQueryKey(42) });
  });

  it("exposes a safe static error message", async () => {
    mockFetchSequence([
      {
        body: { detail: "raw evaluator stack trace with secret" },
        status: 500,
      },
    ]);

    const { result } = renderHook(() => useRerunAuditEvaluation(42), {
      wrapper: ({ children }) => wrapper(children),
    });

    await act(async () => {
      await expect(result.current.mutateAsync()).rejects.toThrow();
    });

    await waitFor(() =>
      expect(result.current.safeErrorMessage).toBe(safeRerunEvaluationErrorMessage),
    );
    expect(result.current.safeErrorMessage).not.toContain("secret");
    expect(result.current.safeErrorMessage).not.toContain("stack trace");
  });
});
