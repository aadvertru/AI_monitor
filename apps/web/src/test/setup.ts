import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";

import { appI18n, fallbackLocale, localeStorageKey } from "../lib/i18n/config";

afterEach(() => {
  localStorage.removeItem(localeStorageKey);
  void appI18n.changeLanguage(fallbackLocale);
});
