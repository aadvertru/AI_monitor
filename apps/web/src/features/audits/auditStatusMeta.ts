import type { AuditStatus } from "../../lib/api/types";

export const statusBadgeClasses: Record<AuditStatus, string> = {
  created: "border-slate-200 bg-slate-100 text-slate-700",
  running: "border-sky-200 bg-sky-50 text-sky-700",
  partial: "border-amber-200 bg-amber-50 text-amber-800",
  completed: "border-emerald-200 bg-emerald-50 text-emerald-700",
  failed: "border-red-200 bg-red-50 text-red-700",
};

export const statusLabels: Record<AuditStatus, string> = {
  created: "Created",
  running: "Running",
  partial: "Partial",
  completed: "Completed",
  failed: "Failed",
};
