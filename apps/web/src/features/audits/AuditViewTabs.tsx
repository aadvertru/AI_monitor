import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

type AuditView = "summary" | "results" | "sources";

type AuditViewTabsProps = {
  auditId: number;
  active?: AuditView;
};

const auditViews: Array<{ key: AuditView; labelKey: string; path: string }> = [
  { key: "summary", labelKey: "views.summary", path: "" },
  { key: "results", labelKey: "views.results", path: "results" },
  { key: "sources", labelKey: "views.sources", path: "sources" },
];

export function AuditViewTabs({ auditId, active }: AuditViewTabsProps) {
  const { t } = useTranslation("audits");

  return (
    <nav aria-label={t("views.label")} className="border-b border-border px-5">
      <div className="flex flex-wrap gap-1 py-2">
        {auditViews.map((view) => {
          const isActive = active === view.key;

          return (
            <Link
              aria-current={isActive ? "page" : undefined}
              className={`rounded-md border px-3 py-2 text-sm font-medium transition ${
                isActive
                  ? "border-brand-600 bg-brand-50 text-brand-700"
                  : "border-transparent text-subtle hover:bg-muted hover:text-ink"
              }`}
              key={view.key}
              to={view.path ? `/audits/${auditId}/${view.path}` : `/audits/${auditId}`}
            >
              {t(view.labelKey)}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
