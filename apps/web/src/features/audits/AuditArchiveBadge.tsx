import { useTranslation } from "react-i18next";

export function AuditArchiveBadge() {
  const { t } = useTranslation("audits");

  return (
    <span className="inline-flex min-w-20 items-center justify-center rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-800">
      {t("archiveBadge")}
    </span>
  );
}
