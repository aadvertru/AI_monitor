import { useQuery } from "@tanstack/react-query";

import {
  compareAudits,
  getBrandAuditTrends,
  getComparisonCandidates,
} from "../../lib/api/client";

export function comparisonCandidatesQueryKey(auditId: number) {
  return ["audit", auditId, "comparison-candidates"] as const;
}

export function auditComparisonQueryKey(auditId: number, previousAuditId: number | null) {
  return ["audit", auditId, "compare", previousAuditId] as const;
}

export function brandAuditTrendsQueryKey(brandId: number) {
  return ["brand", brandId, "audit-trends"] as const;
}

export function useComparisonCandidates(auditId: number, enabled = true) {
  return useQuery({
    queryKey: comparisonCandidatesQueryKey(auditId),
    queryFn: () => getComparisonCandidates(auditId),
    enabled: enabled && Number.isInteger(auditId) && auditId > 0,
    retry: false,
  });
}

export function useAuditComparison(
  auditId: number,
  previousAuditId: number | null,
  enabled = true,
) {
  return useQuery({
    queryKey: auditComparisonQueryKey(auditId, previousAuditId),
    queryFn: () => compareAudits(auditId, previousAuditId as number),
    enabled:
      enabled &&
      Number.isInteger(auditId) &&
      auditId > 0 &&
      Number.isInteger(previousAuditId) &&
      Number(previousAuditId) > 0,
    retry: false,
  });
}

export function useBrandAuditTrends(brandId: number, enabled = true) {
  return useQuery({
    queryKey: brandAuditTrendsQueryKey(brandId),
    queryFn: () => getBrandAuditTrends(brandId),
    enabled: enabled && Number.isInteger(brandId) && brandId > 0,
    retry: false,
  });
}
