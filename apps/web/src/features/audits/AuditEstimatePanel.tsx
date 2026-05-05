import { ApiError } from "../../lib/api/client";
import type { AuditEstimateResponse } from "../../lib/api/types";

type AuditEstimatePanelProps = {
  estimate?: AuditEstimateResponse;
  error?: unknown;
  isLoading: boolean;
  optimisticTokens: number;
};

function estimateErrorText(error: unknown) {
  if (error instanceof ApiError) {
    return error.message;
  }
  return "Unable to estimate audit.";
}

export function AuditEstimatePanel({
  estimate,
  error,
  isLoading,
  optimisticTokens,
}: AuditEstimatePanelProps) {
  return (
    <div className="space-y-2 text-sm">
      <p className="font-medium text-ink">
        Estimated audit cost: <span className="text-brand-700">{optimisticTokens} tokens</span>
      </p>
      {isLoading ? (
        <p className="text-subtle" role="status">
          Estimating checks...
        </p>
      ) : null}
      {estimate ? (
        <p className={estimate.over_cap ? "font-medium text-red-700" : "text-subtle"}>
          This audit will run {estimate.estimated_runs} checks.
        </p>
      ) : null}
      {(estimate?.violations ?? []).map((violation) => (
        <p className="text-red-700" key={violation.code}>
          {violation.message}
        </p>
      ))}
      {(estimate?.warnings ?? []).map((warning) => (
        <p className="text-amber-700" key={warning}>
          {warning}
        </p>
      ))}
      {error ? <p className="text-red-700">{estimateErrorText(error)}</p> : null}
    </div>
  );
}
