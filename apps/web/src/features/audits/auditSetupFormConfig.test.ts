import { describe, expect, it } from "vitest";

import {
  appendGeneratedSeedQueries,
  buildPayload,
  estimateAuditTokens,
  schema,
} from "./auditSetupFormConfig";

describe("seed query append behavior", () => {
  it("adds unique generated suggestions to the end without replacing manual queries", () => {
    const result = appendGeneratedSeedQueries(
      [{ text: "manual query", type: null, source: "user" }],
      [
        {
          text: "generated query",
          type: "recommendation",
          source: "ai",
        },
      ],
    );

    expect(result.queries).toEqual([
      { text: "manual query", type: null, source: "user" },
      { text: "generated query", type: "recommendation", source: "ai" },
    ]);
    expect(result.duplicateCount).toBe(0);
    expect(result.limitSkipped).toBe(0);
  });

  it("skips normalized duplicates defensively", () => {
    const result = appendGeneratedSeedQueries(
      [{ text: "Best AI Tools", type: null, source: "user" }],
      [
        {
          text: " best   ai tools ",
          type: "category_discovery",
          source: "ai",
        },
      ],
    );

    expect(result.queries).toEqual([{ text: "Best AI Tools", type: null, source: "user" }]);
    expect(result.duplicateCount).toBe(1);
    expect(result.limitSkipped).toBe(0);
  });

  it("respects the max total count of 20", () => {
    const currentQueries = Array.from({ length: 19 }, (_, index) => ({
      text: `manual query ${index + 1}`,
      type: null,
      source: "user" as const,
    }));

    const result = appendGeneratedSeedQueries(currentQueries, [
      { text: "generated query 1", type: "alternative", source: "ai" },
      { text: "generated query 2", type: "comparison", source: "ai" },
    ]);

    expect(result.queries).toHaveLength(20);
    expect(result.queries.at(-1)).toEqual({
      text: "generated query 1",
      type: "alternative",
      source: "ai",
    });
    expect(result.limitSkipped).toBe(1);
  });

  it("ignores empty generated suggestions without counting them as duplicates", () => {
    const result = appendGeneratedSeedQueries(
      [{ text: "manual query", type: null, source: "user" }],
      [
        { text: "   ", type: "alternative", source: "ai" },
        { text: "manual query", type: "comparison", source: "ai" },
      ],
    );

    expect(result.queries).toEqual([{ text: "manual query", type: null, source: "user" }]);
    expect(result.duplicateCount).toBe(1);
    expect(result.limitSkipped).toBe(0);
  });
});

describe("audit setup form schema", () => {
  const validValues = {
    brandName: "Acme",
    brandDomain: "acme.example",
    brandDescription: "",
    seedQueryItems: [{ text: "valid query", type: null, source: "user" }],
    modelTargets: [
      {
        aiFamily: "chatgpt",
        executionProvider: "openrouter",
        modelProvider: "openai",
        modelId: "openai/gpt-4o-mini",
        displayName: "GPT-4o mini",
        level: "L1",
      },
    ],
    providers: ["mock"],
    language: "en",
    country: "US",
    maxQueries: "",
    enableSourceIntelligence: false,
    scdlLevel: "L1",
  };

  it("rejects a form with only empty seed query rows", () => {
    const result = schema.safeParse({
      ...validValues,
      seedQueryItems: [{ text: "", type: null, source: "user" }],
    });

    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0]?.message).toBe("Add at least one seed query.");
    }
  });

  it("rejects non-empty seed query rows shorter than three characters", () => {
    const result = schema.safeParse({
      ...validValues,
      seedQueryItems: [{ text: "ab", type: null, source: "user" }],
    });

    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0]?.message).toBe("Seed query must be at least 3 characters.");
    }
  });

  it("ignores source intelligence cost for L1", () => {
    expect(
      estimateAuditTokens({
        enableSourceIntelligence: true,
        providers: ["openai"],
        scdlLevel: "L1",
        seedQueryItems: [{ text: "valid query", type: null, source: "user" }],
      }),
    ).toBe(10);
  });

  it("forces source intelligence off in L1 payloads", () => {
    const values = schema.parse({
      ...validValues,
      enableSourceIntelligence: true,
      scdlLevel: "L1",
    });

    expect(buildPayload(values)).toMatchObject({
      enable_source_intelligence: false,
    });
  });
});
