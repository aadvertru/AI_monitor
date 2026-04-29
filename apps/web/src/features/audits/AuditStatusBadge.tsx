import type { AuditStatus } from "../../lib/api/types";
import { statusBadgeClasses, statusLabels } from "./auditStatusMeta";

export function AuditStatusBadge({ status }: { status: AuditStatus }) {
  return (
    <span
      className={`inline-flex min-w-20 items-center justify-center rounded-full border px-2.5 py-1 text-xs font-medium ${statusBadgeClasses[status]}`}
    >
      {statusLabels[status]}
    </span>
  );
}
