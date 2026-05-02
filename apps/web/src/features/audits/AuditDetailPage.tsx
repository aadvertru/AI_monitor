import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, Copy, Pencil, Play, RefreshCw } from "lucide-react";
import { useEffect } from "react";
import { Link, useParams } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import {
  getAuditDetail,
  getAuditStatus,
  getAuditSummary,
  runAuditPipeline,
} from "../../lib/api/client";
import type {
  AuditDetail,
  AuditStatus,
  AuditPipelineRunResponse,
  AuditSummaryResponse,
} from "../../lib/api/types";
import { AuditBreadcrumbs } from "./AuditBreadcrumbs";
import { AuditSetupPanel } from "./AuditSetupPanel";
import { AuditStatusBadge } from "./AuditStatusBadge";
import { AuditSummaryContent } from "./AuditSummaryContent";
import { AuditViewTabs } from "./AuditViewTabs";
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

const auditTerminalStatuses = new Set<AuditStatus>(["completed", "partial", "failed"]);
const auditStatusPollingIntervalMs = 2000;

function pipelineStatus(response: AuditPipelineRunResponse) {
  return response.final_audit_status ?? response.post_processing?.audit_status ?? null;
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Unable to start audit.";
}

export function AuditDetailPage() {
  const params = useParams();
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
      const status = pipelineStatus(response);
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
                total_runs: Math.max(current.total_runs, response.scheduling.total_jobs),
              }
            : current,
      );
      void queryClient.invalidateQueries({ queryKey: ["audit", auditId] });
      void queryClient.invalidateQueries({ queryKey: ["audits"] });
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
  const canEdit = currentStatus === "created";

  const refresh = () => {
    void detail.refetch();
    void summary.refetch();
  };

  if (isLoading) {
    return (
      <section className="rounded-md border border-border bg-surface px-5 py-10 text-sm text-subtle shadow-panel" role="status">
        Loading audit...
      </section>
    );
  }

  if (hasError || !detail.data || !summary.data) {
    return (
      <section className="rounded-md border border-border bg-surface p-5 shadow-panel">
        <div className="flex items-center gap-2 text-sm text-red-700">
          <AlertTriangle className="size-4" aria-hidden="true" />
          Audit unavailable.
        </div>
        <Button asChild className="mt-4" variant="secondary">
          <Link to="/audits">Back to audits</Link>
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
              Back
            </Link>
          </Button>
          <Button type="button" variant="secondary" onClick={refresh}>
            <RefreshCw className="size-4" aria-hidden="true" />
            Refresh
          </Button>
          {canEdit ? (
            <Button asChild variant="secondary">
              <Link to={`/audits/${auditId}/edit`}>
                <Pencil className="size-4" aria-hidden="true" />
                Edit setup
              </Link>
            </Button>
          ) : null}
          <Button asChild variant="secondary">
            <Link
              to="/audits/new"
              state={{ auditDefaults: auditDetailToFormDefaults(detail.data) }}
            >
              <Copy className="size-4" aria-hidden="true" />
              Duplicate audit
            </Link>
          </Button>
          <Button
            type="button"
            disabled={isRunning || runAuditMutation.isPending}
            onClick={() => runAuditMutation.mutate()}
          >
            <Play className="size-4" aria-hidden="true" />
            {runAuditMutation.isPending ? "Starting" : isRunning ? "Running" : "Start audit"}
          </Button>
        </div>
      </div>

      <AuditViewTabs auditId={auditId} active="summary" />

      {runAuditMutation.error ? (
        <p className="border-b border-border px-5 py-3 text-sm text-red-700">
          {errorMessage(runAuditMutation.error)}
        </p>
      ) : null}
      <AuditSetupPanel audit={detail.data} />
      <AuditSummaryContent auditId={auditId} summary={summary.data} />
    </section>
  );
}
