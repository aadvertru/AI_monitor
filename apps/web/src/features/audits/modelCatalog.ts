import { useQuery } from "@tanstack/react-query";

import { getModelCatalog } from "../../lib/api/client";

export const modelCatalogQueryKey = ["model-catalog"] as const;

export function useModelCatalog() {
  return useQuery({
    queryKey: modelCatalogQueryKey,
    queryFn: getModelCatalog,
    retry: false,
    staleTime: 24 * 60 * 60 * 1000,
  });
}
