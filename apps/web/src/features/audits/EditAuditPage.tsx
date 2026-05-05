import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Loader2, Plus, Save, Sparkles, Trash2 } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useFieldArray, useForm, useWatch } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { Field } from "../../components/ui/Field";
import { Input } from "../../components/ui/Input";
import {
  ApiError,
  generateSeedQuerySuggestions,
  getAuditDetail,
  updateAudit,
} from "../../lib/api/client";
import type { AuditDetail, AuditTarget } from "../../lib/api/types";
import { AuditEstimatePanel } from "./AuditEstimatePanel";
import { AuditBreadcrumbs } from "./AuditBreadcrumbs";
import { AuditStatusBadge } from "./AuditStatusBadge";
import { AuditTargetSelector } from "./AuditTargetSelector";
import { useAuditEstimate } from "./auditEstimate";
import {
  brandDescriptionMaxLength,
  appendGeneratedSeedQueries,
  buildPayload,
  buildEstimatePayload,
  countryOptions,
  emptySeedQueryItem,
  estimateAuditTokens,
  languageOptions,
  parseSeedQueryItems,
  queryTypeOptions,
  schema,
  type CreateAuditFormInput,
  type CreateAuditFormValues,
} from "./auditSetupFormConfig";
import { auditDetailToFormDefaults } from "./auditSetupFormMapping";

function detailQueryKey(auditId: number) {
  return ["audit", auditId, "detail"] as const;
}

export function EditAuditPage() {
  const params = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isGenerationOpen, setIsGenerationOpen] = useState(false);
  const [useDomainForGeneration, setUseDomainForGeneration] = useState<boolean | null>(null);
  const [useDescriptionForGeneration, setUseDescriptionForGeneration] = useState<boolean | null>(
    null,
  );
  const [generationWarnings, setGenerationWarnings] = useState<string[]>([]);
  const auditId = Number(params.auditId);
  const isValidAuditId = Number.isInteger(auditId) && auditId > 0;
  const detail = useQuery({
    queryKey: detailQueryKey(auditId),
    queryFn: () => getAuditDetail(auditId),
    enabled: isValidAuditId,
    retry: false,
  });
  const updateAuditMutation = useMutation({
    mutationFn: (values: CreateAuditFormValues) => updateAudit(auditId, buildPayload(values)),
    onSuccess: (audit) => {
      queryClient.setQueryData<AuditDetail>(detailQueryKey(auditId), audit);
      void queryClient.invalidateQueries({ queryKey: ["audit", auditId] });
      void queryClient.invalidateQueries({ queryKey: ["audits"] });
      navigate(`/audits/${auditId}`, { replace: true });
    },
  });
  const {
    formState: { errors },
    control,
    getValues,
    handleSubmit,
    register,
    reset,
    setValue,
  } = useForm<CreateAuditFormInput, unknown, CreateAuditFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      brandName: "",
      brandDomain: "",
      brandDescription: "",
      seedQueryItems: [{ ...emptySeedQueryItem }],
      modelTargets: [],
      language: "en",
      country: "US",
      maxQueries: "",
      enableSourceIntelligence: false,
      scdlLevel: "L1",
    },
  });
  const seedQueryFields = useFieldArray({
    control,
    name: "seedQueryItems",
  });
  const generateMutation = useMutation({
    mutationFn: generateSeedQuerySuggestions,
    onSuccess: (response) => {
      const currentQueries = getValues("seedQueryItems");
      const appendResult = appendGeneratedSeedQueries(currentQueries, response.suggestions);
      const warnings = [...(response.warnings ?? [])];
      const addedCount = appendResult.queries.length - parseSeedQueryItems(currentQueries).length;
      if (appendResult.duplicateCount > 0) {
        warnings.push(`${appendResult.duplicateCount} duplicate queries were skipped.`);
      }
      if (appendResult.limitSkipped > 0) {
        warnings.push(
          `Only ${addedCount} queries were added because the audit limit is 20 seed queries.`,
        );
      }
      setValue("seedQueryItems", appendResult.queries, {
        shouldDirty: true,
        shouldValidate: true,
      });
      setGenerationWarnings(warnings);
    },
    onError: () => {
      setGenerationWarnings([]);
    },
  });

  useEffect(() => {
    if (detail.data) {
      reset(auditDetailToFormDefaults(detail.data));
    }
  }, [detail.data, reset]);

  const watchedValues = useWatch({ control });
  const modelTargets = (watchedValues.modelTargets ?? []) as AuditTarget[];
  const isSourceIntelligenceAvailable = modelTargets.some((target) => target.level === "L2");
  const setModelTargets = useCallback(
    (targets: AuditTarget[]) => {
      setValue("modelTargets", targets, {
        shouldDirty: true,
        shouldValidate: true,
      });
    },
    [setValue],
  );
  useEffect(() => {
    if (!isSourceIntelligenceAvailable && watchedValues.enableSourceIntelligence) {
      setValue("enableSourceIntelligence", false, {
        shouldDirty: true,
        shouldValidate: true,
      });
    }
  }, [isSourceIntelligenceAvailable, setValue, watchedValues.enableSourceIntelligence]);
  const canEdit = detail.data?.status === "created";
  const estimatedTokens = estimateAuditTokens({ ...watchedValues, modelTargets });
  const estimatePayload = useMemo(() => {
    if (parseSeedQueryItems(watchedValues.seedQueryItems).length === 0 || modelTargets.length === 0) {
      return null;
    }
    return buildEstimatePayload({ ...watchedValues, modelTargets });
  }, [modelTargets, watchedValues]);
  const auditEstimate = useAuditEstimate(estimatePayload, estimatePayload !== null && canEdit);
  const brandDescriptionLength = watchedValues.brandDescription?.length ?? 0;
  const seedQueryItemsError =
    errors.seedQueryItems?.message ?? errors.seedQueryItems?.root?.message;
  const modelTargetsError =
    typeof errors.modelTargets?.message === "string" ? errors.modelTargets.message : null;
  const hasGenerationDomain = Boolean(watchedValues.brandDomain?.trim());
  const hasGenerationDescription = Boolean(watchedValues.brandDescription?.trim());
  const effectiveUseDomainForGeneration =
    hasGenerationDomain && (useDomainForGeneration ?? true);
  const effectiveUseDescriptionForGeneration =
    hasGenerationDescription && (useDescriptionForGeneration ?? true);
  const canGenerateQueries =
    !generateMutation.isPending &&
    (effectiveUseDomainForGeneration || effectiveUseDescriptionForGeneration);
  const onSubmit = handleSubmit((values) => {
    updateAuditMutation.mutate(values);
  });
  const generateQueries = () => {
    if (!canGenerateQueries) {
      return;
    }

    generateMutation.mutate({
      brandName: getValues("brandName"),
      brandDomain: getValues("brandDomain"),
      brandDescription: getValues("brandDescription"),
      useDomain: effectiveUseDomainForGeneration,
      useDescription: effectiveUseDescriptionForGeneration,
      count: 10,
      existingQueries: parseSeedQueryItems(getValues("seedQueryItems")),
    });
  };

  if (detail.isLoading) {
    return (
      <section className="rounded-md border border-border bg-surface px-5 py-10 text-sm text-subtle shadow-panel" role="status">
        Loading audit setup...
      </section>
    );
  }

  if (detail.isError || !detail.data || !isValidAuditId) {
    return (
      <section className="rounded-md border border-border bg-surface p-5 shadow-panel">
        <p className="text-sm text-red-700">Audit setup unavailable.</p>
        <Button asChild className="mt-4" variant="secondary">
          <Link to="/audits">Back to audits</Link>
        </Button>
      </section>
    );
  }

  return (
    <section className="rounded-md border border-border bg-surface shadow-panel">
      <div className="flex flex-col gap-3 border-b border-border px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <AuditBreadcrumbs auditId={auditId} auditNumber={detail.data.audit_number} />
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-xl font-semibold text-ink">Edit audit setup</h1>
            <AuditStatusBadge status={detail.data.status} />
          </div>
          <p className="mt-1 text-sm text-subtle">{detail.data.brand_name}</p>
        </div>
        <Button asChild variant="ghost">
          <Link to={`/audits/${auditId}`}>
            <ArrowLeft className="size-4" aria-hidden="true" />
            Back to audit
          </Link>
        </Button>
      </div>

      {!canEdit ? (
        <div className="px-5 py-5">
          <div className="rounded-md border border-border bg-muted px-4 py-3 text-sm text-subtle">
            Only audits in Created status can be edited. Duplicate this audit to change
            setup for a new run.
          </div>
        </div>
      ) : (
        <form className="space-y-6 px-5 py-5" noValidate onSubmit={onSubmit}>
          <div className="grid gap-4 md:grid-cols-2">
            <Field htmlFor="edit-brand-name" label="Brand name" error={errors.brandName?.message}>
              <Input id="edit-brand-name" {...register("brandName")} />
            </Field>
            <Field
              htmlFor="edit-brand-domain"
              label="Brand domain"
              error={errors.brandDomain?.message}
            >
              <Input id="edit-brand-domain" placeholder="example.com" {...register("brandDomain")} />
            </Field>
          </div>

          <Field
            htmlFor="edit-brand-description"
            label="Brand description"
            error={errors.brandDescription?.message}
          >
            <textarea
              id="edit-brand-description"
              className="min-h-24 w-full rounded-md border border-border bg-white px-3 py-2 text-sm text-ink outline-none transition-colors placeholder:text-slate-400 focus:border-brand-600 focus:ring-2 focus:ring-brand-100"
              maxLength={brandDescriptionMaxLength}
              {...register("brandDescription")}
            />
            <p className="text-xs text-subtle">
              {brandDescriptionLength} / {brandDescriptionMaxLength}
            </p>
          </Field>

          <fieldset className="space-y-2">
            <legend className="text-sm font-medium text-ink">Seed queries</legend>
            {seedQueryFields.fields.map((field, index) => (
              <div className="grid gap-2 sm:grid-cols-[1fr_12rem_auto]" key={field.id}>
                <Input
                  aria-label={`Seed query ${index + 1}`}
                  placeholder="best ai visibility tools"
                  {...register(`seedQueryItems.${index}.text`)}
                />
                <select
                  aria-label={`Query type ${index + 1}`}
                  className="h-10 w-full rounded-md border border-border bg-white px-3 text-sm text-ink outline-none transition-colors focus:border-brand-600 focus:ring-2 focus:ring-brand-100"
                  {...register(`seedQueryItems.${index}.type`)}
                >
                  <option value="">No type</option>
                  {queryTypeOptions.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
                <Button
                  type="button"
                  variant="ghost"
                  aria-label={`Remove seed query ${index + 1}`}
                  onClick={() => seedQueryFields.remove(index)}
                >
                  <Trash2 className="size-4" aria-hidden="true" />
                </Button>
                <input type="hidden" {...register(`seedQueryItems.${index}.source`)} />
              </div>
            ))}
            {seedQueryItemsError ? (
              <p className="text-sm text-red-700">{seedQueryItemsError}</p>
            ) : null}
            <Button
              type="button"
              variant="secondary"
              onClick={() => seedQueryFields.append({ ...emptySeedQueryItem })}
            >
              <Plus className="size-4" aria-hidden="true" />
              Add query
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsGenerationOpen((current) => !current)}
            >
              <Sparkles className="size-4" aria-hidden="true" />
              Generate seed queries
            </Button>
            {isGenerationOpen ? (
              <div className="space-y-3 rounded-md border border-border bg-muted p-3">
                <p className="text-sm font-medium text-ink">Generate seed queries</p>
                <div className="grid gap-2 sm:grid-cols-2">
                  <label className="flex items-center gap-2 text-sm text-ink">
                    <input
                      className="size-4 accent-brand-600"
                      type="checkbox"
                      checked={effectiveUseDomainForGeneration}
                      disabled={!hasGenerationDomain}
                      onChange={(event) => setUseDomainForGeneration(event.target.checked)}
                    />
                    Use brand domain
                  </label>
                  <label className="flex items-center gap-2 text-sm text-ink">
                    <input
                      className="size-4 accent-brand-600"
                      type="checkbox"
                      checked={effectiveUseDescriptionForGeneration}
                      disabled={!hasGenerationDescription}
                      onChange={(event) => setUseDescriptionForGeneration(event.target.checked)}
                    />
                    Use brand description
                  </label>
                </div>
                <Button type="button" disabled={!canGenerateQueries} onClick={generateQueries}>
                  {generateMutation.isPending ? (
                    <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                  ) : (
                    <Sparkles className="size-4" aria-hidden="true" />
                  )}
                  {generateMutation.isPending ? "Generating..." : "Generate 10 queries"}
                </Button>
                {generateMutation.isError ? (
                  <p className="text-sm text-red-700">
                    Could not generate seed queries. Please try again or enter queries manually.
                  </p>
                ) : null}
                {generationWarnings.map((warning) => (
                  <p className="text-sm text-amber-700" key={warning}>
                    {warning}
                  </p>
                ))}
              </div>
            ) : null}
          </fieldset>

          <div className="space-y-2">
            <AuditTargetSelector value={modelTargets} onChange={setModelTargets} />
            {modelTargetsError ? (
              <p className="text-sm text-red-700">{modelTargetsError}</p>
            ) : null}
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <Field htmlFor="edit-language" label="Language" error={errors.language?.message}>
              <select
                id="edit-language"
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
            <Field htmlFor="edit-country" label="Country" error={errors.country?.message}>
              <select
                id="edit-country"
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
            <Field htmlFor="edit-max-queries" label="Max queries" error={errors.maxQueries?.message}>
              <Input id="edit-max-queries" type="number" min={1} {...register("maxQueries")} />
            </Field>
          </div>

          {isSourceIntelligenceAvailable ? (
            <label className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm text-ink md:w-1/2">
              <input
                className="size-4 accent-brand-600"
                type="checkbox"
                {...register("enableSourceIntelligence")}
              />
              Source intelligence
            </label>
          ) : null}

          {updateAuditMutation.error ? (
            <p className="text-sm text-red-700">
              {updateAuditMutation.error instanceof ApiError
                ? updateAuditMutation.error.message
                : "Unable to update audit."}
            </p>
          ) : null}

          <div className="flex flex-col gap-3 border-t border-border pt-4 sm:flex-row sm:items-center sm:justify-between">
            <AuditEstimatePanel
              error={auditEstimate.error}
              estimate={auditEstimate.data}
              isLoading={auditEstimate.isLoading || auditEstimate.isFetching}
              optimisticTokens={estimatedTokens}
            />
            <Button
              type="submit"
              disabled={updateAuditMutation.isPending || Boolean(auditEstimate.data?.over_cap)}
            >
              <Save className="size-4" aria-hidden="true" />
              {updateAuditMutation.isPending ? "Saving..." : "Save setup"}
            </Button>
          </div>
        </form>
      )}
    </section>
  );
}
