import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { I18nextProvider } from "react-i18next";
import { RouterProvider } from "react-router-dom";

import { createAppRouter } from "./app/router";
import { appI18n } from "./lib/i18n/config";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
});

export function App() {
  return (
    <I18nextProvider i18n={appI18n}>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={createAppRouter()} />
      </QueryClientProvider>
    </I18nextProvider>
  );
}
