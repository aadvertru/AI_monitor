import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Loader2, Plus, Save, Sparkles, Trash2 } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useFieldArray, useForm, useWatch } from "react-hook-form";
import { useTranslation } from "react-i18next";
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
  createAuditSetupSchema,
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
  const { t } = useTranslation("audits");
  const [isGenerationOpen, setIsGenerationOpen] = useState(false);
  const [useDomainForGeneration, setUseDomainForGeneration] = useState<boolean | null>(null);
  const [useDescriptionForGeneration, setUseDescriptionForGeneration] = useState<boolean | null>(
    null,
  );
  const [generationWarnings, setGenerationWarnings] = useState<string[]>([]);
  const formSchema = useMemo(() => createAuditSetupSchema(t), [t]);
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
    resolver: zodResolver(formSchema),
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
        {t("errors.loadingSetup")}
      </section>
    );
  }

  if (detail.isError || !detail.data || !isValidAuditId) {
    return (
      <section className="rounded-md border border-border bg-surface p-5 shadow-panel">
        <p className="text-sm text-red-700">
          {t("errors.setupUnavailable")}
        </p>
        <Button asChild className="mt-4" variant="secondary">
          <Link to="/audits">{t("backToAudits")}</Link>
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
            <h1 className="text-xl font-semibold text-ink">{t("edit")}</h1>
            <AuditStatusBadge status={detail.data.status} />
          </div>
          <p className="mt-1 text-sm text-subtle">{detail.data.brand_name}</p>
        </div>
        <Button asChild variant="ghost">
          <Link to={`/audits/${auditId}`}>
            <ArrowLeft className="size-4" aria-hidden="true" />
            {t("backToAudit")}
          </Link>
        </Button>
      </div>

      {!canEdit ? (
        <div className="px-5 py-5">
          <div className="rounded-md border border-border bg-muted px-4 py-3 text-sm text-subtle">
            {t("errors.createdOnlyEdit")}
          </div>
        </div>
      ) : (
        <form className="space-y-6 px-5 py-5" noValidate onSubmit={onSubmit}>
          <div className="grid gap-4 md:grid-cols-2">
            <Field htmlFor="edit-brand-name" label={t("fields.brandName")} error={errors.brandName?.message}>
              <Input id="edit-brand-name" {...register("brandName")} />
            </Field>
            <Field
              htmlFor="edit-brand-domain"
              label={t("fields.brandDomain")}
              error={errors.brandDomain?.message}
            >
              <Input id="edit-brand-domain" placeholder="example.com" {...register("brandDomain")} />
            </Field>
          </div>

          <Field
            htmlFor="edit-brand-description"
            label={t("fields.brandDescription")}
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
              {t("generation.addQuery")}
            </Button>
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
          </fieldset>

          <div className="space-y-2">
            <AuditTargetSelector value={modelTargets} onChange={setModelTargets} />
            {modelTargetsError ? (
              <p className="text-sm text-red-700">{modelTargetsError}</p>
            ) : null}
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <Field htmlFor="edit-language" label={t("fields.language")} error={errors.language?.message}>
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
            <Field htmlFor="edit-country" label={t("fields.country")} error={errors.country?.message}>
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
            <Field htmlFor="edit-max-queries" label={t("fields.maxQueries")} error={errors.maxQueries?.message}>
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
              {t("fields.sourceIntelligence")}
            </label>
          ) : null}

          {updateAuditMutation.error ? (
            <p className="text-sm text-red-700">
              {updateAuditMutation.error instanceof ApiError
                ? updateAuditMutation.error.message
                : t("errors.save")}
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
              {updateAuditMutation.isPending ? t("savePending") : t("saveSetup")}
            </Button>
          </div>
        </form>
      )}
    </section>
  );
}
