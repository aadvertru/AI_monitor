import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { ArrowLeft, Plus } from "lucide-react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { Button } from "../../components/ui/Button";
import { Field } from "../../components/ui/Field";
import { Input } from "../../components/ui/Input";
import { ApiError, createAudit } from "../../lib/api/client";
import type { AuditCreateRequest, SCDLLevel } from "../../lib/api/types";

const providerOptions = [
  { label: "Mock", value: "mock" },
  { label: "OpenAI", value: "openai" },
  { label: "Anthropic", value: "anthropic" },
  { label: "Gemini", value: "gemini" },
] as const;

const schema = z.object({
  brandName: z.string().trim().min(1, "Enter a brand name."),
  brandDomain: z.string().trim().optional(),
  brandDescription: z.string().trim().optional(),
  seedQueries: z.string().trim().optional(),
  providers: z.array(z.string()).min(1, "Select at least one provider."),
  runsPerQuery: z.coerce
    .number({ error: "Enter a number of runs." })
    .int("Runs per query must be a whole number.")
    .min(1, "Runs per query must be at least 1.")
    .max(5, "Runs per query cannot exceed 5."),
  language: z.string().trim().optional(),
  country: z.string().trim().optional(),
  locale: z.string().trim().optional(),
  maxQueries: z.union([z.literal(""), z.coerce.number().int().positive()]).optional(),
  enableQueryExpansion: z.boolean(),
  enableSourceIntelligence: z.boolean(),
  followUpDepth: z.coerce.number().int().min(0).max(1),
  scdlLevel: z.enum(["L1", "L2"]),
});

type CreateAuditFormInput = z.input<typeof schema>;
type CreateAuditFormValues = z.output<typeof schema>;

function optionalText(value?: string) {
  const normalized = value?.trim();
  return normalized ? normalized : null;
}

function parseSeedQueries(value?: string) {
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

function buildPayload(values: CreateAuditFormValues): AuditCreateRequest {
  const seedQueries = parseSeedQueries(values.seedQueries);
  return {
    brand_name: values.brandName.trim(),
    brand_domain: optionalText(values.brandDomain),
    brand_description: optionalText(values.brandDescription),
    providers: values.providers,
    runs_per_query: values.runsPerQuery,
    seed_queries: seedQueries.length > 0 ? seedQueries : null,
    language: optionalText(values.language),
    country: optionalText(values.country),
    locale: optionalText(values.locale),
    max_queries:
      values.maxQueries === "" || values.maxQueries === undefined ? null : values.maxQueries,
    enable_query_expansion: values.enableQueryExpansion,
    enable_source_intelligence: values.enableSourceIntelligence,
    follow_up_depth: values.followUpDepth,
    scdl_level: values.scdlLevel as SCDLLevel,
  };
}

export function CreateAuditPage() {
  const navigate = useNavigate();
  const createAuditMutation = useMutation({
    mutationFn: createAudit,
    onSuccess: (response) => {
      navigate(`/audits/${response.audit_id}`, { replace: true });
    },
  });
  const {
    formState: { errors },
    handleSubmit,
    register,
  } = useForm<CreateAuditFormInput, unknown, CreateAuditFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      brandName: "",
      brandDomain: "",
      brandDescription: "",
      seedQueries: "",
      providers: ["mock"],
      runsPerQuery: 1,
      language: "",
      country: "",
      locale: "",
      maxQueries: "",
      enableQueryExpansion: false,
      enableSourceIntelligence: false,
      followUpDepth: 0,
      scdlLevel: "L1",
    },
  });

  const onSubmit = handleSubmit((values) => {
    createAuditMutation.mutate(buildPayload(values));
  });

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

        <Field htmlFor="seed-queries" label="Seed queries" error={errors.seedQueries?.message}>
          <textarea
            id="seed-queries"
            className="min-h-28 w-full rounded-md border border-border bg-white px-3 py-2 text-sm text-ink outline-none transition-colors placeholder:text-slate-400 focus:border-brand-600 focus:ring-2 focus:ring-brand-100"
            placeholder={"best ai visibility tools\nbrand monitoring platforms"}
            {...register("seedQueries")}
          />
        </Field>

        <div className="grid gap-4 md:grid-cols-[1.4fr_0.8fr_0.8fr]">
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

          <Field
            htmlFor="runs-per-query"
            label="Runs per query"
            error={errors.runsPerQuery?.message}
          >
            <Input id="runs-per-query" type="number" min={1} max={5} {...register("runsPerQuery")} />
          </Field>

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

        <div className="grid gap-4 md:grid-cols-4">
          <Field htmlFor="language" label="Language" error={errors.language?.message}>
            <Input id="language" placeholder="en" {...register("language")} />
          </Field>
          <Field htmlFor="country" label="Country" error={errors.country?.message}>
            <Input id="country" placeholder="US" {...register("country")} />
          </Field>
          <Field htmlFor="locale" label="Locale" error={errors.locale?.message}>
            <Input id="locale" placeholder="en-US" {...register("locale")} />
          </Field>
          <Field htmlFor="max-queries" label="Max queries" error={errors.maxQueries?.message}>
            <Input id="max-queries" type="number" min={1} {...register("maxQueries")} />
          </Field>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <label className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm text-ink">
            <input
              className="size-4 accent-brand-600"
              type="checkbox"
              {...register("enableQueryExpansion")}
            />
            Query expansion
          </label>
          <label className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm text-ink">
            <input
              className="size-4 accent-brand-600"
              type="checkbox"
              {...register("enableSourceIntelligence")}
            />
            Source intelligence
          </label>
          <Field
            htmlFor="follow-up-depth"
            label="Follow-up depth"
            error={errors.followUpDepth?.message}
          >
            <select
              id="follow-up-depth"
              className="h-10 w-full rounded-md border border-border bg-white px-3 text-sm text-ink outline-none transition-colors focus:border-brand-600 focus:ring-2 focus:ring-brand-100"
              {...register("followUpDepth")}
            >
              <option value={0}>0</option>
              <option value={1}>1</option>
            </select>
          </Field>
        </div>

        {createAuditMutation.error ? (
          <p className="text-sm text-red-700">
            {createAuditMutation.error instanceof ApiError
              ? createAuditMutation.error.message
              : "Unable to create audit."}
          </p>
        ) : null}

        <div className="flex justify-end">
          <Button type="submit" disabled={createAuditMutation.isPending}>
            <Plus className="size-4" aria-hidden="true" />
            {createAuditMutation.isPending ? "Creating..." : "Create audit"}
          </Button>
        </div>
      </form>
    </section>
  );
}
