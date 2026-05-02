import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { ArrowLeft, Loader2, Plus, Sparkles } from "lucide-react";
import { useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { Field } from "../../components/ui/Field";
import { Input } from "../../components/ui/Input";
import { ApiError, createAudit } from "../../lib/api/client";
import {
  buildPayload,
  countryOptions,
  estimateAuditTokens,
  languageOptions,
  parseSeedQueries,
  providerOptions,
  queryExpansionTokenCost,
  schema,
  type CreateAuditFormInput,
  type CreateAuditFormValues,
} from "./auditSetupFormConfig";

const mockPaaQueries = [
  "PAA query 1: what are the best AI visibility monitoring tools?",
  "PAA query 2: how do brands track visibility in AI answers?",
];

const mockAiExpansionQueries = [
  "AI expansion query 1: compare AI brand monitoring platforms",
  "AI expansion query 2: tools for tracking ChatGPT brand mentions",
  "AI expansion query 3: how to measure brand visibility in LLM answers",
  "AI expansion query 4: best platforms for AI search visibility audits",
  "AI expansion query 5: monitor competitor mentions in AI responses",
  "AI expansion query 6: AI answer optimization tools for marketing teams",
  "AI expansion query 7: brand monitoring software for generative AI",
  "AI expansion query 8: measure Share of Voice in AI-generated answers",
  "AI expansion query 9: LLM visibility audit tools for B2B SaaS",
  "AI expansion query 10: track citations and sources in AI answers",
];

function mergeSeedQueries(currentValue: string | undefined, expandedQueries: string[]) {
  return [...parseSeedQueries(currentValue), ...expandedQueries]
    .reduce<string[]>((queries, query) => {
      const normalized = query.trim();
      const seen = new Set(queries.map((item) => item.toLowerCase()));
      if (normalized && !seen.has(normalized.toLowerCase())) {
        queries.push(normalized);
      }
      return queries;
    }, [])
    .join("\n");
}

function mockExpandQueries() {
  return new Promise<string[]>((resolve) => {
    window.setTimeout(() => {
      resolve([...mockPaaQueries, ...mockAiExpansionQueries]);
    }, 250);
  });
}

export function CreateAuditPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const duplicateDefaults = (location.state as { auditDefaults?: Partial<CreateAuditFormInput> } | null)
    ?.auditDefaults;
  const [isExpandingQueries, setIsExpandingQueries] = useState(false);
  const createAuditMutation = useMutation({
    mutationFn: createAudit,
    onSuccess: (response) => {
      navigate(`/audits/${response.audit_id}`, { replace: true });
    },
  });
  const {
    formState: { errors },
    control,
    getValues,
    handleSubmit,
    register,
    setValue,
  } = useForm<CreateAuditFormInput, unknown, CreateAuditFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      brandName: duplicateDefaults?.brandName ?? "",
      brandDomain: duplicateDefaults?.brandDomain ?? "",
      brandDescription: duplicateDefaults?.brandDescription ?? "",
      seedQueries: duplicateDefaults?.seedQueries ?? "",
      providers: duplicateDefaults?.providers ?? ["mock"],
      language: duplicateDefaults?.language ?? "en",
      country: duplicateDefaults?.country ?? "US",
      maxQueries: duplicateDefaults?.maxQueries ?? "",
      enableSourceIntelligence: duplicateDefaults?.enableSourceIntelligence ?? false,
      scdlLevel: duplicateDefaults?.scdlLevel ?? "L1",
    },
  });

  const watchedValues = useWatch({ control });
  const seedQueryCount = parseSeedQueries(watchedValues.seedQueries).length;
  const estimatedTokens = estimateAuditTokens(watchedValues);
  const canExpandQueries = seedQueryCount > 0 && !isExpandingQueries;

  const onSubmit = handleSubmit((values) => {
    createAuditMutation.mutate(buildPayload(values));
  });

  const expandQueries = async () => {
    if (!canExpandQueries) {
      return;
    }

    setIsExpandingQueries(true);
    try {
      const expandedQueries = await mockExpandQueries();
      setValue("seedQueries", mergeSeedQueries(getValues("seedQueries"), expandedQueries), {
        shouldDirty: true,
        shouldValidate: true,
      });
    } finally {
      setIsExpandingQueries(false);
    }
  };

  return (
    <section className="rounded-md border border-border bg-surface shadow-panel">
      <div className="flex flex-col gap-3 border-b border-border px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-ink">Create audit</h1>
          <p className="text-sm text-subtle">Manual SCDL audit setup</p>
        </div>
        <Button asChild variant="ghost">
          <Link to="/audits">
            <ArrowLeft className="size-4" aria-hidden="true" />
            Back to audits
          </Link>
        </Button>
      </div>

      <form className="space-y-6 px-5 py-5" noValidate onSubmit={onSubmit}>
        <div className="grid gap-4 md:grid-cols-2">
          <Field htmlFor="brand-name" label="Brand name" error={errors.brandName?.message}>
            <Input id="brand-name" {...register("brandName")} />
          </Field>
          <Field htmlFor="brand-domain" label="Brand domain" error={errors.brandDomain?.message}>
            <Input id="brand-domain" placeholder="example.com" {...register("brandDomain")} />
          </Field>
        </div>

        <Field
          htmlFor="brand-description"
          label="Brand description"
          error={errors.brandDescription?.message}
        >
          <textarea
            id="brand-description"
            className="min-h-24 w-full rounded-md border border-border bg-white px-3 py-2 text-sm text-ink outline-none transition-colors placeholder:text-slate-400 focus:border-brand-600 focus:ring-2 focus:ring-brand-100"
            {...register("brandDescription")}
          />
        </Field>

        <div className="space-y-3">
          <Field htmlFor="seed-queries" label="Seed queries" error={errors.seedQueries?.message}>
            <textarea
              id="seed-queries"
              className="min-h-28 w-full rounded-md border border-border bg-white px-3 py-2 text-sm text-ink outline-none transition-colors placeholder:text-slate-400 focus:border-brand-600 focus:ring-2 focus:ring-brand-100"
              placeholder={"best ai visibility tools\nbrand monitoring platforms"}
              {...register("seedQueries")}
            />
          </Field>
          <Button
            type="button"
            variant="secondary"
            disabled={!canExpandQueries}
            onClick={expandQueries}
          >
            {isExpandingQueries ? (
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
            ) : (
              <Sparkles className="size-4" aria-hidden="true" />
            )}
            {isExpandingQueries
              ? "Expanding queries..."
              : `Query expansion · ${queryExpansionTokenCost} tokens`}
          </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-[1.4fr_0.8fr]">
          <div>
            <p className="text-sm font-medium text-ink">Providers</p>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {providerOptions.map((provider) => (
                <label
                  className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm text-ink"
                  key={provider.value}
                >
                  <input
                    className="size-4 accent-brand-600"
                    type="checkbox"
                    value={provider.value}
                    {...register("providers")}
                  />
                  {provider.label}
                </label>
              ))}
            </div>
            {errors.providers?.message ? (
              <p className="mt-1 text-sm text-red-700">{errors.providers.message}</p>
            ) : null}
          </div>

          <Field htmlFor="scdl-level" label="SCDL level" error={errors.scdlLevel?.message}>
            <select
              id="scdl-level"
              className="h-10 w-full rounded-md border border-border bg-white px-3 text-sm text-ink outline-none transition-colors focus:border-brand-600 focus:ring-2 focus:ring-brand-100"
              {...register("scdlLevel")}
            >
              <option value="L1">L1 - no web access</option>
              <option value="L2">L2 - web access</option>
            </select>
          </Field>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <Field htmlFor="language" label="Language" error={errors.language?.message}>
            <select
              id="language"
              className="h-10 w-full rounded-md border border-border bg-white px-3 text-sm text-ink outline-none transition-colors focus:border-brand-600 focus:ring-2 focus:ring-brand-100"
              {...register("language")}
            >
              {languageOptions.map((language) => (
                <option key={language.value} value={language.value}>
                  {language.label}
                </option>
              ))}
            </select>
          </Field>
          <Field htmlFor="country" label="Country" error={errors.country?.message}>
            <select
              id="country"
              className="h-10 w-full rounded-md border border-border bg-white px-3 text-sm text-ink outline-none transition-colors focus:border-brand-600 focus:ring-2 focus:ring-brand-100"
              {...register("country")}
            >
              {countryOptions.map((country) => (
                <option key={country.value} value={country.value}>
                  {country.label}
                </option>
              ))}
            </select>
          </Field>
          <Field htmlFor="max-queries" label="Max queries" error={errors.maxQueries?.message}>
            <Input id="max-queries" type="number" min={1} {...register("maxQueries")} />
          </Field>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <label className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm text-ink">
            <input
              className="size-4 accent-brand-600"
              type="checkbox"
              {...register("enableSourceIntelligence")}
            />
            Source intelligence
          </label>
        </div>

        {createAuditMutation.error ? (
          <p className="text-sm text-red-700">
            {createAuditMutation.error instanceof ApiError
              ? createAuditMutation.error.message
              : "Unable to create audit."}
          </p>
        ) : null}

        <div className="flex flex-col gap-3 border-t border-border pt-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm font-medium text-ink">
            Estimated audit cost: <span className="text-brand-700">{estimatedTokens} tokens</span>
          </p>
          <Button type="submit" disabled={createAuditMutation.isPending}>
            <Plus className="size-4" aria-hidden="true" />
            {createAuditMutation.isPending ? "Creating..." : "Create audit"}
          </Button>
        </div>
      </form>
    </section>
  );
}
