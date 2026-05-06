import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, FileSpreadsheet, FileText, Repeat2, RotateCcw } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { downloadAuditExport, duplicateAudit, rerunAuditEvaluation } from "../../lib/api/client";
import type { AuditExportKind } from "../../lib/api/client";
import type {
  AuditDetail,
  AuditTarget,
  MentionabilityMetric,
  SCDLLevel,
  AuditSummaryV2ModelSummary,
} from "../../lib/api/types";
import { useLocaleFormatters } from "../../lib/i18n/format";
import { AuditStatusBadge } from "./AuditStatusBadge";
import { ProviderDiagnostics } from "./ProviderDiagnostics";
import { auditSummaryV2QueryKey, useAuditSummaryV2 } from "./useAuditSummaryV2";

function SummaryMetricCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-md border border-border bg-white p-4">
      <p className="text-xs font-semibold uppercase text-subtle">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
      <p className="mt-1 text-xs text-subtle">{detail}</p>
    </div>
  );
}

function uniqueValues(values: Array<string | null | undefined>) {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value))));
}

function formatLevelList(levels: SCDLLevel[]) {
  return levels.length > 0 ? levels.join(" / ") : "N/A";
}

function legacyTargets(audit: AuditDetail): AuditTarget[] {
  return audit.providers.map((provider) => ({
    aiFamily: provider,
    executionProvider: provider,
    modelProvider: provider,
    modelId: provider,
    displayName: provider,
    level: audit.scdl_level,
  }));
}

function formatBackendPercentage(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "N/A";
  }
  return `${Math.round(value)}%`;
}

function formatBackendDelta(value: number | null | undefined, suffix = "%") {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "N/A";
  }
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(0)}${suffix}`;
}

function mentionabilityDetail(metric: MentionabilityMetric) {
  return `${metric.found}/${metric.total}`;
}

function formatTonePair(model: AuditSummaryV2ModelSummary) {
  const l1 = model.tone_l1 ?? "N/A";
  const l2 = model.tone_l2 ?? "N/A";
  return `${l1} / ${l2}`;
}

function triggerBrowserDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export function Web5SummaryShell({
  auditId,
  audit,
}: {
  auditId: number;
  audit: AuditDetail;
}) {
  const { t } = useTranslation("results");
  const formatters = useLocaleFormatters();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const summary = useAuditSummaryV2(auditId);
  const rerunEvaluation = useMutation({
    mutationFn: () => rerunAuditEvaluation(auditId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: auditSummaryV2QueryKey(auditId) });
      void queryClient.invalidateQueries({
        queryKey: ["audit", auditId, "answer-matrix"],
        refetchType: "none",
      });
      void queryClient.invalidateQueries({
        queryKey: ["audit", auditId, "status"],
        refetchType: "none",
      });
      void queryClient.invalidateQueries({
        queryKey: ["audit", auditId, "detail"],
        refetchType: "none",
      });
    },
  });
  const exportDownload = useMutation({
    mutationFn: async (kind: AuditExportKind) => {
      const result = await downloadAuditExport(auditId, kind);
      triggerBrowserDownload(result.blob, result.filename);
      return result;
    },
  });
  const repeatAudit = useMutation({
    mutationFn: () => duplicateAudit(auditId),
    onSuccess: (result) => {
      void queryClient.invalidateQueries({ queryKey: ["audits"] });
      navigate(`/audits/${result.audit_id}`);
    },
  });

  if (summary.isLoading) {
    return (
      <section
        className="mx-5 mt-5 rounded-md border border-border bg-muted px-4 py-3 text-sm text-subtle"
        role="status"
      >
        {t("web5.loading")}
      </section>
    );
  }

  if (summary.isError) {
    return (
      <section className="mx-5 mt-5 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-900">
        <div className="flex items-center gap-2 font-semibold">
          <AlertTriangle className="size-4" aria-hidden="true" />
          {t("web5.errorTitle")}
        </div>
        <p className="mt-2">{t("web5.errorBody")}</p>
      </section>
    );
  }

  const data = summary.data;
  if (!data) {
    return null;
  }

  const hasRunData = data.totals.run_count > 0 || data.model_summaries.length > 0;
  const hasRunIssues = data.status === "partial" || data.status === "failed" || data.totals.failed_runs > 0;
  const hasEvaluations =
    data.overall.accuracy_l1 !== null || data.overall.accuracy_l2 !== null;
  const targets =
    audit.modelTargets && audit.modelTargets.length > 0
      ? audit.modelTargets
      : legacyTargets(audit);
  const families = uniqueValues(targets.map((target) => target.aiFamily));
  const l2GatewayTargets = targets.filter(
    (target) => target.level === "L2" && target.gatewayL2Experimental,
  );

  return (
    <section className="mx-5 mt-5 space-y-4 rounded-md border border-border bg-muted/40 p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase text-subtle">
            {t("web5.eyebrow")}
          </p>
          <div className="mt-1 flex flex-wrap items-center gap-3">
            <h2 className="text-lg font-semibold text-ink">{t("web5.title")}</h2>
            <AuditStatusBadge status={data.status} />
          </div>
          <p className="mt-1 text-sm text-subtle">
            {t("web5.subtitle", {
              queries: formatters.number(data.totals.query_count),
              targets: formatters.number(data.totals.target_count),
              runs: formatters.number(data.totals.run_count),
            })}
          </p>
          <p className="mt-1 text-xs text-subtle">
            {t("web5.auditMeta", {
              number: audit.audit_number,
              updated: formatters.dateTime(audit.updated_at),
              completed: formatters.number(data.totals.completed_runs),
              failed: formatters.number(data.totals.failed_runs),
              partial: formatters.number(data.totals.partial_runs),
            })}
          </p>
        </div>
        <div className="rounded-md border border-border bg-white px-3 py-2 text-sm text-subtle">
          {t("web5.endpointLabel")}: <span className="font-medium text-ink">summary-v2</span>
        </div>
      </div>

      {!hasRunData ? (
        <div className="rounded-md border border-border bg-white px-4 py-3 text-sm text-subtle">
          {t("web5.empty")}
        </div>
      ) : null}

      {hasRunIssues ? (
        <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          {t("web5.partialState")}
        </div>
      ) : null}

      {!hasEvaluations ? (
        <div className="rounded-md border border-border bg-white px-4 py-3 text-sm text-subtle">
          {t("web5.noEvaluations")}
        </div>
      ) : null}

      <ProviderDiagnostics diagnostics={data.provider_diagnostics} compact />

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <SummaryMetricCard
          label={t("web5.mentionabilityL1")}
          value={formatBackendPercentage(data.overall.mentionability_l1.percentage)}
          detail={t("web5.foundOutOfTotal", {
            count: mentionabilityDetail(data.overall.mentionability_l1),
          })}
        />
        <SummaryMetricCard
          label={t("web5.mentionabilityL2")}
          value={formatBackendPercentage(data.overall.mentionability_l2.percentage)}
          detail={t("web5.foundOutOfTotal", {
            count: mentionabilityDetail(data.overall.mentionability_l2),
          })}
        />
        <SummaryMetricCard
          label={t("web5.accuracyL1")}
          value={formatters.percent(data.overall.accuracy_l1)}
          detail={t("web5.backendMetric")}
        />
        <SummaryMetricCard
          label={t("web5.accuracyL2")}
          value={formatters.percent(data.overall.accuracy_l2)}
          detail={t("web5.backendMetric")}
        />
        <SummaryMetricCard
          label={t("web5.tone")}
          value={t("web5.toneSummary")}
          detail={[
            t("web5.tonePositive", { count: data.overall.tone.positive }),
            t("web5.toneNeutral", { count: data.overall.tone.neutral }),
            t("web5.toneNegative", { count: data.overall.tone.negative }),
            t("web5.toneUnknown", { count: data.overall.tone.unknown }),
          ].join(" · ")}
        />
      </div>

      <details className="rounded-md border border-border bg-white p-4">
        <summary className="cursor-pointer text-sm font-semibold text-ink">
          {t("web5.testedScopeTitle")}
        </summary>
        <div className="mt-3 grid gap-3 text-sm md:grid-cols-3">
          <div>
            <p className="text-xs font-semibold uppercase text-subtle">
              {t("web5.testedLevels")}
            </p>
            <p className="mt-1 font-medium text-ink">{formatLevelList(data.totals.levels)}</p>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase text-subtle">
              {t("web5.testedFamilies")}
            </p>
            <p className="mt-1 font-medium text-ink">
              {families.length > 0 ? families.join(", ") : "N/A"}
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase text-subtle">
              {t("web5.openRouterL2")}
            </p>
            <p className="mt-1 font-medium text-ink">
              {l2GatewayTargets.length > 0
                ? t("web5.experimentalTargets", { count: l2GatewayTargets.length })
                : t("web5.none")}
            </p>
          </div>
        </div>
        <ul className="mt-3 grid gap-2">
          {targets.map((target) => (
            <li
              className="rounded-md border border-border bg-muted px-3 py-2 text-sm"
              key={`${target.modelId}-${target.level}-${target.executionProvider}`}
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium text-ink">{target.displayName}</span>
                <span className="rounded-full bg-white px-2 py-0.5 text-xs text-subtle">
                  {target.level}
                </span>
                {target.gateway ? (
                  <span className="rounded-full bg-brand-50 px-2 py-0.5 text-xs text-brand-700">
                    {t("web5.gateway")}
                  </span>
                ) : null}
                {target.gatewayL2Experimental ? (
                  <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs text-amber-700">
                    {t("web5.l2Experimental")}
                  </span>
                ) : null}
              </div>
              <p className="mt-1 text-xs text-subtle">{target.modelId}</p>
            </li>
          ))}
        </ul>
      </details>

      <div className="rounded-md border border-border bg-white p-4">
        <h3 className="text-sm font-semibold text-ink">{t("web5.actionsTitle")}</h3>
        <p className="mt-1 text-sm text-subtle">{t("web5.actionsBody")}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Button
            type="button"
            variant="secondary"
            disabled={rerunEvaluation.isPending}
            onClick={() => rerunEvaluation.mutate()}
          >
            <RotateCcw className="size-4" aria-hidden="true" />
            {rerunEvaluation.isPending ? t("web5.rerunPending") : t("web5.rerun")}
          </Button>
          <Button
            type="button"
            variant="secondary"
            disabled={exportDownload.isPending}
            onClick={() => exportDownload.mutate("docx")}
          >
            <FileText className="size-4" aria-hidden="true" />
            {exportDownload.isPending && exportDownload.variables === "docx"
              ? t("web5.exportPending")
              : t("web5.exportDocx")}
          </Button>
          <Button
            type="button"
            variant="secondary"
            disabled={exportDownload.isPending}
            onClick={() => exportDownload.mutate("excel")}
          >
            <FileSpreadsheet className="size-4" aria-hidden="true" />
            {exportDownload.isPending && exportDownload.variables === "excel"
              ? t("web5.exportPending")
              : t("web5.exportExcel")}
          </Button>
          <Button
            type="button"
            variant="secondary"
            disabled={repeatAudit.isPending}
            onClick={() => repeatAudit.mutate()}
          >
            <Repeat2 className="size-4" aria-hidden="true" />
            {repeatAudit.isPending ? t("web5.repeatPending") : t("web5.repeatAudit")}
          </Button>
        </div>
        {rerunEvaluation.data ? (
          <div className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900">
            <p>
              {t("web5.rerunComplete", {
                evaluated: formatters.number(rerunEvaluation.data.evaluated_runs),
                skipped: formatters.number(rerunEvaluation.data.skipped_runs),
              })}
            </p>
            {rerunEvaluation.data.warnings && rerunEvaluation.data.warnings.length > 0 ? (
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {rerunEvaluation.data.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}
        {rerunEvaluation.error ? (
          <p className="mt-3 text-sm text-red-700">{t("web5.rerunError")}</p>
        ) : null}
        {exportDownload.error ? (
          <p className="mt-3 text-sm text-red-700">{t("web5.exportError")}</p>
        ) : null}
        {repeatAudit.error ? (
          <p className="mt-3 text-sm text-red-700">{t("web5.repeatError")}</p>
        ) : null}
      </div>

      <div className="rounded-md border border-border bg-white p-4">
        <h3 className="text-sm font-semibold text-ink">{t("web5.modelSummaryTitle")}</h3>
        {data.model_summaries.length > 0 ? (
          <div className="mt-3 overflow-x-auto">
            <table className="min-w-full divide-y divide-border text-sm">
              <thead className="text-left text-xs uppercase text-subtle">
                <tr>
                  <th className="py-2 pr-3 font-semibold">{t("web5.model")}</th>
                  <th className="px-3 py-2 font-semibold">{t("web5.mrL1")}</th>
                  <th className="px-3 py-2 font-semibold">{t("web5.mrL2")}</th>
                  <th className="px-3 py-2 font-semibold">{t("web5.deltaMr")}</th>
                  <th className="px-3 py-2 font-semibold">{t("web5.accuracyL1")}</th>
                  <th className="px-3 py-2 font-semibold">{t("web5.accuracyL2")}</th>
                  <th className="px-3 py-2 font-semibold">{t("web5.deltaAccuracy")}</th>
                  <th className="px-3 py-2 font-semibold">{t("web5.tone")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.model_summaries.map((model) => (
                  <tr key={`${model.model_id ?? model.target_group_label}-${model.execution_provider}`}>
                    <td className="py-2 pr-3">
                      <p className="font-medium text-ink">{model.target_group_label}</p>
                      <p className="text-xs text-subtle">{model.model_id ?? "N/A"}</p>
                    </td>
                    <td className="px-3 py-2 text-subtle">
                      {formatBackendPercentage(model.mr_l1)}
                    </td>
                    <td className="px-3 py-2 text-subtle">
                      {formatBackendPercentage(model.mr_l2)}
                    </td>
                    <td className="px-3 py-2 text-subtle">
                      {formatBackendDelta(model.delta_mr)}
                    </td>
                    <td className="px-3 py-2 text-subtle">
                      {formatters.percent(model.accuracy_l1)}
                    </td>
                    <td className="px-3 py-2 text-subtle">
                      {formatters.percent(model.accuracy_l2)}
                    </td>
                    <td className="px-3 py-2 text-subtle">
                      {formatBackendDelta(
                        model.delta_accuracy === null || model.delta_accuracy === undefined
                          ? null
                          : model.delta_accuracy * 100,
                      )}
                    </td>
                    <td className="px-3 py-2 text-subtle">{formatTonePair(model)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="mt-2 text-sm text-subtle">{t("web5.modelSummaryEmpty")}</p>
        )}
      </div>
    </section>
  );
}
