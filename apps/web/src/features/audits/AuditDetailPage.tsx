import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, Play, RefreshCw } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { getAuditDetail, getAuditStatus, runAudit } from "../../lib/api/client";
import type { AuditRunTriggerResponse, AuditStatusResponse } from "../../lib/api/types";
import { AuditStatusBadge } from "./AuditStatusBadge";

function formatTimestamp(value: string | null) {
  if (!value) {
    return "Not updated yet";
  }
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function MetadataItem({ label, value }: { label: string; value: string | number | null }) {
  return (
    <div className="rounded-md border border-border bg-white px-3 py-2">
      <dt className="text-xs font-medium uppercase text-subtle">{label}</dt>
      <dd className="mt-1 text-sm text-ink">{value ?? "Not set"}</dd>
    </div>
  );
}

function statusQueryKey(auditId: number) {
  return ["audit", auditId, "status"] as const;
}

function detailQueryKey(auditId: number) {
  return ["audit", auditId, "detail"] as const;
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
  const status = useQuery({
    queryKey: statusQueryKey(auditId),
    queryFn: () => getAuditStatus(auditId),
    enabled: isValidAuditId,
    retry: false,
  });
  const runAuditMutation = useMutation({
    mutationFn: () => runAudit(auditId),
    onSuccess: (response: AuditRunTriggerResponse) => {
      queryClient.setQueryData<AuditStatusResponse | undefined>(
        statusQueryKey(auditId),
        (current) =>
          current
            ? { ...current, status: response.status }
            : {
                audit_id: response.audit_id,
                status: response.status,
                scdl_level: detail.data?.scdl_level ?? "L1",
                total_runs: response.total_jobs,
                completed_runs: 0,
                failed_runs: 0,
                completion_ratio: 0,
                updated_at: new Date().toISOString(),
              },
      );
    },
  });

  const isLoading = detail.isLoading || status.isLoading;
  const hasError = detail.isError || status.isError || !isValidAuditId;
  const currentStatus = status.data?.status ?? detail.data?.status;
  const isRunning = currentStatus === "running";

  const refresh = () => {
    void detail.refetch();
    void status.refetch();
  };

  if (isLoading) {
    return (
      <section className="rounded-md border border-border bg-surface px-5 py-10 text-sm text-subtle shadow-panel" role="status">
        Loading audit...
      </section>
    );
  }

  if (hasError || !detail.data || !status.data) {
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
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-xl font-semibold text-ink">{detail.data.brand_name}</h1>
            <AuditStatusBadge status={status.data.status} />
          </div>
          <p className="mt-1 text-sm text-subtle">
            Audit #{detail.data.audit_id}
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

      <div className="grid gap-5 px-5 py-5 lg:grid-cols-[1.4fr_0.8fr]">
        <div>
          <h2 className="text-sm font-semibold text-ink">Metadata</h2>
          <dl className="mt-3 grid gap-3 md:grid-cols-2">
            <MetadataItem label="SCDL level" value={detail.data.scdl_level} />
            <MetadataItem label="Providers" value={detail.data.providers.join(", ")} />
            <MetadataItem label="Runs per query" value={detail.data.runs_per_query} />
            <MetadataItem label="Created" value={formatTimestamp(detail.data.created_at)} />
            <MetadataItem label="Updated" value={formatTimestamp(detail.data.updated_at)} />
            <MetadataItem label="Language" value={detail.data.language} />
            <MetadataItem label="Country" value={detail.data.country} />
            <MetadataItem label="Locale" value={detail.data.locale} />
          </dl>
          {detail.data.brand_description ? (
            <p className="mt-4 rounded-md border border-border bg-white px-3 py-2 text-sm text-ink">
              {detail.data.brand_description}
            </p>
          ) : null}
        </div>

        <div>
          <h2 className="text-sm font-semibold text-ink">Run status</h2>
          <dl className="mt-3 grid gap-3">
            <MetadataItem label="Total runs" value={status.data.total_runs} />
            <MetadataItem label="Completed runs" value={status.data.completed_runs} />
            <MetadataItem label="Failed runs" value={status.data.failed_runs} />
            <MetadataItem
              label="Completion"
              value={`${Math.round(status.data.completion_ratio * 100)}%`}
            />
          </dl>
          {runAuditMutation.error ? (
            <p className="mt-3 text-sm text-red-700">Unable to start audit.</p>
          ) : null}
        </div>
      </div>

      <div className="flex flex-wrap gap-2 border-t border-border px-5 py-4">
        <Button asChild variant="secondary">
          <Link to={`/audits/${auditId}/summary`}>Summary</Link>
        </Button>
        <Button asChild variant="secondary">
          <Link to={`/audits/${auditId}/results`}>Results</Link>
        </Button>
        <Button asChild variant="secondary">
          <Link to={`/audits/${auditId}/sources`}>Sources</Link>
        </Button>
      </div>
    </section>
  );
}
