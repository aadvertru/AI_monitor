import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, Play, RefreshCw } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { getAuditDetail, getAuditSummary, runAudit } from "../../lib/api/client";
import type { AuditRunTriggerResponse, AuditSummaryResponse } from "../../lib/api/types";
import { AuditBreadcrumbs } from "./AuditBreadcrumbs";
import { AuditStatusBadge } from "./AuditStatusBadge";
import { AuditSummaryContent } from "./AuditSummaryContent";
import { AuditViewTabs } from "./AuditViewTabs";

function detailQueryKey(auditId: number) {
  return ["audit", auditId, "detail"] as const;
}

function summaryQueryKey(auditId: number) {
  return ["audit", auditId, "summary"] as const;
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
  const runAuditMutation = useMutation({
    mutationFn: () => runAudit(auditId),
    onSuccess: (response: AuditRunTriggerResponse) => {
      queryClient.setQueryData<AuditSummaryResponse | undefined>(
        summaryQueryKey(auditId),
        (current) =>
          current
            ? {
                ...current,
                status: response.status,
                total_runs: response.total_jobs,
                completion_ratio: response.total_jobs === 0 ? 0 : current.completion_ratio,
              }
            : current,
      );
      void queryClient.invalidateQueries({ queryKey: summaryQueryKey(auditId) });
    },
  });

  const isLoading = detail.isLoading || summary.isLoading;
  const hasError = detail.isError || summary.isError || !isValidAuditId;
  const currentStatus = summary.data?.status ?? detail.data?.status;
  const isRunning = currentStatus === "running";

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
          <Button
            type="button"
            disabled={isRunning || runAuditMutation.isPending}
            onClick={() => runAuditMutation.mutate()}
          >
            <Play className="size-4" aria-hidden="true" />
            {isRunning ? "Running" : "Start audit"}
          </Button>
        </div>
      </div>

      <AuditViewTabs auditId={auditId} active="summary" />

      {runAuditMutation.error ? (
        <p className="border-b border-border px-5 py-3 text-sm text-red-700">Unable to start audit.</p>
      ) : null}
      <AuditSummaryContent auditId={auditId} summary={summary.data} />
    </section>
  );
}
