import { I18nextProvider } from "react-i18next";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { LanguageSwitcher } from "./LanguageSwitcher";
import {
  createI18nInstance,
  fallbackLocale,
  localeStorageKey,
  normalizeLocale,
  supportedLocales,
} from "../../lib/i18n/config";

async function renderSwitcher(locale = "en") {
  const i18n = await createI18nInstance(locale);
  render(
    <I18nextProvider i18n={i18n}>
      <LanguageSwitcher />
    </I18nextProvider>,
  );
  return i18n;
}

describe("LanguageSwitcher", () => {
  it("renders configured locales", async () => {
    await renderSwitcher();

    const select = await screen.findByLabelText("Interface language");
    expect(select).toBeInTheDocument();
    expect(supportedLocales.map((locale) => locale.code)).toEqual(["en", "ru"]);
    expect(screen.getByRole("option", { name: "English" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Russian" })).toBeInTheDocument();
  });

  it("switches locale and persists selection", async () => {
    localStorage.clear();
    const user = userEvent.setup();
    const i18n = await renderSwitcher();

    await user.selectOptions(screen.getByLabelText("Interface language"), "ru");

    await waitFor(() => expect(i18n.language).toBe("ru"));
    expect(localStorage.getItem(localeStorageKey)).toBe("ru");
    expect(screen.getByRole("option", { name: "Русский" })).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Язык интерфейса"), "en");
    await waitFor(() => expect(i18n.language).toBe("en"));
    expect(localStorage.getItem(localeStorageKey)).toBe("en");
  });

  it("falls back from invalid locale values", () => {
    expect(normalizeLocale("xx")).toBe(fallbackLocale);
  });
});
