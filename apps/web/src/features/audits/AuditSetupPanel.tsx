import { useTranslation } from "react-i18next";

import type { AuditDetail } from "../../lib/api/types";
import { useLocaleFormatters } from "../../lib/i18n/format";

function formatOptional(value: string | number | null | undefined, fallback: string) {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  return String(value);
}

function SetupField({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase text-subtle">{label}</dt>
      <dd className="mt-1 text-sm font-medium text-ink">{value}</dd>
    </div>
  );
}

export function AuditSetupPanel({ audit }: { audit: AuditDetail }) {
  const { t } = useTranslation("audits");
  const formatters = useLocaleFormatters();
  const notSet = t("setup.notSet");
  const formatScdlLevel = (level: AuditDetail["scdl_level"]) =>
    level === "L2" ? t("setup.l2") : t("setup.l1");
  const formatBoolean = (value: boolean) => (value ? t("setup.yes") : t("setup.no"));

  return (
    <section className="border-b border-border px-5 py-5">
      <div className="rounded-md border border-border bg-white p-4">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-sm font-semibold text-ink">{t("setup.title")}</h2>
            <p className="mt-1 text-sm text-subtle">
              {t("setup.subtitle")}
            </p>
          </div>
        </div>

        <dl className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <SetupField label={t("setup.brandDomain")} value={formatOptional(audit.brand_domain, notSet)} />
          <SetupField label={t("setup.scdlLevel")} value={formatScdlLevel(audit.scdl_level)} />
          <SetupField
            label={t("setup.providers")}
            value={audit.providers.length > 0 ? audit.providers.join(", ") : notSet}
          />
          <SetupField label={t("setup.runsPerQuery")} value={audit.runs_per_query} />
          <SetupField label={t("setup.language")} value={formatOptional(audit.language, notSet)} />
          <SetupField label={t("setup.country")} value={formatOptional(audit.country, notSet)} />
          <SetupField label={t("setup.locale")} value={formatOptional(audit.locale, notSet)} />
          <SetupField label={t("setup.maxQueries")} value={formatOptional(audit.max_queries, notSet)} />
          <SetupField
            label={t("setup.queryExpansion")}
            value={formatBoolean(audit.enable_query_expansion)}
          />
          <SetupField
            label={t("setup.sourceIntelligence")}
            value={formatBoolean(audit.enable_source_intelligence)}
          />
          <SetupField label={t("setup.created")} value={formatters.dateTime(audit.created_at)} />
          <SetupField label={t("setup.updated")} value={formatters.dateTime(audit.updated_at)} />
        </dl>

        {audit.brand_description ? (
          <div className="mt-4 rounded-md border border-border bg-muted px-3 py-2">
            <p className="text-xs font-medium uppercase text-subtle">{t("setup.brandDescription")}</p>
            <p className="mt-1 text-sm text-ink">{audit.brand_description}</p>
          </div>
        ) : null}

        <div className="mt-4">
          <p className="text-xs font-medium uppercase text-subtle">{t("setup.seedQueries")}</p>
          {audit.seed_queries.length > 0 ? (
            <ul className="mt-2 grid gap-2">
              {audit.seed_queries.map((query) => (
                <li
                  className="rounded-md border border-border bg-muted px-3 py-2 text-sm text-ink"
                  key={query}
                >
                  {query}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-1 text-sm text-subtle">{t("setup.noSeedQueries")}</p>
          )}
        </div>
      </div>
    </section>
  );
}
