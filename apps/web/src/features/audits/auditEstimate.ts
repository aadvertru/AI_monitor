import { useQuery } from "@tanstack/react-query";

import { estimateAudit } from "../../lib/api/client";
import type { AuditEstimateRequest } from "../../lib/api/types";

export function auditEstimateQueryKey(payload: AuditEstimateRequest | null) {
  return ["audit-estimate", payload] as const;
}

export function useAuditEstimate(payload: AuditEstimateRequest | null, enabled: boolean) {
  return useQuery({
    queryKey: auditEstimateQueryKey(payload),
    queryFn: () => {
      if (!payload) {
        throw new Error("Audit estimate payload is missing.");
      }
      return estimateAudit(payload);
    },
    enabled: enabled && payload !== null,
    retry: false,
    staleTime: 5_000,
  });
}
