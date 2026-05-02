import type { AuditDetail } from "../../lib/api/types";
import type { CreateAuditFormInput } from "./auditSetupFormConfig";

export function auditDetailToFormDefaults(audit: AuditDetail): Partial<CreateAuditFormInput> {
  return {
    brandName: audit.brand_name,
    brandDomain: audit.brand_domain ?? "",
    brandDescription: audit.brand_description ?? "",
    seedQueries: audit.seed_queries.join("\n"),
    providers: audit.providers,
    language: (audit.language ?? "en") as CreateAuditFormInput["language"],
    country: (audit.country ?? "US") as CreateAuditFormInput["country"],
    maxQueries: audit.max_queries ?? "",
    enableSourceIntelligence: audit.enable_source_intelligence,
    scdlLevel: audit.scdl_level,
  };
}
