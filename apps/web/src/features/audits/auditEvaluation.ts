import { useMutation, useQueryClient } from "@tanstack/react-query";

import { rerunAuditEvaluation } from "../../lib/api/client";

export const auditSummaryV2QueryKey = (auditId: number) =>
  ["audit", auditId, "summary-v2"] as const;
export const auditAnswerMatrixQueryKey = (auditId: number) =>
  ["audit", auditId, "answer-matrix"] as const;
export const auditStatusQueryKey = (auditId: number) => ["audit", auditId, "status"] as const;
export const auditDetailQueryKey = (auditId: number) => ["audit", auditId] as const;

export const safeRerunEvaluationErrorMessage = "Could not rerun fact-checking.";

export function useRerunAuditEvaluation(auditId: number) {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: () => rerunAuditEvaluation(auditId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: auditSummaryV2QueryKey(auditId) });
      void queryClient.invalidateQueries({ queryKey: auditAnswerMatrixQueryKey(auditId) });
      void queryClient.invalidateQueries({ queryKey: auditStatusQueryKey(auditId) });
      void queryClient.invalidateQueries({ queryKey: auditDetailQueryKey(auditId) });
    },
  });

  return {
    ...mutation,
    safeErrorMessage: mutation.isError ? safeRerunEvaluationErrorMessage : null,
  };
}
