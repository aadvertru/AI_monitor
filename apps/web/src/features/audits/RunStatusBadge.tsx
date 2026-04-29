import type { RunStatus } from "../../lib/api/types";
import { runStatusBadgeClasses, runStatusLabels } from "./runStatusMeta";

export function RunStatusBadge({ status }: { status: RunStatus }) {
  return (
    <span
      className={`inline-flex min-w-24 items-center justify-center rounded-full border px-2.5 py-1 text-xs font-medium ${runStatusBadgeClasses[status]}`}
    >
      {runStatusLabels[status]}
    </span>
  );
}
