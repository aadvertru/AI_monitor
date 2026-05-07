import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  Archive,
  ArrowLeft,
  Copy,
  Pencil,
  Play,
  RefreshCw,
  RotateCcw,
  Trash2,
} from "lucide-react";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import {
  getAuditDetail,
  getAuditProgress,
  getAuditStatus,
  getAuditSummary,
  archiveAudit,
  cancelAuditRun,
  deleteArchivedAudit,
  retryFailedAuditRuns,
  restoreAudit,
  runAuditPipeline,
} from "../../lib/api/client";
import type {
  AuditDetail,
  AuditStatus,
  AuditSummaryResponse,
} from "../../lib/api/types";
import { AuditArchiveBadge } from "./AuditArchiveBadge";
import { AuditBreadcrumbs } from "./AuditBreadcrumbs";
import { AnswerMatrixShell } from "./AnswerMatrixShell";
import { AuditSetupPanel } from "./AuditSetupPanel";
import { AuditStatusBadge } from "./AuditStatusBadge";
import { AuditSummaryContent } from "./AuditSummaryContent";
import { AuditViewTabs } from "./AuditViewTabs";
import { ProviderDiagnostics } from "./ProviderDiagnostics";
import { Web5SummaryShell } from "./Web5SummaryShell";
import {
  archiveConfirmationMessage,
  deleteConfirmationMessage,
} from "./auditActions";
import { auditDetailToFormDefaults } from "./auditSetupFormMapping";

function detailQueryKey(auditId: number) {
  return ["audit", auditId, "detail"] as const;
}

function summaryQueryKey(auditId: number) {
  return ["audit", auditId, "summary"] as const;
}

function statusQueryKey(auditId: number) {
  return ["audit", auditId, "status"] as const;
}

const auditTerminalStatuses = new Set<AuditStatus>([
  "completed",
  "partial",
  "failed",
  "cancelled",
]);
const auditStatusPollingIntervalMs = 2000;

export function AuditDetailPage() {
  const { t } = useTranslation("audits");
  const params = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const auditId = Number(params.auditId);
  const isValidAuditId = Number.isInteger(auditId) && auditId > 0;

  const detail = useQuery({
    queryKey: detailQueryKey(auditId),
    queryFn: () => getAuditDetail(auditId),
    enabled: isValidAuditId,
    retry: false,
  });
  const summary = useQuery({
    queryKey: summaryQueryKey(auditId),
    queryFn: () => getAuditSummary(auditId),
    enabled: isValidAuditId,
    retry: false,
  });
  const baseStatus = summary.data?.status ?? detail.data?.status;
  const shouldPollStatus = isValidAuditId && baseStatus === "running";
  const progress = useQuery({
    queryKey: ["audit", auditId, "progress"],
    queryFn: () => getAuditProgress(auditId),
    enabled:
      isValidAuditId &&
      (baseStatus === "running" ||
        baseStatus === "partial" ||
        baseStatus === "failed" ||
        baseStatus === "cancelled"),
    retry: false,
    refetchInterval: (query) =>
      query.state.data?.status === "running" ? auditStatusPollingIntervalMs : false,
  });
  const status = useQuery({
    queryKey: statusQueryKey(auditId),
    queryFn: () => getAuditStatus(auditId),
    enabled: shouldPollStatus,
    retry: false,
    refetchInterval: (query) =>
      query.state.data?.status === "running" ? auditStatusPollingIntervalMs : false,
  });
  const runAuditMutation = useMutation({
    mutationFn: () => runAuditPipeline(auditId),
    onSuccess: (response) => {
      const status = response.status;
      if (status) {
        queryClient.setQueryData<AuditDetail | undefined>(detailQueryKey(auditId), (current) =>
          current ? { ...current, status } : current,
        );
      }
      queryClient.setQueryData<AuditSummaryResponse | undefined>(
        summaryQueryKey(auditId),
        (current) =>
          current
            ? {
                ...current,
                status: status ?? current.status,
              }
            : current,
      );
      void queryClient.invalidateQueries({ queryKey: ["audit", auditId] });
      void queryClient.invalidateQueries({ queryKey: ["audits"] });
    },
  });
  const cancelAuditMutation = useMutation({
    mutationFn: () => cancelAuditRun(auditId),
    onSuccess: (response) => {
      queryClient.setQueryData<AuditDetail | undefined>(detailQueryKey(auditId), (current) =>
        current ? { ...current, status: response.audit_status } : current,
      );
      queryClient.setQueryData<AuditSummaryResponse | undefined>(
        summaryQueryKey(auditId),
        (current) => (current ? { ...current, status: response.audit_status } : current),
      );
      void queryClient.invalidateQueries({ queryKey: ["audit", auditId] });
      void queryClient.invalidateQueries({ queryKey: ["audits"] });
    },
  });
  const retryFailedMutation = useMutation({
    mutationFn: () => retryFailedAuditRuns(auditId),
    onSuccess: (response) => {
      queryClient.setQueryData<AuditDetail | undefined>(detailQueryKey(auditId), (current) =>
        current ? { ...current, status: response.status } : current,
      );
      queryClient.setQueryData<AuditSummaryResponse | undefined>(
        summaryQueryKey(auditId),
        (current) => (current ? { ...current, status: response.status } : current),
      );
      void queryClient.invalidateQueries({ queryKey: ["audit", auditId] });
      void queryClient.invalidateQueries({ queryKey: ["audits"] });
    },
  });
  const archiveAuditMutation = useMutation({
    mutationFn: () => archiveAudit(auditId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["audits"] });
      navigate("/audits", { replace: true });
    },
  });
  const restoreAuditMutation = useMutation({
    mutationFn: () => restoreAudit(auditId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["audit", auditId] });
      void queryClient.invalidateQueries({ queryKey: ["audits"] });
    },
  });
  const deleteAuditMutation = useMutation({
    mutationFn: () => deleteArchivedAudit(auditId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["audits"] });
      navigate("/audits", { replace: true });
    },
  });
  const polledStatus = status.data?.status;
  useEffect(() => {
    if (!polledStatus || !auditTerminalStatuses.has(polledStatus)) {
      return;
    }

    queryClient.setQueryData<AuditDetail | undefined>(detailQueryKey(auditId), (current) =>
      current ? { ...current, status: polledStatus } : current,
    );
    queryClient.setQueryData<AuditSummaryResponse | undefined>(
      summaryQueryKey(auditId),
      (current) => (current ? { ...current, status: polledStatus } : current),
    );
    void queryClient.invalidateQueries({ queryKey: ["audit", auditId] });
    void queryClient.invalidateQueries({ queryKey: ["audits"] });
  }, [auditId, polledStatus, queryClient]);

  const isLoading = detail.isLoading || summary.isLoading;
  const hasError = detail.isError || summary.isError || !isValidAuditId;
  const currentStatus = status.data?.status ?? baseStatus;
  const isRunning = currentStatus === "running";
  const progressData = progress.data;
  const hasFailedRuns = Boolean(progressData && (progressData.failed_runs > 0 || progressData.skipped_runs > 0));
  const canEdit = currentStatus === "created";
  const isArchived = Boolean(detail.data?.archived_at);
  const statusDiagnostics = status.data?.provider_diagnostics ?? [];
  const progressDiagnostics = progress.data?.provider_diagnostics ?? [];
  const hasActionDiagnostics = statusDiagnostics.length > 0 || progressDiagnostics.length > 0;

  const refresh = () => {
    void detail.refetch();
    void summary.refetch();
  };
  const errorMessage = (error: unknown) =>
    error instanceof Error ? error.message : t("errors.start");

  if (isLoading) {
    return (
      <section className="rounded-md border border-border bg-surface px-5 py-10 text-sm text-subtle shadow-panel" role="status">
        {t("errors.loadingAudit")}
      </section>
    );
  }

  if (hasError || !detail.data || !summary.data) {
    return (
      <section className="rounded-md border border-border bg-surface p-5 shadow-panel">
        <div className="flex items-center gap-2 text-sm text-red-700">
          <AlertTriangle className="size-4" aria-hidden="true" />
          {t("errors.auditUnavailable")}
        </div>
        <Button asChild className="mt-4" variant="secondary">
          <Link to="/audits">{t("backToAudits")}</Link>
        </Button>
      </section>
    );
  }

  return (
    <section className="rounded-md border border-border bg-surface shadow-panel">
      <div className="flex flex-col gap-3 border-b border-border px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <AuditBreadcrumbs auditId={auditId} auditNumber={detail.data.audit_number} />
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-xl font-semibold text-ink">{detail.data.brand_name}</h1>
            <AuditStatusBadge status={summary.data.status} />
            {isArchived ? <AuditArchiveBadge /> : null}
          </div>
          <p className="mt-1 text-sm text-subtle">
            Audit #{detail.data.audit_number}
            {detail.data.brand_domain ? ` · ${detail.data.brand_domain}` : ""}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="ghost">
            <Link to="/audits">
              <ArrowLeft className="size-4" aria-hidden="true" />
              {t("back")}
            </Link>
          </Button>
          <Button type="button" variant="secondary" onClick={refresh}>
            <RefreshCw className="size-4" aria-hidden="true" />
            {t("refresh")}
          </Button>
          {canEdit ? (
            <Button asChild variant="secondary">
              <Link to={`/audits/${auditId}/edit`}>
                <Pencil className="size-4" aria-hidden="true" />
                {t("editSetup")}
              </Link>
            </Button>
          ) : null}
          <Button asChild variant="secondary">
            <Link
              to="/audits/new"
              state={{ auditDefaults: auditDetailToFormDefaults(detail.data) }}
            >
              <Copy className="size-4" aria-hidden="true" />
              {t("duplicateAudit")}
            </Link>
          </Button>
          {isArchived ? (
            <>
              <Button
                type="button"
                variant="secondary"
                onClick={() => restoreAuditMutation.mutate()}
              >
                <RotateCcw className="size-4" aria-hidden="true" />
                {t("restore")}
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  if (window.confirm(deleteConfirmationMessage)) {
                    deleteAuditMutation.mutate();
                  }
                }}
              >
                <Trash2 className="size-4" aria-hidden="true" />
                {t("deletePermanently")}
              </Button>
            </>
          ) : (
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                if (window.confirm(archiveConfirmationMessage)) {
                  archiveAuditMutation.mutate();
                }
              }}
            >
              <Archive className="size-4" aria-hidden="true" />
              {t("archive")}
            </Button>
          )}
          <Button
            type="button"
            disabled={isArchived || isRunning || runAuditMutation.isPending}
            onClick={() => runAuditMutation.mutate()}
          >
            <Play className="size-4" aria-hidden="true" />
            {runAuditMutation.isPending
              ? t("starting")
              : isRunning
                ? t("running")
                : t("startAudit")}
          </Button>
          {isRunning ? (
            <Button
              type="button"
              variant="secondary"
              disabled={cancelAuditMutation.isPending}
              onClick={() => {
                if (window.confirm(t("progress.cancelConfirm"))) {
                  cancelAuditMutation.mutate();
                }
              }}
            >
              {cancelAuditMutation.isPending ? t("progress.cancelling") : t("progress.cancel")}
            </Button>
          ) : null}
          {(currentStatus === "partial" ||
            currentStatus === "failed" ||
            currentStatus === "cancelled") &&
          hasFailedRuns ? (
            <Button
              type="button"
              variant="secondary"
              disabled={retryFailedMutation.isPending}
              onClick={() => retryFailedMutation.mutate()}
            >
              {retryFailedMutation.isPending ? t("progress.retrying") : t("progress.retryFailed")}
            </Button>
          ) : null}
        </div>
      </div>

      <AuditViewTabs auditId={auditId} active="summary" />

      {runAuditMutation.error ? (
        <p className="border-b border-border px-5 py-3 text-sm text-red-700">
          {errorMessage(runAuditMutation.error)}
        </p>
      ) : null}
      {cancelAuditMutation.error || retryFailedMutation.error ? (
        <p className="border-b border-border px-5 py-3 text-sm text-red-700">
          {errorMessage(cancelAuditMutation.error ?? retryFailedMutation.error)}
        </p>
      ) : null}
      {progressData ? (
        <div className="border-b border-border px-5 py-4">
          <div className="grid gap-3 text-sm sm:grid-cols-3 lg:grid-cols-6">
            <div>
              <p className="text-xs font-semibold uppercase text-subtle">{t("progress.total")}</p>
              <p className="text-lg font-semibold text-ink">{progressData.total_runs}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase text-subtle">{t("progress.completed")}</p>
              <p className="text-lg font-semibold text-ink">{progressData.completed_runs}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase text-subtle">{t("progress.failed")}</p>
              <p className="text-lg font-semibold text-ink">{progressData.failed_runs}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase text-subtle">{t("progress.queued")}</p>
              <p className="text-lg font-semibold text-ink">{progressData.queued_runs}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase text-subtle">{t("progress.running")}</p>
              <p className="text-lg font-semibold text-ink">{progressData.running_runs}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase text-subtle">{t("progress.percent")}</p>
              <p className="text-lg font-semibold text-ink">{progressData.percent_complete}%</p>
            </div>
          </div>
        </div>
      ) : progress.isError ? (
        <p className="border-b border-border px-5 py-3 text-sm text-red-700">
          {t("progress.error")}
        </p>
      ) : null}
      {hasActionDiagnostics ? (
        <div className="space-y-3 border-b border-border px-5 py-3">
          <ProviderDiagnostics diagnostics={progressDiagnostics} compact />
      <ProviderDiagnostics diagnostics={statusDiagnostics} compact />
        </div>
      ) : null}
      <AuditSetupPanel audit={detail.data} />
      <Web5SummaryShell auditId={auditId} audit={detail.data} />
      <AnswerMatrixShell auditId={auditId} auditStatus={currentStatus} />
      <AuditSummaryContent auditId={auditId} summary={summary.data} />
    </section>
  );
}
