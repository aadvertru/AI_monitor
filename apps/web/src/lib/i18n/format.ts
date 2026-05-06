import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import { fallbackLocale, normalizeLocale } from "./config";

const fallbackText = "N/A";

function toDate(value: Date | string | number | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const date = value instanceof Date ? value : new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function createLocaleFormatters(localeInput?: string) {
  const locale = normalizeLocale(localeInput ?? fallbackLocale);

  return {
    locale,
    dateTime(value: Date | string | number | null | undefined) {
      const date = toDate(value);
      if (!date) {
        return fallbackText;
      }
      return new Intl.DateTimeFormat(locale, {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(date);
    },
    number(value: number | null | undefined) {
      if (value === null || value === undefined || !Number.isFinite(value)) {
        return fallbackText;
      }
      return new Intl.NumberFormat(locale).format(value);
    },
    percent(value: number | null | undefined) {
      if (value === null || value === undefined || !Number.isFinite(value)) {
        return fallbackText;
      }
      return new Intl.NumberFormat(locale, {
        maximumFractionDigits: 0,
        style: "percent",
      }).format(value);
    },
    decimal(value: number | null | undefined, fractionDigits = 2) {
      if (value === null || value === undefined || !Number.isFinite(value)) {
        return fallbackText;
      }
      return new Intl.NumberFormat(locale, {
        maximumFractionDigits: fractionDigits,
        minimumFractionDigits: fractionDigits,
      }).format(value);
    },
  };
}

export function useLocaleFormatters() {
  const { i18n } = useTranslation();
  const locale = normalizeLocale(i18n.resolvedLanguage ?? i18n.language);
  return useMemo(() => createLocaleFormatters(locale), [locale]);
}
