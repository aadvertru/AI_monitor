import type { AuditDetail, AuditTarget, SeedQueryDraft } from "../../lib/api/types";
import type { CreateAuditFormInput } from "./auditSetupFormConfig";

function fallbackSeedQueryItems(audit: AuditDetail): SeedQueryDraft[] {
  if (audit.seed_query_items.length > 0) {
    return audit.seed_query_items;
  }

  return audit.seed_queries.map((text) => ({
    text,
    type: null,
    source: "user",
  }));
}

function fallbackModelTargets(audit: AuditDetail): AuditTarget[] {
  return audit.modelTargets ?? [];
}

export function auditDetailToFormDefaults(audit: AuditDetail): Partial<CreateAuditFormInput> {
  return {
    brandName: audit.brand_name,
    brandDomain: audit.brand_domain ?? "",
    brandDescription: audit.brand_description ?? "",
    seedQueryItems: fallbackSeedQueryItems(audit),
    modelTargets: fallbackModelTargets(audit),
    providers: audit.providers,
    language: (audit.language ?? "en") as CreateAuditFormInput["language"],
    country: (audit.country ?? "US") as CreateAuditFormInput["country"],
    maxQueries: audit.max_queries ?? "",
    enableSourceIntelligence: audit.enable_source_intelligence,
    scdlLevel: audit.scdl_level,
  };
}
