import { AlertTriangle, BarChart3, GitCompareArrows } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "../../components/ui/Button";
import type {
  AuditStatus,
  AuditTrendPoint,
  LongitudinalChangeItem,
  MetricDelta,
  ModelDelta,
} from "../../lib/api/types";
import { useLocaleFormatters } from "../../lib/i18n/format";
import {
  useAuditComparison,
  useBrandAuditTrends,
  useComparisonCandidates,
} from "./useAuditLongitudinal";

const comparableStatuses = new Set<AuditStatus>([
  "completed",
  "partial",
  "failed",
  "cancelled",
]);

function formatMetric(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "N/A";
  }
  return Math.abs(value) <= 1 ? `${Math.round(value * 100)}%` : `${Math.round(value)}%`;
}

function formatDelta(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "N/A";
  }
  const normalized = Math.abs(value) <= 1 ? value * 100 : value;
  const prefix = normalized > 0 ? "+" : "";
  return `${prefix}${normalized.toFixed(1)} pts`;
}

function formatCountDelta(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "N/A";
  }
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value}`;
}

function metricLabel(key: string) {
  return key.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function MetricDeltaCard({ name, delta }: { name: string; delta: MetricDelta }) {
  return (
    <div className="rounded-md border border-border bg-white p-3">
      <p className="text-xs font-semibold uppercase text-subtle">{metricLabel(name)}</p>
      <p className="mt-2 text-xl font-semibold text-ink">{formatDelta(delta.delta)}</p>
      <p className="mt-1 text-xs text-subtle">
        {formatMetric(delta.previous)} {"->"} {formatMetric(delta.current)}
      </p>
    </div>
  );
}

function ChangeList({
  title,
  items,
}: {
  title: string;
  items: LongitudinalChangeItem[];
}) {
  return (
    <div className="rounded-md border border-border bg-white p-4">
      <h3 className="text-sm font-semibold text-ink">{title}</h3>
      {items.length > 0 ? (
        <ul className="mt-3 divide-y divide-border text-sm">
          {items.slice(0, 6).map((item) => (
            <li className="flex items-center justify-between gap-3 py-2" key={item.key}>
              <div>
                <p className="font-medium text-ink">{item.label ?? item.key}</p>
                <p className="text-xs text-subtle">{item.status}</p>
              </div>
              <span className="text-sm font-semibold text-ink">
                {formatCountDelta(item.delta)}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-subtle">No changes detected.</p>
      )}
    </div>
  );
}

function ModelDeltaTable({ rows }: { rows: ModelDelta[] }) {
  return (
    <div className="overflow-x-auto rounded-md border border-border bg-white">
      <table className="min-w-full divide-y divide-border text-left text-sm">
        <thead className="bg-muted text-xs uppercase text-subtle">
          <tr>
            <th className="px-3 py-2 font-semibold">Model</th>
            <th className="px-3 py-2 font-semibold">Mentionability</th>
            <th className="px-3 py-2 font-semibold">Accuracy</th>
            <th className="px-3 py-2 font-semibold">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.map((row) => (
            <tr key={row.model_id}>
              <td className="px-3 py-2">
                <p className="font-medium text-ink">{row.label ?? row.model_id}</p>
                <p className="text-xs text-subtle">{row.model_id}</p>
              </td>
              <td className="px-3 py-2 text-subtle">
                {formatDelta(row.mentionability_delta)}
              </td>
              <td className="px-3 py-2 text-subtle">{formatDelta(row.accuracy_delta)}</td>
              <td className="px-3 py-2 text-subtle">{row.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TrendTable({ points }: { points: AuditTrendPoint[] }) {
  const formatters = useLocaleFormatters();
  return (
    <div className="overflow-x-auto rounded-md border border-border bg-white">
      <table className="min-w-full divide-y divide-border text-left text-sm">
        <thead className="bg-muted text-xs uppercase text-subtle">
          <tr>
            <th className="px-3 py-2 font-semibold">Audit</th>
            <th className="px-3 py-2 font-semibold">Completed</th>
            <th className="px-3 py-2 font-semibold">MR L1</th>
            <th className="px-3 py-2 font-semibold">MR L2</th>
            <th className="px-3 py-2 font-semibold">Runs</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {points.slice(-6).map((point) => (
            <tr key={point.audit_id}>
              <td className="px-3 py-2 font-medium text-ink">#{point.audit_number}</td>
              <td className="px-3 py-2 text-subtle">
                {point.completed_at ? formatters.dateTime(point.completed_at) : "N/A"}
              </td>
              <td className="px-3 py-2 text-subtle">{formatMetric(point.mentionability_l1)}</td>
              <td className="px-3 py-2 text-subtle">{formatMetric(point.mentionability_l2)}</td>
              <td className="px-3 py-2 text-subtle">{point.run_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function AuditLongitudinalPanel({
  auditId,
  brandId,
  auditStatus,
}: {
  auditId: number;
  brandId: number;
  auditStatus: AuditStatus | null | undefined;
}) {
  const { t } = useTranslation("audits");
  const [historyEnabled, setHistoryEnabled] = useState(false);
  const candidates = useComparisonCandidates(auditId, historyEnabled);
  const trends = useBrandAuditTrends(brandId, historyEnabled);
  const firstCandidateId = candidates.data?.candidates[0]?.audit_id ?? null;
  const [selectedCandidateId, setSelectedCandidateId] = useState<number | null>(null);
  const effectiveCandidateId = selectedCandidateId ?? firstCandidateId;
  const comparison = useAuditComparison(auditId, effectiveCandidateId, historyEnabled);
  const canCompare = auditStatus ? comparableStatuses.has(auditStatus) : false;

  const overallDeltas = useMemo(
    () => Object.entries(comparison.data?.overall_delta ?? {}),
    [comparison.data?.overall_delta],
  );

  if (!canCompare) {
    return null;
  }

  return (
    <section className="mx-5 mt-5 space-y-4 rounded-md border border-border bg-muted/40 p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase text-subtle">
            {t("longitudinal.eyebrow")}
          </p>
          <h2 className="mt-1 text-lg font-semibold text-ink">
            {t("longitudinal.title")}
          </h2>
          <p className="mt-1 text-sm text-subtle">{t("longitudinal.subtitle")}</p>
        </div>
        <Button
          type="button"
          variant="secondary"
          onClick={() => setHistoryEnabled(true)}
          disabled={historyEnabled}
        >
          <BarChart3 className="size-4" aria-hidden="true" />
          {historyEnabled ? t("longitudinal.loaded") : t("longitudinal.load")}
        </Button>
      </div>

      {!historyEnabled ? (
        <div className="rounded-md border border-border bg-white px-4 py-3 text-sm text-subtle">
          {t("longitudinal.idle")}
        </div>
      ) : null}

      {candidates.isLoading || trends.isLoading ? (
        <div
          className="rounded-md border border-border bg-white px-4 py-3 text-sm text-subtle"
          role="status"
        >
          {t("longitudinal.loading")}
        </div>
      ) : null}

      {candidates.isError || trends.isError ? (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-900">
          <div className="flex items-center gap-2 font-semibold">
            <AlertTriangle className="size-4" aria-hidden="true" />
            {t("longitudinal.errorTitle")}
          </div>
          <p className="mt-2">{t("longitudinal.errorBody")}</p>
        </div>
      ) : null}

      {historyEnabled && candidates.data && candidates.data.candidates.length === 0 ? (
        <div className="rounded-md border border-border bg-white px-4 py-3 text-sm text-subtle">
          {t("longitudinal.empty")}
        </div>
      ) : null}

      {historyEnabled && candidates.data && candidates.data.candidates.length > 0 ? (
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_18rem]">
          <div className="space-y-4">
            <label className="grid gap-1 text-sm font-medium text-ink">
              <span>{t("longitudinal.compareWith")}</span>
              <select
                className="h-10 rounded-md border border-border bg-white px-3 text-sm text-ink outline-none transition-colors focus:border-brand-600 focus:ring-2 focus:ring-brand-100"
                value={String(effectiveCandidateId ?? "")}
                onChange={(event) => setSelectedCandidateId(Number(event.target.value))}
              >
                {candidates.data.candidates.map((candidate) => (
                  <option key={candidate.audit_id} value={candidate.audit_id}>
                    Audit #{candidate.audit_number}
                  </option>
                ))}
              </select>
            </label>

            {comparison.isLoading ? (
              <div className="rounded-md border border-border bg-white px-4 py-3 text-sm text-subtle" role="status">
                {t("longitudinal.comparisonLoading")}
              </div>
            ) : null}

            {comparison.data ? (
              <>
                {comparison.data.warnings.length > 0 ? (
                  <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                    {comparison.data.warnings.join(" ")}
                  </div>
                ) : null}
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  {overallDeltas.map(([name, delta]) => (
                    <MetricDeltaCard key={name} name={name} delta={delta} />
                  ))}
                </div>
                <div>
                  <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-ink">
                    <GitCompareArrows className="size-4" aria-hidden="true" />
                    {t("longitudinal.modelDeltas")}
                  </h3>
                  <ModelDeltaTable rows={comparison.data.model_deltas} />
                </div>
                <div className="grid gap-3 xl:grid-cols-3">
                  <ChangeList
                    title={t("longitudinal.sourceChanges")}
                    items={comparison.data.source_domain_changes}
                  />
                  <ChangeList
                    title={t("longitudinal.conceptChanges")}
                    items={comparison.data.concept_changes}
                  />
                  <ChangeList
                    title={t("longitudinal.competitorChanges")}
                    items={comparison.data.competitor_changes}
                  />
                </div>
              </>
            ) : null}
          </div>

          <div>
            <h3 className="mb-2 text-sm font-semibold text-ink">
              {t("longitudinal.trends")}
            </h3>
            {trends.data && trends.data.points.length > 0 ? (
              <TrendTable points={trends.data.points} />
            ) : (
              <div className="rounded-md border border-border bg-white px-4 py-3 text-sm text-subtle">
                {t("longitudinal.noTrends")}
              </div>
            )}
          </div>
        </div>
      ) : null}
    </section>
  );
}
