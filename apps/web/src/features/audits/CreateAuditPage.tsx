import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { ArrowLeft, Loader2, Plus, Sparkles, Trash2 } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useFieldArray, useForm, useWatch } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { Field } from "../../components/ui/Field";
import { Input } from "../../components/ui/Input";
import { ApiError, createAudit, generateSeedQuerySuggestions } from "../../lib/api/client";
import type { AuditTarget } from "../../lib/api/types";
import { AuditEstimatePanel } from "./AuditEstimatePanel";
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
  queryTypeOptions,
  createAuditSetupSchema,
  parseSeedQueryItems,
  seedQueryItemsFromText,
  type CreateAuditFormInput,
  type CreateAuditFormValues,
} from "./auditSetupFormConfig";

type CreateAuditDefaults = Partial<CreateAuditFormInput> & {
  seedQueries?: string;
};

export function CreateAuditPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation("audits");
  const duplicateDefaults = (location.state as { auditDefaults?: CreateAuditDefaults } | null)
    ?.auditDefaults;
  const [isGenerationOpen, setIsGenerationOpen] = useState(false);
  const [useDomainForGeneration, setUseDomainForGeneration] = useState<boolean | null>(null);
  const [useDescriptionForGeneration, setUseDescriptionForGeneration] = useState<boolean | null>(
    null,
  );
  const [generationWarnings, setGenerationWarnings] = useState<string[]>([]);
  const formSchema = useMemo(() => createAuditSetupSchema(t), [t]);
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
    resolver: zodResolver(formSchema),
    defaultValues: {
      brandName: duplicateDefaults?.brandName ?? "",
      brandDomain: duplicateDefaults?.brandDomain ?? "",
      brandDescription: duplicateDefaults?.brandDescription ?? "",
      seedQueryItems:
        duplicateDefaults?.seedQueryItems ?? seedQueryItemsFromText(duplicateDefaults?.seedQueries),
      modelTargets: duplicateDefaults?.modelTargets ?? [],
      language: duplicateDefaults?.language ?? "en",
      country: duplicateDefaults?.country ?? "US",
      maxQueries: duplicateDefaults?.maxQueries ?? "",
      enableSourceIntelligence: duplicateDefaults?.enableSourceIntelligence ?? false,
      scdlLevel: duplicateDefaults?.scdlLevel ?? "L1",
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
      const appendResult = appendGeneratedSeedQueries(
        currentQueries,
        response.suggestions,
      );
      const warnings = [...(response.warnings ?? [])];
      const addedCount =
        appendResult.queries.length - parseSeedQueryItems(currentQueries).length;
      if (appendResult.duplicateCount > 0) {
        warnings.push(t("generation.duplicatesSkipped", { count: appendResult.duplicateCount }));
      }
      if (appendResult.limitSkipped > 0) {
        warnings.push(
          t("generation.limitSkipped", { count: addedCount }),
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
  const estimatedTokens = estimateAuditTokens({ ...watchedValues, modelTargets });
  const estimatePayload = useMemo(() => {
    if (parseSeedQueryItems(watchedValues.seedQueryItems).length === 0 || modelTargets.length === 0) {
      return null;
    }
    return buildEstimatePayload({ ...watchedValues, modelTargets });
  }, [modelTargets, watchedValues]);
  const auditEstimate = useAuditEstimate(estimatePayload, estimatePayload !== null);
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
    createAuditMutation.mutate(buildPayload(values));
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

  return (
    <section className="rounded-md border border-border bg-surface shadow-panel">
      <div className="flex flex-col gap-3 border-b border-border px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-ink">{t("create")}</h1>
          <p className="text-sm text-subtle">{t("manualSetup")}</p>
        </div>
        <Button asChild variant="ghost">
          <Link to="/audits">
            <ArrowLeft className="size-4" aria-hidden="true" />
            {t("backToAudits")}
          </Link>
        </Button>
      </div>

      <form className="space-y-6 px-5 py-5" noValidate onSubmit={onSubmit}>
        <div className="grid gap-4 md:grid-cols-2">
          <Field htmlFor="brand-name" label={t("fields.brandName")} error={errors.brandName?.message}>
            <Input id="brand-name" {...register("brandName")} />
          </Field>
          <Field htmlFor="brand-domain" label={t("fields.brandDomain")} error={errors.brandDomain?.message}>
            <Input id="brand-domain" placeholder="example.com" {...register("brandDomain")} />
          </Field>
        </div>

        <Field
          htmlFor="brand-description"
          label={t("fields.brandDescription")}
          error={errors.brandDescription?.message}
        >
          <textarea
            id="brand-description"
            className="min-h-24 w-full rounded-md border border-border bg-white px-3 py-2 text-sm text-ink outline-none transition-colors placeholder:text-slate-400 focus:border-brand-600 focus:ring-2 focus:ring-brand-100"
            maxLength={brandDescriptionMaxLength}
            {...register("brandDescription")}
          />
          <p className="text-xs text-subtle">
            {brandDescriptionLength} / {brandDescriptionMaxLength}
          </p>
        </Field>

        <div className="space-y-3">
          <fieldset className="space-y-2">
            <legend className="text-sm font-medium text-ink">{t("fields.seedQueries")}</legend>
            {seedQueryFields.fields.map((field, index) => (
              <div className="grid gap-2 sm:grid-cols-[1fr_12rem_auto]" key={field.id}>
                <Input
                  aria-label={t("fields.seedQuery", { index: index + 1 })}
                  placeholder="best ai visibility tools"
                  {...register(`seedQueryItems.${index}.text`)}
                />
                <select
                  aria-label={t("fields.queryType", { index: index + 1 })}
                  className="h-10 w-full rounded-md border border-border bg-white px-3 text-sm text-ink outline-none transition-colors focus:border-brand-600 focus:ring-2 focus:ring-brand-100"
                  {...register(`seedQueryItems.${index}.type`)}
                >
                  <option value="">{t("queryTypes.none")}</option>
                  {queryTypeOptions.map((type) => (
                    <option key={type.value} value={type.value}>
                      {t(`queryTypes.${type.value}`)}
                    </option>
                  ))}
                </select>
                <Button
                  type="button"
                  variant="ghost"
                  aria-label={t("fields.removeSeedQuery", { index: index + 1 })}
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
              {t("generation.addQuery", { defaultValue: "Add query" })}
            </Button>
          </fieldset>
          <Button
            type="button"
            variant="secondary"
            onClick={() => setIsGenerationOpen((current) => !current)}
          >
            <Sparkles className="size-4" aria-hidden="true" />
            {t("generation.toggle")}
          </Button>
          {isGenerationOpen ? (
            <div className="space-y-3 rounded-md border border-border bg-muted p-3">
              <p className="text-sm font-medium text-ink">{t("generation.title")}</p>
              <div className="grid gap-2 sm:grid-cols-2">
                <label className="flex items-center gap-2 text-sm text-ink">
                  <input
                    className="size-4 accent-brand-600"
                    type="checkbox"
                    checked={effectiveUseDomainForGeneration}
                    disabled={!hasGenerationDomain}
                    onChange={(event) => setUseDomainForGeneration(event.target.checked)}
                  />
                  {t("generation.useDomain")}
                </label>
                <label className="flex items-center gap-2 text-sm text-ink">
                  <input
                    className="size-4 accent-brand-600"
                    type="checkbox"
                    checked={effectiveUseDescriptionForGeneration}
                    disabled={!hasGenerationDescription}
                    onChange={(event) => setUseDescriptionForGeneration(event.target.checked)}
                  />
                  {t("generation.useDescription")}
                </label>
              </div>
              <Button type="button" disabled={!canGenerateQueries} onClick={generateQueries}>
                {generateMutation.isPending ? (
                  <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                ) : (
                  <Sparkles className="size-4" aria-hidden="true" />
                )}
                {generateMutation.isPending ? t("generation.generating") : t("generation.generate10")}
              </Button>
              {generateMutation.isError ? (
                <p className="text-sm text-red-700">
                  {t("generation.error")}
                </p>
              ) : null}
              {generationWarnings.map((warning) => (
                <p className="text-sm text-amber-700" key={warning}>
                  {warning}
                </p>
              ))}
            </div>
          ) : null}
        </div>

        <div className="space-y-2">
          <AuditTargetSelector value={modelTargets} onChange={setModelTargets} />
          {modelTargetsError ? (
            <p className="text-sm text-red-700">{modelTargetsError}</p>
          ) : null}
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <Field htmlFor="language" label={t("fields.language")} error={errors.language?.message}>
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
          <Field htmlFor="country" label={t("fields.country")} error={errors.country?.message}>
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
          <Field htmlFor="max-queries" label={t("fields.maxQueries")} error={errors.maxQueries?.message}>
            <Input id="max-queries" type="number" min={1} {...register("maxQueries")} />
          </Field>
        </div>

        {isSourceIntelligenceAvailable ? (
          <div className="grid gap-3 md:grid-cols-2">
            <label className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm text-ink">
              <input
                className="size-4 accent-brand-600"
                type="checkbox"
                {...register("enableSourceIntelligence")}
              />
              {t("fields.sourceIntelligence")}
            </label>
          </div>
        ) : null}

        {createAuditMutation.error ? (
          <p className="text-sm text-red-700">
            {createAuditMutation.error instanceof ApiError
              ? createAuditMutation.error.message
              : t("errors.create")}
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
            disabled={createAuditMutation.isPending || Boolean(auditEstimate.data?.over_cap)}
          >
            <Plus className="size-4" aria-hidden="true" />
            {createAuditMutation.isPending ? t("createPending") : t("create")}
          </Button>
        </div>
      </form>
    </section>
  );
}
