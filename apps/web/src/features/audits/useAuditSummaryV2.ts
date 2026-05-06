import { useQuery } from "@tanstack/react-query";

import { getAuditSummaryV2 } from "../../lib/api/client";

export function auditSummaryV2QueryKey(auditId: number) {
  return ["audit", auditId, "summary-v2"] as const;
}

export function useAuditSummaryV2(auditId: number, enabled = true) {
  return useQuery({
    queryKey: auditSummaryV2QueryKey(auditId),
    queryFn: () => getAuditSummaryV2(auditId),
    enabled: enabled && Number.isInteger(auditId) && auditId > 0,
    retry: false,
  });
}
