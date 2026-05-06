import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, ChevronDown, ChevronUp } from "lucide-react";
import { Fragment, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { getAuditResults } from "../../lib/api/client";
import type { AuditResultRow, CompetitorCandidate, Concept, RunStatus } from "../../lib/api/types";
import { AuditBreadcrumbs } from "./AuditBreadcrumbs";
import { AuditViewTabs } from "./AuditViewTabs";
import { ProviderIssueText } from "./ProviderDiagnostics";
import { RunStatusBadge } from "./RunStatusBadge";

type VisibilityFilter = "all" | "visible" | "not_visible" | "unknown";

function formatScore(value: number | null | undefined) {
  return value === null || value === undefined ? "N/A" : value.toFixed(2);
}

function visibilityLabel(value: boolean | null, t: (key: string) => string) {
  if (value === true) {
    return t("visibility.visible");
  }
  if (value === false) {
    return t("visibility.notVisible");
  }
  return t("visibility.unknown");
}

function visibilityClasses(value: boolean | null) {
  if (value === true) {
    return "bg-emerald-50 text-emerald-700";
  }
  if (value === false) {
    return "bg-red-50 text-red-700";
  }
  return "bg-slate-100 text-slate-700";
}

function rowMatchesVisibility(row: AuditResultRow, filter: VisibilityFilter) {
  if (filter === "all") {
    return true;
  }
  if (filter === "visible") {
    return row.visible_brand === true;
  }
  if (filter === "not_visible") {
    return row.visible_brand === false;
  }
  return row.visible_brand === null;
}

function componentScoreText(row: AuditResultRow, t: (key: string) => string) {
  const scores = row.component_scores;
  if (!scores) {
    return "N/A";
  }

  // Display backend component scores as-is; scoring formulas stay server-side.
  return [
    `${t("details.prominence")} ${formatScore(scores.prominence_score)}`,
    `${t("details.sentiment")} ${formatScore(scores.sentiment_score)}`,
    `${t("details.recommendation")} ${formatScore(scores.recommendation_score)}`,
    `${t("details.sourceQuality")} ${formatScore(scores.source_quality_score)}`,
  ].join(" · ");
}

function conceptsForRow(row: AuditResultRow): Concept[] {
  if (row.concepts && row.concepts.length > 0) {
    return row.concepts;
  }
  return row.competitors.map((text) => ({
    text,
    type: "concept" as const,
    category: "legacy",
    count: 1,
    evidence_count: 1,
  }));
}

function confidenceText(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "N/A";
  }
  return `${Math.round(value * 100)}%`;
}

function ConceptList({
  concepts,
  t,
}: {
  concepts: Concept[];
  t: (key: string, options?: Record<string, unknown>) => string;
}) {
  if (concepts.length === 0) {
    return <p className="mt-2 text-sm text-subtle">{t("details.noConcepts")}</p>;
  }

  return (
    <ul className="mt-2 grid gap-2 md:grid-cols-2">
      {concepts.map((concept) => (
        <li
          className="rounded-md border border-border bg-white px-3 py-2"
          key={`${concept.text}-${concept.category ?? "none"}`}
        >
          <p className="font-medium text-ink">{concept.text}</p>
          <p className="mt-1 text-xs text-subtle">
            {[
              concept.category,
              t("details.count", { count: concept.count }),
              t("details.evidence", { count: concept.evidence_count }),
            ]
              .filter(Boolean)
              .join(" · ")}
          </p>
        </li>
      ))}
    </ul>
  );
}

function CompetitorCandidateList({
  candidates,
  t,
}: {
  candidates: CompetitorCandidate[];
  t: (key: string, options?: Record<string, unknown>) => string;
}) {
  if (candidates.length === 0) {
    return <p className="mt-2 text-sm text-subtle">{t("details.noCompetitorCandidates")}</p>;
  }

  return (
    <ul className="mt-2 grid gap-2 md:grid-cols-2">
      {candidates.map((candidate) => (
        <li
          className="rounded-md border border-border bg-white px-3 py-2"
          key={`${candidate.name}-${candidate.domain ?? "none"}`}
        >
          <p className="font-medium text-ink">{candidate.name}</p>
          <p className="mt-1 text-xs text-subtle">
            {[
              candidate.domain,
              candidate.evidence_type,
              t("details.confidence", { value: confidenceText(candidate.confidence) }),
              t("details.evidence", { count: candidate.evidence_count }),
            ]
              .filter(Boolean)
              .join(" · ")}
          </p>
        </li>
      ))}
    </ul>
  );
}

export function AuditResultsPage() {
  const { t } = useTranslation(["results", "audits"]);
  const params = useParams();
  const auditId = Number(params.auditId);
  const isValidAuditId = Number.isInteger(auditId) && auditId > 0;
  const [providerFilter, setProviderFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState<RunStatus | "all">("all");
  const [visibilityFilter, setVisibilityFilter] = useState<VisibilityFilter>("all");
  const [expandedRunId, setExpandedRunId] = useState<number | null>(null);
  const results = useQuery({
    queryKey: ["audit", auditId, "results"],
    queryFn: () => getAuditResults(auditId),
    enabled: isValidAuditId,
    retry: false,
  });

  const providers = useMemo(
    () => Array.from(new Set(results.data?.rows.map((row) => row.provider) ?? [])).sort(),
    [results.data?.rows],
  );
  const filteredRows = useMemo(
    () =>
      results.data?.rows.filter(
        (row) =>
          (providerFilter === "all" || row.provider === providerFilter) &&
          (statusFilter === "all" || row.run_status === statusFilter) &&
          rowMatchesVisibility(row, visibilityFilter),
      ) ?? [],
    [providerFilter, results.data?.rows, statusFilter, visibilityFilter],
  );

  if (results.isLoading) {
    return (
      <section className="rounded-md border border-border bg-surface px-5 py-10 text-sm text-subtle shadow-panel" role="status">
        {t("loadingResults")}
      </section>
    );
  }

  if (results.isError || !results.data || !isValidAuditId) {
    return (
      <section className="rounded-md border border-border bg-surface p-5 shadow-panel">
        <div className="flex items-center gap-2 text-sm text-red-700">
          <AlertTriangle className="size-4" aria-hidden="true" />
          {t("loadResultsError")}
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
            auditNumber={results.data.audit_number}
            current={t("results")}
          />
          <h1 className="text-xl font-semibold text-ink">{t("auditResults")}</h1>
          <p className="mt-1 text-sm text-subtle">
            {t("auditRows", {
              count: results.data.total,
              number: results.data.audit_number,
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

      <AuditViewTabs auditId={auditId} active="results" />

      {results.data.rows.length > 0 ? (
        <div className="grid gap-3 border-b border-border px-5 py-3 md:grid-cols-3">
          <label className="text-sm font-medium text-ink">
            {t("filters.provider")}
            <select
              className="mt-1 h-10 w-full rounded-md border border-border bg-white px-3 text-sm text-ink"
              value={providerFilter}
              onChange={(event) => setProviderFilter(event.target.value)}
            >
              <option value="all">{t("filters.allProviders")}</option>
              {providers.map((provider) => (
                <option value={provider} key={provider}>
                  {provider}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm font-medium text-ink">
            {t("filters.runStatus")}
            <select
              className="mt-1 h-10 w-full rounded-md border border-border bg-white px-3 text-sm text-ink"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as RunStatus | "all")}
            >
              <option value="all">{t("filters.allStatuses")}</option>
              <option value="pending">{t("audits:runStatus.pending")}</option>
              <option value="success">{t("audits:runStatus.success")}</option>
              <option value="error">{t("audits:runStatus.error")}</option>
              <option value="timeout">{t("audits:runStatus.timeout")}</option>
              <option value="rate_limited">{t("audits:runStatus.rate_limited")}</option>
            </select>
          </label>
          <label className="text-sm font-medium text-ink">
            {t("filters.visibility")}
            <select
              className="mt-1 h-10 w-full rounded-md border border-border bg-white px-3 text-sm text-ink"
              value={visibilityFilter}
              onChange={(event) => setVisibilityFilter(event.target.value as VisibilityFilter)}
            >
              <option value="all">{t("filters.allVisibility")}</option>
              <option value="visible">{t("visibility.visible")}</option>
              <option value="not_visible">{t("visibility.notVisible")}</option>
              <option value="unknown">{t("visibility.unknown")}</option>
            </select>
          </label>
        </div>
      ) : null}

      {results.data.rows.length === 0 ? (
        <div className="px-5 py-10">
          <p className="text-sm font-medium text-ink">{t("empty.resultsTitle")}</p>
          <p className="mt-1 text-sm text-subtle">{t("empty.resultsBody")}</p>
        </div>
      ) : null}

      {results.data.rows.length > 0 && filteredRows.length === 0 ? (
        <div className="px-5 py-10 text-sm text-subtle">{t("empty.noFilterMatch")}</div>
      ) : null}

      {filteredRows.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-border text-sm">
            <thead className="bg-muted text-left text-xs uppercase text-subtle">
              <tr>
                <th className="px-5 py-3 font-semibold">{t("table.query")}</th>
                <th className="px-3 py-3 font-semibold">{t("table.provider")}</th>
                <th className="px-3 py-3 font-semibold">{t("table.run")}</th>
                <th className="px-3 py-3 font-semibold">{t("table.status")}</th>
                <th className="px-3 py-3 font-semibold">{t("table.level")}</th>
                <th className="px-3 py-3 font-semibold">{t("table.visibility")}</th>
                <th className="px-3 py-3 font-semibold">{t("table.rank")}</th>
                <th className="px-3 py-3 font-semibold">{t("table.score")}</th>
                <th className="px-3 py-3 font-semibold">{t("table.details")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredRows.map((row) => (
                <Fragment key={row.run_id}>
                  <tr className="align-top">
                    <td className="max-w-md px-5 py-3 text-ink">
                      <p className="line-clamp-2">{row.query}</p>
                      {row.error_message ? (
                        <p className="mt-1 text-xs text-red-700">{row.error_message}</p>
                      ) : null}
                      <ProviderIssueText diagnostic={row.provider_error} />
                    </td>
                    <td className="px-3 py-3 text-subtle">{row.provider}</td>
                    <td className="px-3 py-3 text-subtle">#{row.run_number}</td>
                    <td className="px-3 py-3">
                      <RunStatusBadge status={row.run_status} />
                    </td>
                    <td className="px-3 py-3 text-subtle">{row.scdl_level}</td>
                    <td className="px-3 py-3">
                      <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${visibilityClasses(row.visible_brand)}`}>
                        {visibilityLabel(row.visible_brand, t)}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-subtle">
                      {row.brand_position_rank ?? "N/A"}
                    </td>
                    <td className="px-3 py-3 text-subtle">{formatScore(row.final_score)}</td>
                    <td className="px-3 py-3">
                      <Button
                        type="button"
                        variant="ghost"
                        onClick={() =>
                          setExpandedRunId(expandedRunId === row.run_id ? null : row.run_id)
                        }
                      >
                        {expandedRunId === row.run_id ? (
                          <ChevronUp className="size-4" aria-hidden="true" />
                        ) : (
                          <ChevronDown className="size-4" aria-hidden="true" />
                        )}
                        {t("table.details")}
                      </Button>
                    </td>
                  </tr>
                  {expandedRunId === row.run_id ? (
                    <tr>
                      <td className="bg-slate-50 px-5 py-3 text-sm text-subtle" colSpan={9}>
                        <p>{componentScoreText(row, t)}</p>
                        <div className="mt-4 grid gap-4 lg:grid-cols-2">
                          <section>
                            <h2 className="text-sm font-semibold text-ink">
                              {t("details.concepts")}
                            </h2>
                            <ConceptList concepts={conceptsForRow(row)} t={t} />
                          </section>
                          <section>
                            <h2 className="text-sm font-semibold text-ink">
                              {t("details.competitorCandidates")}
                            </h2>
                            <CompetitorCandidateList
                              candidates={row.competitor_candidates ?? []}
                              t={t}
                            />
                          </section>
                        </div>
                        <p className="mt-1">
                          {t("details.sources")}:{" "}
                          {row.sources.length > 0
                            ? row.sources.map((source) => source.domain ?? source.url ?? t("details.unknown")).join(", ")
                            : t("details.none")}
                        </p>
                      </td>
                    </tr>
                  ) : null}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
