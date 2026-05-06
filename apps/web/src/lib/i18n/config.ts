import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import enAudits from "./locales/en/audits.json";
import enAuth from "./locales/en/auth.json";
import enCommon from "./locales/en/common.json";
import enErrors from "./locales/en/errors.json";
import enNavigation from "./locales/en/navigation.json";
import enProfile from "./locales/en/profile.json";
import enProviders from "./locales/en/providers.json";
import enResults from "./locales/en/results.json";
import ruAudits from "./locales/ru/audits.json";
import ruAuth from "./locales/ru/auth.json";
import ruCommon from "./locales/ru/common.json";
import ruErrors from "./locales/ru/errors.json";
import ruNavigation from "./locales/ru/navigation.json";
import ruProfile from "./locales/ru/profile.json";
import ruProviders from "./locales/ru/providers.json";
import ruResults from "./locales/ru/results.json";

export const fallbackLocale = "en";

export const supportedLocales = [
  { code: "en", labelKey: "language.english" },
  { code: "ru", labelKey: "language.russian" },
] as const;

export type SupportedLocale = (typeof supportedLocales)[number]["code"];

export const localeStorageKey = "ai-monitor.locale";

export const defaultNamespace = "common";

export const namespaces = [
  "common",
  "navigation",
  "auth",
  "audits",
  "profile",
  "results",
  "providers",
  "errors",
] as const;

export function isSupportedLocale(value: string | null | undefined): value is SupportedLocale {
  return supportedLocales.some((locale) => locale.code === value);
}

export function normalizeLocale(value: string | null | undefined): SupportedLocale {
  return isSupportedLocale(value) ? value : fallbackLocale;
}

export function readStoredLocale(storage: Pick<Storage, "getItem"> | undefined = globalThis.localStorage) {
  try {
    return normalizeLocale(storage?.getItem(localeStorageKey));
  } catch {
    return fallbackLocale;
  }
}

export function persistLocale(
  locale: string,
  storage: Pick<Storage, "setItem"> | undefined = globalThis.localStorage,
) {
  const normalized = normalizeLocale(locale);
  try {
    storage?.setItem(localeStorageKey, normalized);
  } catch {
    // Locale persistence is a convenience; failing storage must not break the app.
  }
  return normalized;
}

export const resources = {
  en: {
    common: enCommon,
    navigation: enNavigation,
    auth: enAuth,
    audits: enAudits,
    profile: enProfile,
    results: enResults,
    providers: enProviders,
    errors: enErrors,
  },
  ru: {
    common: ruCommon,
    navigation: ruNavigation,
    auth: ruAuth,
    audits: ruAudits,
    profile: ruProfile,
    results: ruResults,
    providers: ruProviders,
    errors: ruErrors,
  },
} as const;

export async function createI18nInstance(initialLocale: string = readStoredLocale()) {
  const instance = i18n.createInstance().use(initReactI18next);
  await instance.init({
    resources,
    lng: normalizeLocale(initialLocale),
    fallbackLng: fallbackLocale,
    defaultNS: defaultNamespace,
    ns: [...namespaces],
    interpolation: {
      escapeValue: false,
    },
    returnNull: false,
  });
  return instance;
}

export const appI18n = i18n.createInstance();

void appI18n.use(initReactI18next).init({
  resources,
  lng: readStoredLocale(),
  fallbackLng: fallbackLocale,
  defaultNS: defaultNamespace,
  ns: [...namespaces],
  interpolation: {
    escapeValue: false,
  },
  returnNull: false,
});
