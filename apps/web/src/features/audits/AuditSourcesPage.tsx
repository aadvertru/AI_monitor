import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { getAuditSummary } from "../../lib/api/client";
import type { SourceSummaryItem } from "../../lib/api/types";
import { AuditBreadcrumbs } from "./AuditBreadcrumbs";
import { AuditViewTabs } from "./AuditViewTabs";

type SortMode = "citations" | "provider" | "source_type";

function formatScore(value: number | null) {
  return value === null ? "N/A" : value.toFixed(2);
}

function sourceLabel(source: SourceSummaryItem, fallback: string) {
  return source.title ?? source.domain ?? source.url ?? fallback;
}

function sourceLocation(source: SourceSummaryItem, fallback: string) {
  return source.domain ?? source.url ?? fallback;
}

function sortSources(sources: SourceSummaryItem[], sortMode: SortMode) {
  // Sort backend-provided source summaries only; no crawling or classification happens here.
  return [...sources].sort((left, right) => {
    if (sortMode === "citations") {
      return (right.citation_count ?? 0) - (left.citation_count ?? 0);
    }
    if (sortMode === "provider") {
      return (left.provider ?? "").localeCompare(right.provider ?? "");
    }
    return (left.source_type ?? "").localeCompare(right.source_type ?? "");
  });
}

export function AuditSourcesPage() {
  const { t } = useTranslation("results");
  const params = useParams();
  const auditId = Number(params.auditId);
  const isValidAuditId = Number.isInteger(auditId) && auditId > 0;
  const [sortMode, setSortMode] = useState<SortMode>("citations");
  const summary = useQuery({
    queryKey: ["audit", auditId, "summary"],
    queryFn: () => getAuditSummary(auditId),
    enabled: isValidAuditId,
    retry: false,
  });

  const sortedSources = useMemo(
    () => sortSources(summary.data?.sources ?? [], sortMode),
    [sortMode, summary.data?.sources],
  );

  if (summary.isLoading) {
    return (
      <section className="rounded-md border border-border bg-surface px-5 py-10 text-sm text-subtle shadow-panel" role="status">
        {t("loadingSources")}
      </section>
    );
  }

  if (summary.isError || !summary.data || !isValidAuditId) {
    return (
      <section className="rounded-md border border-border bg-surface p-5 shadow-panel">
        <div className="flex items-center gap-2 text-sm text-red-700">
          <AlertTriangle className="size-4" aria-hidden="true" />
          {t("loadSourcesError")}
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-md border border-border bg-surface shadow-panel">
      <div className="flex flex-col gap-3 border-b border-border px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <AuditBreadcrumbs
            auditId={auditId}
            auditNumber={summary.data.audit_number}
            current={t("sources")}
          />
          <h1 className="text-xl font-semibold text-ink">{t("sourceIntelligence")}</h1>
          <p className="mt-1 text-sm text-subtle">
            {t("auditSources", {
              count: summary.data.sources.length,
              number: summary.data.audit_number,
            })}
          </p>
        </div>
        <Button asChild variant="ghost">
          <Link to={`/audits/${auditId}`}>
            <ArrowLeft className="size-4" aria-hidden="true" />
            {t("backToDetail")}
          </Link>
        </Button>
      </div>

      <AuditViewTabs auditId={auditId} active="sources" />

      {summary.data.sources.length > 0 ? (
        <div className="border-b border-border px-5 py-3">
          <label className="block max-w-xs text-sm font-medium text-ink">
            {t("sort.label")}
            <select
              className="mt-1 h-10 w-full rounded-md border border-border bg-white px-3 text-sm text-ink"
              value={sortMode}
              onChange={(event) => setSortMode(event.target.value as SortMode)}
            >
              <option value="citations">{t("sort.citations")}</option>
              <option value="provider">{t("sort.provider")}</option>
              <option value="source_type">{t("sort.sourceType")}</option>
            </select>
          </label>
        </div>
      ) : null}

      {summary.data.sources.length === 0 ? (
        <div className="px-5 py-10">
          <p className="text-sm font-medium text-ink">{t("empty.sourcesTitle")}</p>
          <p className="mt-1 text-sm text-subtle">{t("empty.sourcesBody")}</p>
        </div>
      ) : null}

      {sortedSources.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-border text-sm">
            <thead className="bg-muted text-left text-xs uppercase text-subtle">
              <tr>
                <th className="px-5 py-3 font-semibold">{t("table.source")}</th>
                <th className="px-3 py-3 font-semibold">{t("table.provider")}</th>
                <th className="px-3 py-3 font-semibold">{t("table.type")}</th>
                <th className="px-3 py-3 font-semibold">{t("table.citations")}</th>
                <th className="px-3 py-3 font-semibold">{t("table.queries")}</th>
                <th className="px-3 py-3 font-semibold">{t("table.quality")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {sortedSources.map((source, index) => (
                <tr key={`${source.url ?? source.domain ?? "source"}-${index}`}>
                  <td className="px-5 py-3">
                    <p className="font-medium text-ink">{sourceLabel(source, t("sections.untitledSource"))}</p>
                    <p className="text-subtle">{sourceLocation(source, t("sections.noUrl"))}</p>
                  </td>
                  <td className="px-3 py-3 text-subtle">{source.provider ?? "N/A"}</td>
                  <td className="px-3 py-3 text-subtle">{source.source_type ?? "N/A"}</td>
                  <td className="px-3 py-3 text-subtle">{source.citation_count ?? 0}</td>
                  <td className="px-3 py-3 text-subtle">{source.related_query_count ?? 0}</td>
                  <td className="px-3 py-3 text-subtle">{formatScore(source.source_quality_score)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
