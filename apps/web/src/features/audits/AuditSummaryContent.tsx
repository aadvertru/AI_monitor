import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from "recharts";

import type { AuditSummaryResponse } from "../../lib/api/types";
import { useLocaleFormatters } from "../../lib/i18n/format";
import { ProviderDiagnostics } from "./ProviderDiagnostics";

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

export function AuditSummaryContent({
  auditId,
  summary,
}: {
  auditId: number;
  summary: AuditSummaryResponse;
}) {
  const { t } = useTranslation(["results", "audits"]);
  const formatters = useLocaleFormatters();
  const providerData = providerChartData(summary);
  const queryTypeLabel = (value: string) =>
    t(`audits:queryTypes.${value}`, { defaultValue: value });

  return (
    <div className="space-y-5 px-5 py-5">
      <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-7">
        <MetricCard label={t("summaryCards.queries")} value={formatters.number(summary.total_queries)} />
        <MetricCard label={t("summaryCards.runs")} value={formatters.number(summary.total_runs)} />
        <MetricCard label={t("summaryCards.completion")} value={formatters.percent(summary.completion_ratio)} />
        <MetricCard label={t("summaryCards.visibility")} value={formatters.percent(summary.visibility_ratio)} />
        <MetricCard label={t("summaryCards.avgScore")} value={formatScore(summary.average_score)} />
        <MetricCard
          label={t("summaryCards.weighted")}
          value={formatScore(summary.weighted_visibility_score)}
        />
        <MetricCard label={t("summaryCards.critical")} value={formatters.number(summary.critical_query_count)} />
      </div>

      {summary.total_runs === 0 ? (
        <div className="rounded-md border border-border bg-muted px-4 py-3 text-sm text-subtle">
          {t("sections.noRunData")}
        </div>
      ) : null}

      <ProviderDiagnostics diagnostics={summary.provider_diagnostics} compact />

      <div className="rounded-md border border-border bg-white p-4">
        <h2 className="text-sm font-semibold text-ink">{t("sections.queryTypeDiagnostics")}</h2>
        {summary.query_type_coverage.length > 0 ? (
          <div className="mt-3 overflow-x-auto">
            <table className="min-w-full divide-y divide-border text-sm">
              <thead className="text-left text-xs uppercase text-subtle">
                <tr>
                  <th className="py-2 pr-3 font-semibold">{t("sections.queryType")}</th>
                  <th className="px-3 py-2 font-semibold">{t("summaryCards.queries")}</th>
                  <th className="px-3 py-2 font-semibold">{t("sections.processed")}</th>
                  <th className="px-3 py-2 font-semibold">{t("sections.failed")}</th>
                  <th className="px-3 py-2 font-semibold">{t("sections.brandFound")}</th>
                  <th className="px-3 py-2 font-semibold">{t("summaryCards.visibility")}</th>
                  <th className="px-3 py-2 font-semibold">{t("summaryCards.avgScore")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {summary.query_type_coverage.map((item) => (
                  <tr key={item.type}>
                    <td className="py-2 pr-3 font-medium text-ink">
                      {queryTypeLabel(item.type)}
                    </td>
                    <td className="px-3 py-2 text-subtle">{item.total_queries}</td>
                    <td className="px-3 py-2 text-subtle">{item.processed_runs}</td>
                    <td className="px-3 py-2 text-subtle">{item.failed_runs}</td>
                    <td className="px-3 py-2 text-subtle">{item.brand_found_count}</td>
                    <td className="px-3 py-2 text-subtle">
                      {formatters.percent(item.brand_found_rate)}
                    </td>
                    <td className="px-3 py-2 text-subtle">{formatScore(item.average_score)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="mt-3 text-sm text-subtle">
            {t("sections.queryTypeEmpty")}
          </p>
        )}
      </div>

      <div className="grid gap-5 lg:grid-cols-[1fr_0.9fr]">
        <div className="rounded-md border border-border bg-white p-4">
          <h2 className="text-sm font-semibold text-ink">{t("sections.providerSummary")}</h2>
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
            <p className="mt-3 text-sm text-subtle">{t("sections.noProviderScores")}</p>
          )}
        </div>

        <div className="rounded-md border border-border bg-white p-4">
          <h2 className="text-sm font-semibold text-ink">{t("sections.criticalQueries")}</h2>
          {summary.critical_queries.length > 0 ? (
            <ul className="mt-3 divide-y divide-border">
              {summary.critical_queries.slice(0, 5).map((query) => (
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
                    {t("sections.viewRelatedRows")}
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-subtle">{t("sections.noCriticalQueries")}</p>
          )}
        </div>
      </div>

      <div className="rounded-md border border-border bg-white p-4">
        <h2 className="text-sm font-semibold text-ink">{t("sections.competitorVisibility")}</h2>
        {summary.competitors.length > 0 ? (
          <div className="mt-3 overflow-x-auto">
            <table className="min-w-full divide-y divide-border text-sm">
              <thead className="text-left text-xs uppercase text-subtle">
                <tr>
                  <th className="py-2 pr-3 font-semibold">{t("sections.competitor")}</th>
                  <th className="px-3 py-2 font-semibold">{t("sections.mentions")}</th>
                  <th className="px-3 py-2 font-semibold">{t("summaryCards.visibility")}</th>
                  <th className="px-3 py-2 font-semibold">{t("summaryCards.avgScore")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {summary.competitors.slice(0, 8).map((competitor) => (
                  <tr key={competitor.name}>
                    <td className="py-2 pr-3 font-medium text-ink">{competitor.name}</td>
                    <td className="px-3 py-2 text-subtle">{competitor.mention_count ?? 0}</td>
                    <td className="px-3 py-2 text-subtle">
                      {competitor.visibility_ratio === null
                        ? "N/A"
                        : formatters.percent(competitor.visibility_ratio)}
                    </td>
                    <td className="px-3 py-2 text-subtle">{formatScore(competitor.average_score)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="mt-3 text-sm text-subtle">{t("sections.noCompetitors")}</p>
        )}
      </div>

      <div className="rounded-md border border-border bg-white p-4">
        <h2 className="text-sm font-semibold text-ink">{t("sections.topSources")}</h2>
        {summary.sources.length > 0 ? (
          <div className="mt-3 overflow-x-auto">
            <table className="min-w-full divide-y divide-border text-sm">
              <thead className="text-left text-xs uppercase text-subtle">
                <tr>
                  <th className="py-2 pr-3 font-semibold">{t("table.source")}</th>
                  <th className="px-3 py-2 font-semibold">{t("table.provider")}</th>
                  <th className="px-3 py-2 font-semibold">{t("table.citations")}</th>
                  <th className="px-3 py-2 font-semibold">{t("table.quality")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {summary.sources.slice(0, 5).map((source) => (
                  <tr key={`${source.url ?? source.domain}-${source.provider}`}>
                    <td className="py-2 pr-3">
                      <p className="font-medium text-ink">{source.title ?? source.domain ?? t("sections.untitledSource")}</p>
                      <p className="text-subtle">{source.domain ?? source.url ?? t("sections.noUrl")}</p>
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
          <p className="mt-3 text-sm text-subtle">{t("sections.noSourceCitations")}</p>
        )}
      </div>
    </div>
  );
}
