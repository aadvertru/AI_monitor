import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useCurrentUser } from "./session";

export function ProtectedRoute() {
  const location = useLocation();
  const { data: user, isError, isLoading } = useCurrentUser();

  if (isLoading) {
    return <div className="p-6 text-sm text-subtle">Loading session...</div>;
  }

  if (isError || !user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}

export function GuestRoute() {
  const { data: user, isLoading } = useCurrentUser();

  if (isLoading) {
    return <div className="p-6 text-sm text-subtle">Loading session...</div>;
  }

  if (user) {
    return <Navigate to="/audits" replace />;
  }

  return <Outlet />;
}
