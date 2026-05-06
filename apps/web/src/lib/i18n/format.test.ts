import { describe, expect, it } from "vitest";

import { createLocaleFormatters } from "./format";

describe("locale formatters", () => {
  it("formats dates differently by locale", () => {
    const value = "2026-05-04T16:05:00Z";

    expect(createLocaleFormatters("en").dateTime(value)).not.toEqual(
      createLocaleFormatters("ru").dateTime(value),
    );
  });

  it("formats percents and large numbers through Intl", () => {
    expect(createLocaleFormatters("en").percent(0.42)).toBe("42%");
    expect(createLocaleFormatters("en").number(1234567)).toBe("1,234,567");
  });

  it("falls back from unsupported locales", () => {
    expect(createLocaleFormatters("xx").locale).toBe("en");
  });

  it("handles nullish and invalid values safely", () => {
    const formatters = createLocaleFormatters("en");

    expect(formatters.dateTime(null)).toBe("N/A");
    expect(formatters.dateTime("not-a-date")).toBe("N/A");
    expect(formatters.number(undefined)).toBe("N/A");
    expect(formatters.percent(Number.NaN)).toBe("N/A");
  });
});
