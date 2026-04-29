import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, ChevronDown, ChevronUp } from "lucide-react";
import { Fragment, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { getAuditResults } from "../../lib/api/client";
import type { AuditResultRow, RunStatus } from "../../lib/api/types";
import { RunStatusBadge } from "./RunStatusBadge";

type VisibilityFilter = "all" | "visible" | "not_visible" | "unknown";

function formatScore(value: number | null | undefined) {
  return value === null || value === undefined ? "N/A" : value.toFixed(2);
}

function visibilityLabel(value: boolean | null) {
  if (value === true) {
    return "Visible";
  }
  if (value === false) {
    return "Not visible";
  }
  return "Unknown";
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

function componentScoreText(row: AuditResultRow) {
  const scores = row.component_scores;
  if (!scores) {
    return "N/A";
  }

  // Display backend component scores as-is; scoring formulas stay server-side.
  return [
    `Prominence ${formatScore(scores.prominence_score)}`,
    `Sentiment ${formatScore(scores.sentiment_score)}`,
    `Recommendation ${formatScore(scores.recommendation_score)}`,
    `Source quality ${formatScore(scores.source_quality_score)}`,
  ].join(" · ");
}

export function AuditResultsPage() {
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
        Loading results...
      </section>
    );
  }

  if (results.isError || !results.data || !isValidAuditId) {
    return (
      <section className="rounded-md border border-border bg-surface p-5 shadow-panel">
        <div className="flex items-center gap-2 text-sm text-red-700">
          <AlertTriangle className="size-4" aria-hidden="true" />
          Unable to load results.
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-md border border-border bg-surface shadow-panel">
      <div className="flex flex-col gap-3 border-b border-border px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-ink">Audit results</h1>
          <p className="mt-1 text-sm text-subtle">
            Audit #{results.data.audit_id} · {results.data.total} rows
          </p>
        </div>
        <Button asChild variant="ghost">
          <Link to={`/audits/${auditId}`}>
            <ArrowLeft className="size-4" aria-hidden="true" />
            Back to detail
          </Link>
        </Button>
      </div>

      {results.data.rows.length > 0 ? (
        <div className="grid gap-3 border-b border-border px-5 py-3 md:grid-cols-3">
          <label className="text-sm font-medium text-ink">
            Provider
            <select
              className="mt-1 h-10 w-full rounded-md border border-border bg-white px-3 text-sm text-ink"
              value={providerFilter}
              onChange={(event) => setProviderFilter(event.target.value)}
            >
              <option value="all">All providers</option>
              {providers.map((provider) => (
                <option value={provider} key={provider}>
                  {provider}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm font-medium text-ink">
            Run status
            <select
              className="mt-1 h-10 w-full rounded-md border border-border bg-white px-3 text-sm text-ink"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as RunStatus | "all")}
            >
              <option value="all">All statuses</option>
              <option value="pending">Pending</option>
              <option value="success">Success</option>
              <option value="error">Error</option>
              <option value="timeout">Timeout</option>
              <option value="rate_limited">Rate limited</option>
            </select>
          </label>
          <label className="text-sm font-medium text-ink">
            Visibility
            <select
              className="mt-1 h-10 w-full rounded-md border border-border bg-white px-3 text-sm text-ink"
              value={visibilityFilter}
              onChange={(event) => setVisibilityFilter(event.target.value as VisibilityFilter)}
            >
              <option value="all">All visibility</option>
              <option value="visible">Visible</option>
              <option value="not_visible">Not visible</option>
              <option value="unknown">Unknown</option>
            </select>
          </label>
        </div>
      ) : null}

      {results.data.rows.length === 0 ? (
        <div className="px-5 py-10">
          <p className="text-sm font-medium text-ink">No results yet</p>
          <p className="mt-1 text-sm text-subtle">Run the audit before inspecting per-run outputs.</p>
        </div>
      ) : null}

      {results.data.rows.length > 0 && filteredRows.length === 0 ? (
        <div className="px-5 py-10 text-sm text-subtle">No results match the current filters.</div>
      ) : null}

      {filteredRows.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-border text-sm">
            <thead className="bg-muted text-left text-xs uppercase text-subtle">
              <tr>
                <th className="px-5 py-3 font-semibold">Query</th>
                <th className="px-3 py-3 font-semibold">Provider</th>
                <th className="px-3 py-3 font-semibold">Run</th>
                <th className="px-3 py-3 font-semibold">Status</th>
                <th className="px-3 py-3 font-semibold">Level</th>
                <th className="px-3 py-3 font-semibold">Visibility</th>
                <th className="px-3 py-3 font-semibold">Rank</th>
                <th className="px-3 py-3 font-semibold">Score</th>
                <th className="px-3 py-3 font-semibold">Details</th>
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
                    </td>
                    <td className="px-3 py-3 text-subtle">{row.provider}</td>
                    <td className="px-3 py-3 text-subtle">#{row.run_number}</td>
                    <td className="px-3 py-3">
                      <RunStatusBadge status={row.run_status} />
                    </td>
                    <td className="px-3 py-3 text-subtle">{row.scdl_level}</td>
                    <td className="px-3 py-3">
                      <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${visibilityClasses(row.visible_brand)}`}>
                        {visibilityLabel(row.visible_brand)}
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
                        Details
                      </Button>
                    </td>
                  </tr>
                  {expandedRunId === row.run_id ? (
                    <tr>
                      <td className="bg-slate-50 px-5 py-3 text-sm text-subtle" colSpan={9}>
                        <p>{componentScoreText(row)}</p>
                        <p className="mt-2">
                          Competitors: {row.competitors.length > 0 ? row.competitors.join(", ") : "None"}
                        </p>
                        <p className="mt-1">
                          Sources:{" "}
                          {row.sources.length > 0
                            ? row.sources.map((source) => source.domain ?? source.url ?? "Unknown").join(", ")
                            : "None"}
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
