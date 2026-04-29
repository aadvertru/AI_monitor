import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from "recharts";

import { Button } from "../../components/ui/Button";
import { getAuditSummary } from "../../lib/api/client";
import type { AuditSummaryResponse } from "../../lib/api/types";
import { AuditStatusBadge } from "./AuditStatusBadge";

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function formatScore(value: number | null) {
  return value === null ? "N/A" : value.toFixed(2);
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-border bg-white p-4">
      <p className="text-xs font-medium uppercase text-subtle">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}

function providerChartData(summary: AuditSummaryResponse) {
  // Display backend aggregate provider scores as-is; scoring formulas stay server-side.
  return Object.entries(summary.provider_scores)
    .filter(([, score]) => score !== null)
    .map(([provider, score]) => ({
      provider,
      score: Number(score),
    }));
}

export function AuditSummaryPage() {
  const params = useParams();
  const auditId = Number(params.auditId);
  const isValidAuditId = Number.isInteger(auditId) && auditId > 0;
  const summary = useQuery({
    queryKey: ["audit", auditId, "summary"],
    queryFn: () => getAuditSummary(auditId),
    enabled: isValidAuditId,
    retry: false,
  });

  if (summary.isLoading) {
    return (
      <section className="rounded-md border border-border bg-surface px-5 py-10 text-sm text-subtle shadow-panel" role="status">
        Loading summary...
      </section>
    );
  }

  if (summary.isError || !summary.data || !isValidAuditId) {
    return (
      <section className="rounded-md border border-border bg-surface p-5 shadow-panel">
        <div className="flex items-center gap-2 text-sm text-red-700">
          <AlertTriangle className="size-4" aria-hidden="true" />
          Unable to load summary.
        </div>
      </section>
    );
  }

  const providerData = providerChartData(summary.data);

  return (
    <section className="rounded-md border border-border bg-surface shadow-panel">
      <div className="flex flex-col gap-3 border-b border-border px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold text-ink">Audit summary</h1>
            <AuditStatusBadge status={summary.data.status} />
          </div>
          <p className="mt-1 text-sm text-subtle">Audit #{summary.data.audit_id}</p>
        </div>
        <Button asChild variant="ghost">
          <Link to={`/audits/${auditId}`}>
            <ArrowLeft className="size-4" aria-hidden="true" />
            Back to detail
          </Link>
        </Button>
      </div>

      <div className="space-y-5 px-5 py-5">
        <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
          <MetricCard label="Queries" value={summary.data.total_queries} />
          <MetricCard label="Runs" value={summary.data.total_runs} />
          <MetricCard label="Completion" value={formatPercent(summary.data.completion_ratio)} />
          <MetricCard label="Visibility" value={formatPercent(summary.data.visibility_ratio)} />
          <MetricCard label="Avg score" value={formatScore(summary.data.average_score)} />
          <MetricCard label="Critical" value={summary.data.critical_query_count} />
        </div>

        {summary.data.total_runs === 0 ? (
          <div className="rounded-md border border-border bg-muted px-4 py-3 text-sm text-subtle">
            No run data is available yet.
          </div>
        ) : null}

        <div className="grid gap-5 lg:grid-cols-[1fr_0.9fr]">
          <div className="rounded-md border border-border bg-white p-4">
            <h2 className="text-sm font-semibold text-ink">Provider summary</h2>
            {providerData.length > 0 ? (
              <div className="mt-4 overflow-x-auto" data-testid="provider-score-chart">
                <BarChart data={providerData} width={420} height={220} margin={{ left: -20, right: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="provider" />
                  <YAxis domain={[0, 1]} />
                  <Tooltip />
                  <Bar dataKey="score" fill="hsl(175 84% 32%)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </div>
            ) : (
              <p className="mt-3 text-sm text-subtle">No provider scores yet.</p>
            )}
          </div>

          <div className="rounded-md border border-border bg-white p-4">
            <h2 className="text-sm font-semibold text-ink">Critical queries</h2>
            {summary.data.critical_queries.length > 0 ? (
              <ul className="mt-3 divide-y divide-border">
                {summary.data.critical_queries.slice(0, 5).map((query) => (
                  <li className="py-2 text-sm" key={query.query}>
                    <div className="flex items-start justify-between gap-3">
                      <span className="font-medium text-ink">{query.query}</span>
                      <span className="shrink-0 text-subtle">{formatScore(query.query_score)}</span>
                    </div>
                    <p className="mt-1 text-subtle">{query.reason}</p>
                    <Link
                      className="mt-1 inline-block text-xs font-medium text-brand-700 hover:underline"
                      to={`/audits/${auditId}/results`}
                    >
                      View related rows
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-subtle">No critical queries detected.</p>
            )}
          </div>
        </div>

        <div className="rounded-md border border-border bg-white p-4">
          <h2 className="text-sm font-semibold text-ink">Competitor visibility</h2>
          {summary.data.competitors.length > 0 ? (
            <div className="mt-3 overflow-x-auto">
              <table className="min-w-full divide-y divide-border text-sm">
                <thead className="text-left text-xs uppercase text-subtle">
                  <tr>
                    <th className="py-2 pr-3 font-semibold">Competitor</th>
                    <th className="px-3 py-2 font-semibold">Mentions</th>
                    <th className="px-3 py-2 font-semibold">Visibility</th>
                    <th className="px-3 py-2 font-semibold">Avg score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {summary.data.competitors.slice(0, 8).map((competitor) => (
                    <tr key={competitor.name}>
                      <td className="py-2 pr-3 font-medium text-ink">{competitor.name}</td>
                      <td className="px-3 py-2 text-subtle">{competitor.mention_count ?? 0}</td>
                      <td className="px-3 py-2 text-subtle">
                        {competitor.visibility_ratio === null
                          ? "N/A"
                          : formatPercent(competitor.visibility_ratio)}
                      </td>
                      <td className="px-3 py-2 text-subtle">{formatScore(competitor.average_score)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="mt-3 text-sm text-subtle">No competitors detected.</p>
          )}
        </div>

        <div className="rounded-md border border-border bg-white p-4">
          <h2 className="text-sm font-semibold text-ink">Top sources</h2>
          {summary.data.sources.length > 0 ? (
            <div className="mt-3 overflow-x-auto">
              <table className="min-w-full divide-y divide-border text-sm">
                <thead className="text-left text-xs uppercase text-subtle">
                  <tr>
                    <th className="py-2 pr-3 font-semibold">Source</th>
                    <th className="px-3 py-2 font-semibold">Provider</th>
                    <th className="px-3 py-2 font-semibold">Citations</th>
                    <th className="px-3 py-2 font-semibold">Quality</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {summary.data.sources.slice(0, 5).map((source) => (
                    <tr key={`${source.url ?? source.domain}-${source.provider}`}>
                      <td className="py-2 pr-3">
                        <p className="font-medium text-ink">{source.title ?? source.domain ?? "Untitled source"}</p>
                        <p className="text-subtle">{source.domain ?? source.url ?? "No URL"}</p>
                      </td>
                      <td className="px-3 py-2 text-subtle">{source.provider ?? "N/A"}</td>
                      <td className="px-3 py-2 text-subtle">{source.citation_count ?? 0}</td>
                      <td className="px-3 py-2 text-subtle">{formatScore(source.source_quality_score)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="mt-3 text-sm text-subtle">No source citations yet.</p>
          )}
        </div>
      </div>
    </section>
  );
}
