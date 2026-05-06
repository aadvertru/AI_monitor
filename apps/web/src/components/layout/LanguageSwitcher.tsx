import { useTranslation } from "react-i18next";

import {
  normalizeLocale,
  persistLocale,
  supportedLocales,
} from "../../lib/i18n/config";

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation("common");
  const currentLocale = normalizeLocale(i18n.resolvedLanguage ?? i18n.language);

  return (
    <label className="inline-flex items-center gap-2 text-sm text-subtle">
      <span className="sr-only">{t("language.switcherLabel")}</span>
      <select
        aria-label={t("language.switcherLabel")}
        className="rounded-md border border-border bg-surface px-2 py-1 text-sm text-ink"
        value={currentLocale}
        onChange={(event) => {
          const nextLocale = persistLocale(event.target.value);
          void i18n.changeLanguage(nextLocale);
        }}
      >
        {supportedLocales.map((locale) => (
          <option key={locale.code} value={locale.code}>
            {t(locale.labelKey)}
          </option>
        ))}
      </select>
    </label>
  );
}
