import { Navigate, createBrowserRouter, createMemoryRouter } from "react-router-dom";

import { AppShell } from "../components/layout/AppShell";
import { AuditDetailPage } from "../features/audits/AuditDetailPage";
import { AuditResultsPage } from "../features/audits/AuditResultsPage";
import { AuditSourcesPage } from "../features/audits/AuditSourcesPage";
import { AuditSummaryPage } from "../features/audits/AuditSummaryPage";
import { AuditsDashboardPage } from "../features/audits/AuditsDashboardPage";
import { CreateAuditPage } from "../features/audits/CreateAuditPage";
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
            { path: "/audits/new", element: <CreateAuditPage /> },
            { path: "/audits/:auditId/summary", element: <AuditSummaryPage /> },
            { path: "/audits/:auditId/results", element: <AuditResultsPage /> },
            { path: "/audits/:auditId/sources", element: <AuditSourcesPage /> },
            {
              path: "/audits/:auditId",
              element: <AuditDetailPage />,
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
