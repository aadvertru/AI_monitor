import type { AuditDetail } from "../../lib/api/types";

function formatScdlLevel(level: AuditDetail["scdl_level"]) {
  return level === "L2" ? "L2 - web access" : "L1 - no web access";
}

function formatOptional(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "Not set";
  }
  return String(value);
}

function formatBoolean(value: boolean) {
  return value ? "Yes" : "No";
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
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
  return (
    <section className="border-b border-border px-5 py-5">
      <div className="rounded-md border border-border bg-white p-4">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-sm font-semibold text-ink">Audit setup</h2>
            <p className="mt-1 text-sm text-subtle">
              Saved inputs used for this audit run.
            </p>
          </div>
        </div>

        <dl className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <SetupField label="Brand domain" value={formatOptional(audit.brand_domain)} />
          <SetupField label="SCDL level" value={formatScdlLevel(audit.scdl_level)} />
          <SetupField
            label="Providers"
            value={audit.providers.length > 0 ? audit.providers.join(", ") : "Not set"}
          />
          <SetupField label="Runs per query" value={audit.runs_per_query} />
          <SetupField label="Language" value={formatOptional(audit.language)} />
          <SetupField label="Country" value={formatOptional(audit.country)} />
          <SetupField label="Locale" value={formatOptional(audit.locale)} />
          <SetupField label="Max queries" value={formatOptional(audit.max_queries)} />
          <SetupField
            label="Query expansion"
            value={formatBoolean(audit.enable_query_expansion)}
          />
          <SetupField
            label="Source intelligence"
            value={formatBoolean(audit.enable_source_intelligence)}
          />
          <SetupField label="Created" value={formatDateTime(audit.created_at)} />
          <SetupField label="Updated" value={formatDateTime(audit.updated_at)} />
        </dl>

        {audit.brand_description ? (
          <div className="mt-4 rounded-md border border-border bg-muted px-3 py-2">
            <p className="text-xs font-medium uppercase text-subtle">Brand description</p>
            <p className="mt-1 text-sm text-ink">{audit.brand_description}</p>
          </div>
        ) : null}

        <div className="mt-4">
          <p className="text-xs font-medium uppercase text-subtle">Seed queries</p>
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
            <p className="mt-1 text-sm text-subtle">No seed queries saved.</p>
          )}
        </div>
      </div>
    </section>
  );
}
