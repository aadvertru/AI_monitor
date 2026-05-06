import { describe, expect, it } from "vitest";

import {
  createI18nInstance,
  fallbackLocale,
  localeStorageKey,
  normalizeLocale,
  persistLocale,
  readStoredLocale,
  supportedLocales,
} from "./config";

describe("i18n config", () => {
  it("renders known keys in English and Russian", async () => {
    const i18n = await createI18nInstance("en");
    expect(i18n.t("actions.save")).toBe("Save");

    await i18n.changeLanguage("ru");
    expect(i18n.t("actions.save")).toBe("Сохранить");
  });

  it("falls back to English for unsupported locales", async () => {
    const i18n = await createI18nInstance("zz");
    expect(i18n.language).toBe(fallbackLocale);
    expect(i18n.t("actions.refresh")).toBe("Refresh");
  });

  it("keeps missing keys safe", async () => {
    const i18n = await createI18nInstance("en");
    expect(i18n.t("common:missing.deep.key")).toBe("missing.deep.key");
  });

  it("normalizes and persists locale through configured locale list", () => {
    const storage = new Map<string, string>();
    const storageLike = {
      getItem: (key: string) => storage.get(key) ?? null,
      setItem: (key: string, value: string) => storage.set(key, value),
    };

    expect(supportedLocales.map((locale) => locale.code)).toContain("ru");
    expect(normalizeLocale("de")).toBe("en");
    expect(persistLocale("ru", storageLike)).toBe("ru");
    expect(storage.get(localeStorageKey)).toBe("ru");
    expect(readStoredLocale(storageLike)).toBe("ru");
  });
});
