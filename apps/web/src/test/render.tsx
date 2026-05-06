import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { I18nextProvider } from "react-i18next";
import { RouterProvider } from "react-router-dom";

import { createTestRouter } from "../app/router";
import { appI18n } from "../lib/i18n/config";

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
    <I18nextProvider i18n={appI18n}>
      <QueryClientProvider client={createTestQueryClient()}>{ui}</QueryClientProvider>
    </I18nextProvider>,
  );
}

export function renderRoute(initialPath: string) {
  return renderWithClient(<RouterProvider router={createTestRouter([initialPath])} />);
}
