import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { RouterProvider } from "react-router-dom";

import { createTestRouter } from "../app/router";

export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        refetchOnWindowFocus: false,
      },
    },
  });
}

export function renderWithClient(ui: ReactElement) {
  return render(
    <QueryClientProvider client={createTestQueryClient()}>{ui}</QueryClientProvider>,
  );
}

export function renderRoute(initialPath: string) {
  return renderWithClient(<RouterProvider router={createTestRouter([initialPath])} />);
}
