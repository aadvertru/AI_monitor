import { useTranslation } from "react-i18next";

import { ApiError } from "../../lib/api/client";
import type { AuditEstimateResponse } from "../../lib/api/types";

type AuditEstimatePanelProps = {
  estimate?: AuditEstimateResponse;
  error?: unknown;
  isLoading: boolean;
  optimisticTokens: number;
};

function estimateErrorText(error: unknown, fallback: string) {
  if (error instanceof ApiError) {
    return error.message;
  }
  return fallback;
}

export function AuditEstimatePanel({
  estimate,
  error,
  isLoading,
  optimisticTokens,
}: AuditEstimatePanelProps) {
  const { t } = useTranslation("audits");

  return (
    <div className="space-y-2 text-sm">
      <p className="font-medium text-ink">
        {t("estimate.cost")}{" "}
        <span className="text-brand-700">
          {t("estimate.tokens", { count: optimisticTokens })}
        </span>
      </p>
      {isLoading ? (
        <p className="text-subtle" role="status">
          {t("estimate.estimating")}
        </p>
      ) : null}
      {estimate ? (
        <p className={estimate.over_cap ? "font-medium text-red-700" : "text-subtle"}>
          {t("estimate.checks", { count: estimate.estimated_runs })}
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
      {error ? (
        <p className="text-red-700">
          {estimateErrorText(error, t("estimate.error"))}
        </p>
      ) : null}
    </div>
  );
}
