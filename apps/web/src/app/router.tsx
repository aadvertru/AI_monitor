import { Navigate, createBrowserRouter, createMemoryRouter } from "react-router-dom";

import { AppShell } from "../components/layout/AppShell";
import { AuditsDashboardPage } from "../features/audits/AuditsDashboardPage";
import { GuestRoute, ProtectedRoute } from "../features/auth/routeGuards";
import { LoginPage } from "../features/auth/LoginPage";
import { RegisterPage } from "../features/auth/RegisterPage";

export function routes() {
  return [
    {
      path: "/",
      element: <Navigate to="/audits" replace />,
    },
    {
      element: <GuestRoute />,
      children: [
        { path: "/login", element: <LoginPage /> },
        { path: "/register", element: <RegisterPage /> },
      ],
    },
    {
      element: <ProtectedRoute />,
      children: [
        {
          element: <AppShell />,
          children: [
            { path: "/audits", element: <AuditsDashboardPage /> },
            {
              path: "/audits/:auditId",
              element: <AuditsDashboardPage />,
            },
          ],
        },
      ],
    },
    {
      path: "*",
      element: <Navigate to="/audits" replace />,
    },
  ];
}

export function createAppRouter() {
  return createBrowserRouter(routes());
}

export function createTestRouter(initialEntries: string[]) {
  return createMemoryRouter(routes(), { initialEntries });
}
