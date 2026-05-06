import { useTranslation } from "react-i18next";

import type { RunStatus } from "../../lib/api/types";
import { runStatusBadgeClasses } from "./runStatusMeta";

export function RunStatusBadge({ status }: { status: RunStatus }) {
  const { t } = useTranslation("audits");
  return (
    <span
      className={`inline-flex min-w-24 items-center justify-center rounded-full border px-2.5 py-1 text-xs font-medium ${runStatusBadgeClasses[status]}`}
    >
      {t(`runStatus.${status}`)}
    </span>
  );
}
