import { QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import {
  currentUserQueryKey,
  useCurrentUser,
  useLoginMutation,
  useLogoutMutation,
} from "./session";
import { currentUserFixture } from "../../test/fixtures";
import { createTestQueryClient } from "../../test/render";
import { mockFetchSequence } from "../../test/mockFetch";

function wrapper(children: ReactNode) {
  const queryClient = createTestQueryClient();
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

describe("auth session primitives", () => {
  it("loads current user success state", async () => {
    mockFetchSequence([{ body: currentUserFixture }]);

    const { result } = renderHook(() => useCurrentUser(), {
      wrapper: ({ children }) => wrapper(children),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(currentUserFixture);
  });

  it("exposes current user unauthenticated state", async () => {
    mockFetchSequence([{ body: { detail: "Unauthorized" }, status: 401 }]);

    const { result } = renderHook(() => useCurrentUser(), {
      wrapper: ({ children }) => wrapper(children),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });

  it("login updates current-user cache", async () => {
    const queryClient = createTestQueryClient();
    mockFetchSequence([{ body: currentUserFixture }]);

    const { result } = renderHook(() => useLoginMutation(), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      ),
    });

    result.current.mutate({ email: "user@example.com", password: "secret" });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(queryClient.getQueryData(currentUserQueryKey)).toEqual(currentUserFixture);
  });

  it("logout clears current-user cache", async () => {
    const queryClient = createTestQueryClient();
    queryClient.setQueryData(currentUserQueryKey, currentUserFixture);
    mockFetchSequence([{ body: { status: "logged_out" } }]);

    const { result } = renderHook(() => useLogoutMutation(), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      ),
    });

    result.current.mutate();

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(queryClient.getQueryData(currentUserQueryKey)).toBeNull();
  });
});
