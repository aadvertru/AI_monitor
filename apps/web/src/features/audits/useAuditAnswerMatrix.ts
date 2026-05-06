import { useQuery } from "@tanstack/react-query";

import { getAuditAnswerMatrix } from "../../lib/api/client";

export function auditAnswerMatrixQueryKey(auditId: number) {
  return ["audit", auditId, "answer-matrix"] as const;
}

export function useAuditAnswerMatrix(auditId: number, enabled = true) {
  return useQuery({
    queryKey: auditAnswerMatrixQueryKey(auditId),
    queryFn: () => getAuditAnswerMatrix(auditId),
    enabled: enabled && Number.isInteger(auditId) && auditId > 0,
    retry: false,
  });
}
