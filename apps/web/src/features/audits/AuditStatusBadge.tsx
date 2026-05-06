import { useTranslation } from "react-i18next";

import type { AuditStatus } from "../../lib/api/types";
import { statusBadgeClasses } from "./auditStatusMeta";

export function AuditStatusBadge({ status }: { status: AuditStatus }) {
  const { t } = useTranslation("audits");
  return (
    <span
      className={`inline-flex min-w-20 items-center justify-center rounded-full border px-2.5 py-1 text-xs font-medium ${statusBadgeClasses[status]}`}
    >
      {t(`status.${status}`)}
    </span>
  );
}
