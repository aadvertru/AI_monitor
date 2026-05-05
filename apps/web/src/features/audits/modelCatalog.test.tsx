import { QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import { modelCatalogQueryKey, useModelCatalog } from "./modelCatalog";
import { modelCatalogWireFixture, warningModelCatalogWireFixture } from "../../test/fixtures";
import { mockFetchSequence } from "../../test/mockFetch";
import { createTestQueryClient } from "../../test/render";

function wrapper(children: ReactNode) {
  const queryClient = createTestQueryClient();
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

describe("model catalog query hook", () => {
  it("exposes loading and success states", async () => {
    mockFetchSequence([{ body: modelCatalogWireFixture }]);

    const { result } = renderHook(() => useModelCatalog(), {
      wrapper: ({ children }) => wrapper(children),
    });

    expect(result.current.isLoading || result.current.isPending).toBe(true);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.families[0]?.id).toBe("chatgpt");
  });

  it("exposes catalog API errors", async () => {
    mockFetchSequence([{ body: { detail: "Catalog unavailable." }, status: 503 }]);

    const { result } = renderHook(() => useModelCatalog(), {
      wrapper: ({ children }) => wrapper(children),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });

  it("preserves catalog warning metadata", async () => {
    mockFetchSequence([{ body: warningModelCatalogWireFixture }]);

    const { result } = renderHook(() => useModelCatalog(), {
      wrapper: ({ children }) => wrapper(children),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.warnings).toEqual(["OpenRouter catalog refresh failed."]);
    expect(result.current.data?.cachedAt).toBe("2026-05-05T00:00:00Z");
  });

  it("uses a stable query key", () => {
    expect(modelCatalogQueryKey).toEqual(["model-catalog"]);
  });
});
