import { BarChart3, LogOut, ShieldCheck } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

import { Button } from "../ui/Button";
import { useCurrentUser, useLogoutMutation } from "../../features/auth/session";

export function AppShell() {
  const { data: user } = useCurrentUser();
  const logout = useLogoutMutation();

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-md bg-brand-600 text-white">
              <ShieldCheck className="size-5" aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-semibold leading-5 text-ink">
                AI Brand Visibility Monitor
              </p>
              <p className="text-xs text-subtle">{user?.email}</p>
            </div>
          </div>
          <Button
            type="button"
            variant="ghost"
            onClick={() => logout.mutate()}
            disabled={logout.isPending}
          >
            <LogOut className="size-4" aria-hidden="true" />
            Sign out
          </Button>
        </div>
      </header>
      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[220px_1fr] lg:px-8">
        <aside className="rounded-md border border-border bg-surface p-2 shadow-panel">
          <nav aria-label="Primary">
            <NavLink
              to="/audits"
              className={({ isActive }) =>
                [
                  "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium",
                  isActive
                    ? "bg-brand-50 text-brand-700"
                    : "text-subtle hover:bg-muted hover:text-ink",
                ].join(" ")
              }
            >
              <BarChart3 className="size-4" aria-hidden="true" />
              Audits
            </NavLink>
          </nav>
        </aside>
        <main>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
