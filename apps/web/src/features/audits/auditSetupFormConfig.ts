import { z } from "zod";

import type { AuditCreateRequest, SCDLLevel } from "../../lib/api/types";

export const providerOptions = [
  { label: "Mock", value: "mock" },
  { label: "OpenAI", value: "openai" },
  { label: "Anthropic", value: "anthropic" },
  { label: "Gemini", value: "gemini" },
] as const;

export const languageOptions = [
  { label: "English", value: "en" },
  { label: "Ukrainian", value: "uk" },
  { label: "Russian", value: "ru" },
  { label: "Spanish", value: "es" },
  { label: "German", value: "de" },
  { label: "French", value: "fr" },
] as const;

export const countryOptions = [
  { label: "United States", value: "US" },
  { label: "Ukraine", value: "UA" },
  { label: "United Kingdom", value: "GB" },
  { label: "Canada", value: "CA" },
  { label: "Germany", value: "DE" },
  { label: "France", value: "FR" },
] as const;

export const queryExpansionTokenCost = 15;

export function localeFrom(language: string, country: string) {
  return `${language}-${country}`;
}

export const schema = z.object({
  brandName: z.string().trim().min(1, "Enter a brand name."),
  brandDomain: z.string().trim().min(1, "Enter a brand domain."),
  brandDescription: z.string().trim().optional(),
  seedQueries: z.string().trim().optional(),
  providers: z.array(z.string()).min(1, "Select at least one provider."),
  language: z.enum(languageOptions.map((option) => option.value)),
  country: z.enum(countryOptions.map((option) => option.value)),
  maxQueries: z.union([z.literal(""), z.coerce.number().int().positive()]).optional(),
  enableSourceIntelligence: z.boolean(),
  scdlLevel: z.enum(["L1", "L2"]),
});

export type CreateAuditFormInput = z.input<typeof schema>;
export type CreateAuditFormValues = z.output<typeof schema>;

function optionalText(value?: string) {
  const normalized = value?.trim();
  return normalized ? normalized : null;
}

export function parseSeedQueries(value?: string) {
  const seen = new Set<string>();
  const queries: string[] = [];

  for (const line of value?.split(/\r?\n/) ?? []) {
    const query = line.trim();
    if (query && !seen.has(query.toLowerCase())) {
      seen.add(query.toLowerCase());
      queries.push(query);
    }
  }

  return queries;
}

type EstimateValues = {
  enableSourceIntelligence?: boolean;
  maxQueries?: unknown;
  providers?: string[];
  scdlLevel?: "L1" | "L2";
  seedQueries?: string;
};

export function estimateAuditTokens(values: EstimateValues) {
  const queryCount = parseSeedQueries(values.seedQueries).length;
  const parsedMaxQueries =
    typeof values.maxQueries === "number"
      ? values.maxQueries
      : typeof values.maxQueries === "string" && values.maxQueries.trim()
        ? Number(values.maxQueries)
        : null;
  const maxQueries =
    typeof parsedMaxQueries === "number" && Number.isFinite(parsedMaxQueries)
      ? parsedMaxQueries
      : null;
  const effectiveQueries = maxQueries ? Math.min(queryCount, maxQueries) : queryCount;
  const selectedProviders = values.providers?.length ?? 0;
  const base = effectiveQueries * selectedProviders * 10;
  const scdlMultiplier = values.scdlLevel === "L2" ? 1.5 : 1;
  const sourceIntelligenceAddon = values.enableSourceIntelligence
    ? effectiveQueries * selectedProviders * 5
    : 0;

  return Math.round(base * scdlMultiplier + sourceIntelligenceAddon);
}

export function buildPayload(values: CreateAuditFormValues): AuditCreateRequest {
  const seedQueries = parseSeedQueries(values.seedQueries);
  return {
    brand_name: values.brandName.trim(),
    brand_domain: optionalText(values.brandDomain),
    brand_description: optionalText(values.brandDescription),
    providers: values.providers,
    runs_per_query: 1,
    seed_queries: seedQueries.length > 0 ? seedQueries : null,
    language: optionalText(values.language),
    country: optionalText(values.country),
    locale: localeFrom(values.language, values.country),
    max_queries:
      values.maxQueries === "" || values.maxQueries === undefined ? null : values.maxQueries,
    enable_query_expansion: false,
    enable_source_intelligence: values.enableSourceIntelligence,
    follow_up_depth: 0,
    scdl_level: values.scdlLevel as SCDLLevel,
  };
}
