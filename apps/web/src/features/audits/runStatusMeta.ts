import type { RunStatus } from "../../lib/api/types";

export const runStatusLabels: Record<RunStatus, string> = {
  pending: "Pending",
  success: "Success",
  error: "Error",
  timeout: "Timeout",
  rate_limited: "Rate limited",
};

export const runStatusBadgeClasses: Record<RunStatus, string> = {
  pending: "border-slate-200 bg-slate-100 text-slate-700",
  success: "border-emerald-200 bg-emerald-50 text-emerald-700",
  error: "border-red-200 bg-red-50 text-red-700",
  timeout: "border-amber-200 bg-amber-50 text-amber-800",
  rate_limited: "border-violet-200 bg-violet-50 text-violet-700",
};
