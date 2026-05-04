import { z } from "zod";

import type {
  AuditCreateRequest,
  GeneratedSeedQuerySuggestion,
  SCDLLevel,
  SeedQueryDraft,
  SeedQueryType,
} from "../../lib/api/types";

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

export const brandDescriptionMaxLength = 500;
export const invalidDomainMessage = "Invalid domain format";
export const maxSeedQueryCount = 20;

const queryTypeValues = [
  "brand_direct",
  "category_discovery",
  "recommendation",
  "comparison",
  "alternative",
  "problem_solution",
] as const;

export const queryTypeOptions: { label: string; value: SeedQueryType }[] = [
  { label: "Brand direct", value: "brand_direct" },
  { label: "Category discovery", value: "category_discovery" },
  { label: "Recommendation", value: "recommendation" },
  { label: "Comparison", value: "comparison" },
  { label: "Alternative", value: "alternative" },
  { label: "Problem-solution", value: "problem_solution" },
];

export const emptySeedQueryItem: SeedQueryDraft = {
  text: "",
  type: null,
  source: "user",
};

type SeedQueryFormItem = {
  text?: string;
  type?: SeedQueryType | null;
  source?: "user" | "ai";
};
const brandDomainPattern =
  /^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/;

export function localeFrom(language: string, country: string) {
  return `${language}-${country}`;
}

export function normalizeBrandDomain(value: string) {
  return value.trim().toLowerCase().replace(/\/+$/, "");
}

function isValidBrandDomain(value: string) {
  const normalized = normalizeBrandDomain(value);
  return (
    normalized.length > 0 &&
    !normalized.includes("://") &&
    !normalized.includes("/") &&
    !normalized.includes("?") &&
    !normalized.includes("#") &&
    brandDomainPattern.test(normalized)
  );
}

const seedQueryItemSchema = z.object({
  text: z
    .string()
    .max(300, "Seed query must be 300 characters or fewer.")
    .refine(
      (value) => value.trim().length === 0 || value.trim().length >= 3,
      "Seed query must be at least 3 characters.",
    )
    .default(""),
  type: z
    .enum(queryTypeValues)
    .nullable()
    .optional(),
  source: z.enum(["user", "ai"]).optional(),
});

export const schema = z
  .object({
    brandName: z.string().trim().min(1, "Enter a brand name."),
    brandDomain: z
      .string()
      .trim()
      .min(1, "Enter a brand domain.")
      .refine(isValidBrandDomain, invalidDomainMessage)
      .transform(normalizeBrandDomain),
    brandDescription: z
      .string()
      .trim()
      .max(brandDescriptionMaxLength, `Brand description must be ${brandDescriptionMaxLength} characters or fewer.`)
      .optional(),
    seedQueryItems: z
      .array(seedQueryItemSchema)
      .max(maxSeedQueryCount, `Use ${maxSeedQueryCount} seed queries or fewer.`)
      .optional(),
    providers: z.array(z.string()).min(1, "Select at least one provider."),
    language: z.enum(languageOptions.map((option) => option.value)),
    country: z.enum(countryOptions.map((option) => option.value)),
    maxQueries: z.union([z.literal(""), z.coerce.number().int().positive()]).optional(),
    enableSourceIntelligence: z.boolean(),
    scdlLevel: z.enum(["L1", "L2"]),
  })
  .superRefine((values, context) => {
    if (parseSeedQueryItems(values.seedQueryItems).length === 0) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Add at least one seed query.",
        path: ["seedQueryItems"],
      });
    }
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

function normalizeSeedQueryForDedupe(value: string) {
  return value.trim().toLowerCase().replace(/\s+/g, " ");
}

export function seedQueryItemsFromText(value?: string): SeedQueryDraft[] {
  const queries = parseSeedQueries(value);
  return queries.length > 0
    ? queries.map((text) => ({ text, type: null, source: "user" }))
    : [{ ...emptySeedQueryItem }];
}

export function parseSeedQueryItems(value?: SeedQueryFormItem[]) {
  const seen = new Set<string>();
  const queries: SeedQueryDraft[] = [];

  for (const item of value ?? []) {
    const text = (item.text ?? "").trim().replace(/\s+/g, " ");
    const normalized = normalizeSeedQueryForDedupe(text);
    if (text && !seen.has(normalized)) {
      seen.add(normalized);
      queries.push({
        text,
        type: item.type ?? null,
        source: item.source ?? "user",
      });
    }
  }

  return queries;
}

export type AppendGeneratedSeedQueriesResult = {
  queries: SeedQueryDraft[];
  duplicateCount: number;
  limitSkipped: number;
};

export function appendGeneratedSeedQueries(
  currentQueries: SeedQueryFormItem[] | undefined,
  suggestions: GeneratedSeedQuerySuggestion[],
  maxQueries = maxSeedQueryCount,
): AppendGeneratedSeedQueriesResult {
  const queries = parseSeedQueryItems(currentQueries);
  const seen = new Set(queries.map((query) => normalizeSeedQueryForDedupe(query.text)));
  let duplicateCount = 0;
  let limitSkipped = 0;

  for (const suggestion of suggestions) {
    const text = suggestion.text.trim().replace(/\s+/g, " ");
    const normalized = normalizeSeedQueryForDedupe(text);
    if (!text) {
      continue;
    }
    if (seen.has(normalized)) {
      duplicateCount += 1;
      continue;
    }

    if (queries.length >= maxQueries) {
      limitSkipped += 1;
      continue;
    }

    seen.add(normalized);
    queries.push({
      text,
      type: suggestion.type,
      source: "ai",
    });
  }

  return { queries, duplicateCount, limitSkipped };
}

type EstimateValues = {
  enableSourceIntelligence?: boolean;
  maxQueries?: unknown;
  providers?: string[];
  scdlLevel?: "L1" | "L2";
  seedQueries?: string;
  seedQueryItems?: SeedQueryFormItem[];
};

export function estimateAuditTokens(values: EstimateValues) {
  const queryCount = values.seedQueryItems
    ? parseSeedQueryItems(values.seedQueryItems).length
    : parseSeedQueries(values.seedQueries).length;
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
  const sourceIntelligenceAddon = values.scdlLevel === "L2" && values.enableSourceIntelligence
    ? effectiveQueries * selectedProviders * 5
    : 0;

  return Math.round(base * scdlMultiplier + sourceIntelligenceAddon);
}

export function buildPayload(values: CreateAuditFormValues): AuditCreateRequest {
  const seedQueryItems = parseSeedQueryItems(values.seedQueryItems);
  return {
    brand_name: values.brandName.trim(),
    brand_domain: optionalText(normalizeBrandDomain(values.brandDomain)),
    brand_description: optionalText(values.brandDescription),
    providers: values.providers,
    runs_per_query: 1,
    seed_query_items: seedQueryItems.length > 0 ? seedQueryItems : null,
    language: optionalText(values.language),
    country: optionalText(values.country),
    locale: localeFrom(values.language, values.country),
    max_queries:
      values.maxQueries === "" || values.maxQueries === undefined ? null : values.maxQueries,
    enable_query_expansion: false,
    enable_source_intelligence:
      values.scdlLevel === "L2" ? values.enableSourceIntelligence : false,
    follow_up_depth: 0,
    scdl_level: values.scdlLevel as SCDLLevel,
  };
}
