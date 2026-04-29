import { ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";

type AuditBreadcrumbsProps = {
  auditId?: number;
  auditNumber?: number;
  current?: string;
};

export function AuditBreadcrumbs({ auditId, auditNumber, current }: AuditBreadcrumbsProps) {
  const auditLabel = auditNumber ? `Audit #${auditNumber}` : "Audit";

  return (
    <nav aria-label="Breadcrumb" className="mb-3 flex flex-wrap items-center gap-1 text-xs text-subtle">
      <Link className="font-medium text-brand-700 hover:underline" to="/audits">
        Audits
      </Link>
      {auditId ? (
        <>
          <ChevronRight className="size-3" aria-hidden="true" />
          {current ? (
            <Link className="font-medium text-brand-700 hover:underline" to={`/audits/${auditId}`}>
              {auditLabel}
            </Link>
          ) : (
            <span className="font-medium text-ink">{auditLabel}</span>
          )}
        </>
      ) : null}
      {current ? (
        <>
          <ChevronRight className="size-3" aria-hidden="true" />
          <span className="font-medium text-ink">{current}</span>
        </>
      ) : null}
    </nav>
  );
}
