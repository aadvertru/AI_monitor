import { ChevronRight } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

type AuditBreadcrumbsProps = {
  auditId?: number;
  auditNumber?: number;
  current?: string;
};

export function AuditBreadcrumbs({ auditId, auditNumber, current }: AuditBreadcrumbsProps) {
  const { t } = useTranslation("audits");
  const auditLabel = auditNumber
    ? t("breadcrumbs.auditNumber", { number: auditNumber })
    : t("breadcrumbs.audit");

  return (
    <nav aria-label={t("breadcrumbs.label")} className="mb-3 flex flex-wrap items-center gap-1 text-xs text-subtle">
      <Link className="font-medium text-brand-700 hover:underline" to="/audits">
        {t("title")}
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
