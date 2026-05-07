import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "../../components/ui/Button";
import { getProfile, updateProfilePreferences } from "../../lib/api/client";
import { persistLocale, supportedLocales } from "../../lib/i18n/config";
import { useLocaleFormatters } from "../../lib/i18n/format";
import type { ProfilePreferences } from "../../lib/api/types";

function yesNo(value: boolean, yes: string, no: string) {
  return value ? yes : no;
}

function preferencesEqual(left: ProfilePreferences, right: ProfilePreferences) {
  return (
    left.locale === right.locale &&
    left.email_notifications === right.email_notifications &&
    left.audit_completed_notifications === right.audit_completed_notifications &&
    left.provider_error_notifications === right.provider_error_notifications
  );
}

export function ProfilePage() {
  const { i18n, t } = useTranslation("profile");
  const queryClient = useQueryClient();
  const formatters = useLocaleFormatters();
  const profile = useQuery({
    queryKey: ["profile"],
    queryFn: getProfile,
    retry: false,
  });
  const [draftPreferences, setDraftPreferences] = useState<ProfilePreferences | null>(
    null,
  );
  const [saveMessage, setSaveMessage] = useState<"saved" | null>(null);
  const updatePreferences = useMutation({
    mutationFn: updateProfilePreferences,
    onSuccess: (data) => {
      queryClient.setQueryData(["profile"], data);
      setDraftPreferences(data.preferences);
      const persistedLocale = persistLocale(data.preferences.locale);
      void i18n.changeLanguage(persistedLocale);
      setSaveMessage("saved");
    },
  });

  useEffect(() => {
    if (profile.data && draftPreferences === null) {
      setDraftPreferences(profile.data.preferences);
    }
  }, [draftPreferences, profile.data]);

  const hasUnsavedChanges = useMemo(() => {
    if (!profile.data || !draftPreferences) {
      return false;
    }
    return !preferencesEqual(profile.data.preferences, draftPreferences);
  }, [draftPreferences, profile.data]);

  const setPreference = <Key extends keyof ProfilePreferences>(
    key: Key,
    value: ProfilePreferences[Key],
  ) => {
    setSaveMessage(null);
    setDraftPreferences((current) =>
      current ? { ...current, [key]: value } : current,
    );
  };

  if (profile.isLoading) {
    return (
      <section
        className="rounded-md border border-border bg-surface px-5 py-10 text-sm text-subtle shadow-panel"
        role="status"
      >
        {t("loading")}
      </section>
    );
  }

  if (profile.isError || !profile.data) {
    return (
      <section className="rounded-md border border-border bg-surface p-5 shadow-panel">
        <div className="flex items-center gap-2 text-sm text-red-700">
          <AlertTriangle className="size-4" aria-hidden="true" />
          {t("error")}
        </div>
      </section>
    );
  }

  const data = profile.data;
  const preferences = draftPreferences ?? data.preferences;
  const displayName = data.user.display_name || t("account.noDisplayName");
  const resetDate = data.usage.reset_at ? formatters.dateTime(data.usage.reset_at) : t("usage.noReset");
  const actualUsage = data.usage.actual_usage;

  return (
    <section className="space-y-4">
      <div className="rounded-md border border-border bg-surface p-5 shadow-panel">
        <h1 className="text-xl font-semibold text-ink">{t("title")}</h1>
        <p className="mt-1 text-sm text-subtle">{t("subtitle")}</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-md border border-border bg-surface p-5 shadow-panel">
          <h2 className="text-base font-semibold text-ink">{t("account.title")}</h2>
          <dl className="mt-4 grid gap-3 text-sm">
            <div>
              <dt className="text-subtle">{t("account.displayName")}</dt>
              <dd className="font-medium text-ink">{displayName}</dd>
            </div>
            <div>
              <dt className="text-subtle">{t("account.email")}</dt>
              <dd className="font-medium text-ink">{data.user.email}</dd>
            </div>
            <div>
              <dt className="text-subtle">{t("account.editing")}</dt>
              <dd className="font-medium text-ink">{t("account.readOnly")}</dd>
            </div>
          </dl>
        </section>

        <section className="rounded-md border border-border bg-surface p-5 shadow-panel">
          <h2 className="text-base font-semibold text-ink">{t("plan.title")}</h2>
          <dl className="mt-4 grid gap-3 text-sm">
            <div>
              <dt className="text-subtle">{t("plan.name")}</dt>
              <dd className="font-medium text-ink">{data.plan.name}</dd>
            </div>
            <div>
              <dt className="text-subtle">{t("plan.status")}</dt>
              <dd className="font-medium text-ink">{t("plan.demoStatus")}</dd>
            </div>
          </dl>
          {data.plan.is_demo ? (
            <p className="mt-4 rounded-md bg-brand-50 px-3 py-2 text-sm font-medium text-brand-700">
              {t("demoMarker")}
            </p>
          ) : null}
        </section>

        <section className="rounded-md border border-border bg-surface p-5 shadow-panel">
          <h2 className="text-base font-semibold text-ink">{t("usage.title")}</h2>
          <dl className="mt-4 grid gap-3 text-sm">
            <div>
              <dt className="text-subtle">{t("usage.remaining")}</dt>
              <dd className="font-medium text-ink">
                {formatters.number(data.usage.tokens_remaining)}
              </dd>
            </div>
            <div>
              <dt className="text-subtle">{t("usage.total")}</dt>
              <dd className="font-medium text-ink">
                {formatters.number(data.usage.tokens_total)}
              </dd>
            </div>
            <div>
              <dt className="text-subtle">{t("usage.resetAt")}</dt>
              <dd className="font-medium text-ink">{resetDate}</dd>
            </div>
          </dl>
          {data.usage.is_demo ? (
            <p className="mt-4 rounded-md bg-muted px-3 py-2 text-sm text-subtle">
              {t("usage.demo")}
            </p>
          ) : null}
          <div className="mt-4 border-t border-border pt-4">
            <h3 className="text-sm font-semibold text-ink">{t("usage.actualTitle")}</h3>
            <p className="mt-1 text-xs text-subtle">{t("usage.actualDescription")}</p>
            <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-subtle">{t("usage.actualTokens")}</dt>
                <dd className="font-medium text-ink">
                  {formatters.number(actualUsage.total_tokens_used)}
                </dd>
              </div>
              <div>
                <dt className="text-subtle">{t("usage.actualAudits")}</dt>
                <dd className="font-medium text-ink">
                  {formatters.number(actualUsage.audit_count)}
                </dd>
              </div>
              <div>
                <dt className="text-subtle">{t("usage.actualRuns")}</dt>
                <dd className="font-medium text-ink">
                  {formatters.number(actualUsage.run_count)}
                </dd>
              </div>
              <div>
                <dt className="text-subtle">{t("usage.webSearchRequests")}</dt>
                <dd className="font-medium text-ink">
                  {formatters.number(actualUsage.web_search_requests)}
                </dd>
              </div>
            </dl>
          </div>
        </section>

        <section className="rounded-md border border-border bg-surface p-5 shadow-panel">
          <h2 className="text-base font-semibold text-ink">{t("notifications.title")}</h2>
          <form
            className="mt-4 space-y-4 text-sm"
            onSubmit={(event) => {
              event.preventDefault();
              if (draftPreferences) {
                updatePreferences.mutate(draftPreferences);
              }
            }}
          >
            <label className="flex items-center justify-between gap-3 rounded-md border border-border px-3 py-2">
              <span>
                <span className="block font-medium text-ink">
                  {t("notifications.email")}
                </span>
                <span className="text-subtle">
                  {yesNo(preferences.email_notifications, t("enabled"), t("disabled"))}
                </span>
              </span>
              <input
                type="checkbox"
                checked={preferences.email_notifications}
                onChange={(event) =>
                  setPreference("email_notifications", event.target.checked)
                }
              />
            </label>
            <label className="flex items-center justify-between gap-3 rounded-md border border-border px-3 py-2">
              <span>
                <span className="block font-medium text-ink">
                  {t("notifications.auditCompleted")}
                </span>
                <span className="text-subtle">
                  {yesNo(
                    preferences.audit_completed_notifications,
                    t("enabled"),
                    t("disabled"),
                  )}
                </span>
              </span>
              <input
                type="checkbox"
                checked={preferences.audit_completed_notifications}
                onChange={(event) =>
                  setPreference("audit_completed_notifications", event.target.checked)
                }
              />
            </label>
            <label className="flex items-center justify-between gap-3 rounded-md border border-border px-3 py-2">
              <span>
                <span className="block font-medium text-ink">
                  {t("notifications.providerError")}
                </span>
                <span className="text-subtle">
                  {yesNo(
                    preferences.provider_error_notifications,
                    t("enabled"),
                    t("disabled"),
                  )}
                </span>
              </span>
              <input
                type="checkbox"
                checked={preferences.provider_error_notifications}
                onChange={(event) =>
                  setPreference("provider_error_notifications", event.target.checked)
                }
              />
            </label>
            <label className="block space-y-1">
              <span className="font-medium text-ink">{t("preferences.locale")}</span>
              <select
                className="w-full rounded-md border border-border bg-surface px-3 py-2 text-ink"
                value={preferences.locale}
                onChange={(event) =>
                  setPreference(
                    "locale",
                    event.target.value as ProfilePreferences["locale"],
                  )
                }
              >
                {supportedLocales.map((locale) => (
                  <option key={locale.code} value={locale.code}>
                    {t(locale.labelKey, { ns: "common" })}
                  </option>
                ))}
              </select>
            </label>
            {updatePreferences.isError ? (
              <p className="text-sm text-red-700">{t("preferences.saveError")}</p>
            ) : null}
            {saveMessage ? (
              <p className="text-sm font-medium text-brand-700">
                {t("preferences.saved")}
              </p>
            ) : null}
            <div className="flex flex-wrap gap-2">
              <Button
                type="submit"
                disabled={!hasUnsavedChanges || updatePreferences.isPending}
              >
                {updatePreferences.isPending ? t("preferences.saving") : t("preferences.save")}
              </Button>
              <Button
                type="button"
                variant="secondary"
                disabled={!hasUnsavedChanges || updatePreferences.isPending}
                onClick={() => {
                  setDraftPreferences(data.preferences);
                  setSaveMessage(null);
                }}
              >
                {t("preferences.cancel")}
              </Button>
            </div>
          </form>
        </section>
      </div>
    </section>
  );
}
