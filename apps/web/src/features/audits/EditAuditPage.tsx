import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Save } from "lucide-react";
import { useEffect } from "react";
import { useForm, useWatch } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { Field } from "../../components/ui/Field";
import { Input } from "../../components/ui/Input";
import { ApiError, getAuditDetail, updateAudit } from "../../lib/api/client";
import type { AuditDetail } from "../../lib/api/types";
import { AuditBreadcrumbs } from "./AuditBreadcrumbs";
import { AuditStatusBadge } from "./AuditStatusBadge";
import {
  buildPayload,
  countryOptions,
  estimateAuditTokens,
  languageOptions,
  providerOptions,
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
    handleSubmit,
    register,
    reset,
  } = useForm<CreateAuditFormInput, unknown, CreateAuditFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      brandName: "",
      brandDomain: "",
      brandDescription: "",
      seedQueries: "",
      providers: ["mock"],
      language: "en",
      country: "US",
      maxQueries: "",
      enableSourceIntelligence: false,
      scdlLevel: "L1",
    },
  });

  useEffect(() => {
    if (detail.data) {
      reset(auditDetailToFormDefaults(detail.data));
    }
  }, [detail.data, reset]);

  const watchedValues = useWatch({ control });
  const estimatedTokens = estimateAuditTokens(watchedValues);
  const canEdit = detail.data?.status === "created";
  const onSubmit = handleSubmit((values) => {
    updateAuditMutation.mutate(values);
  });

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
              {...register("brandDescription")}
            />
          </Field>

          <Field
            htmlFor="edit-seed-queries"
            label="Seed queries"
            error={errors.seedQueries?.message}
          >
            <textarea
              id="edit-seed-queries"
              className="min-h-28 w-full rounded-md border border-border bg-white px-3 py-2 text-sm text-ink outline-none transition-colors placeholder:text-slate-400 focus:border-brand-600 focus:ring-2 focus:ring-brand-100"
              {...register("seedQueries")}
            />
          </Field>

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

            <Field htmlFor="edit-scdl-level" label="SCDL level" error={errors.scdlLevel?.message}>
              <select
                id="edit-scdl-level"
                className="h-10 w-full rounded-md border border-border bg-white px-3 text-sm text-ink outline-none transition-colors focus:border-brand-600 focus:ring-2 focus:ring-brand-100"
                {...register("scdlLevel")}
              >
                <option value="L1">L1 - no web access</option>
                <option value="L2">L2 - web access</option>
              </select>
            </Field>
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

          <label className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm text-ink md:w-1/2">
            <input
              className="size-4 accent-brand-600"
              type="checkbox"
              {...register("enableSourceIntelligence")}
            />
            Source intelligence
          </label>

          {updateAuditMutation.error ? (
            <p className="text-sm text-red-700">
              {updateAuditMutation.error instanceof ApiError
                ? updateAuditMutation.error.message
                : "Unable to update audit."}
            </p>
          ) : null}

          <div className="flex flex-col gap-3 border-t border-border pt-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm font-medium text-ink">
              Estimated audit cost:{" "}
              <span className="text-brand-700">{estimatedTokens} tokens</span>
            </p>
            <Button type="submit" disabled={updateAuditMutation.isPending}>
              <Save className="size-4" aria-hidden="true" />
              {updateAuditMutation.isPending ? "Saving..." : "Save setup"}
            </Button>
          </div>
        </form>
      )}
    </section>
  );
}
