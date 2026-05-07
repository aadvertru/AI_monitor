import { describe, expect, it } from "vitest";

import type {
  AuditStatus,
  ProviderDiagnosticCode,
  RunStatus,
  SCDLLevel,
} from "../lib/api/types";
import {
  auditDetailWithModelTargetsFixture,
  auditAnswerMatrixFixture,
  auditListFixture,
  auditPipelineRunFixture,
  auditResultsFixture,
  auditSummaryV2Fixture,
  auditSummaryFixture,
  auditTargetWireFixture,
  completedAuditSummaryV2Fixture,
  createAuditModelTargetsPayloadFixture,
  createAuditModelTargetsWireFixture,
  currentUserFixture,
  emptyAuditResultsFixture,
  emptyAuditSummaryFixture,
  failedAuditSummaryFixture,
  failedAuditSummaryV2Fixture,
  l1OnlyAuditSummaryV2Fixture,
  legacyAuditDetailWithoutModelTargetsFixture,
  openRouterL2AuditTargetWireFixture,
  partialAuditSummaryFixture,
  sourceDomainsFixture,
} from "./fixtures";

const documentedAuditStatuses = new Set<AuditStatus>([
  "created",
  "running",
  "partial",
  "completed",
  "failed",
  "cancelled",
]);
const documentedRunStatuses = new Set<RunStatus>([
  "pending",
  "success",
  "error",
  "timeout",
  "rate_limited",
]);
const documentedScdlLevels = new Set<SCDLLevel>(["L1", "L2"]);
const documentedProviderDiagnosticCodes = new Set<ProviderDiagnosticCode>([
  "PROVIDER_DISABLED",
  "NO_API_KEY",
  "INVALID_API_KEY",
  "INVALID_MODEL",
  "UNSUPPORTED_L2",
  "TIMEOUT",
  "RATE_LIMIT",
  "EMPTY_RESPONSE",
  "INVALID_RESPONSE",
  "PROVIDER_UNAVAILABLE",
  "PROVIDER_REQUEST_FAILED",
  "CONFIGURATION_ERROR",
  "UNKNOWN_PROVIDER_ERROR",
]);

describe("frontend-backend contract fixtures", () => {
  it("uses documented auth and audit status values only", () => {
    expect(currentUserFixture).not.toHaveProperty("password");
    expect(currentUserFixture).not.toHaveProperty("token");

    for (const audit of auditListFixture) {
      expect(documentedAuditStatuses.has(audit.status)).toBe(true);
      expect(documentedScdlLevels.has(audit.scdl_level)).toBe(true);
    }

    for (const summary of [
      auditSummaryFixture,
      emptyAuditSummaryFixture,
      partialAuditSummaryFixture,
      failedAuditSummaryFixture,
    ]) {
      expect(documentedAuditStatuses.has(summary.status)).toBe(true);
    }
  });

  it("covers successful, empty, partial, and failed audit response shapes", () => {
    expect(auditSummaryFixture.status).toBe("completed");
    expect(emptyAuditSummaryFixture.status).toBe("created");
    expect(partialAuditSummaryFixture.status).toBe("partial");
    expect(failedAuditSummaryFixture.status).toBe("failed");
    expect(emptyAuditResultsFixture.rows).toHaveLength(0);
    expect(auditPipelineRunFixture.final_audit_status).toBe("completed");
    expect(auditPipelineRunFixture.execution?.success_count).toBeGreaterThan(0);
  });

  it("covers results, competitors, critical queries, and source citations", () => {
    expect(auditResultsFixture.rows.some((row) => row.run_status === "success")).toBe(true);
    expect(auditResultsFixture.rows.some((row) => row.run_status === "error")).toBe(true);
    expect(auditResultsFixture.rows.some((row) => row.run_status === "timeout")).toBe(true);
    expect(auditResultsFixture.rows[0]?.concepts?.[0]?.text).toBe(
      "AI visibility benchmarks",
    );
    expect(auditResultsFixture.rows[0]?.competitor_candidates?.[0]?.name).toBe(
      "Contoso Monitor",
    );
    for (const row of auditResultsFixture.rows) {
      expect(documentedRunStatuses.has(row.run_status)).toBe(true);
      expect(documentedScdlLevels.has(row.scdl_level)).toBe(true);
      if (row.provider_error) {
        expect(documentedProviderDiagnosticCodes.has(row.provider_error.code)).toBe(true);
      }
    }

    expect(auditSummaryFixture.competitors.length).toBeGreaterThan(0);
    expect(auditSummaryFixture.critical_queries.length).toBeGreaterThan(0);
    expect(auditSummaryFixture.sources.length).toBeGreaterThan(0);
    expect(emptyAuditSummaryFixture.sources).toHaveLength(0);
  });

  it("covers canonical and legacy audit target response fixtures", () => {
    expect(auditTargetWireFixture.execution_provider).toBe("openrouter");
    expect(auditTargetWireFixture.gateway_l2_experimental).toBe(false);
    expect(openRouterL2AuditTargetWireFixture.level).toBe("L2");
    expect(openRouterL2AuditTargetWireFixture.gateway_l2_experimental).toBe(true);

    expect(auditDetailWithModelTargetsFixture.model_targets).toHaveLength(2);
    expect(auditDetailWithModelTargetsFixture.model_targets?.[1]?.gateway_l2_experimental).toBe(
      true,
    );
    expect(legacyAuditDetailWithoutModelTargetsFixture.model_targets).toBeUndefined();
  });

  it("covers results v2 summary, matrix, and source-domain fixtures", () => {
    expect(auditSummaryV2Fixture.overall.accuracy_l1).toBeNull();
    expect(auditSummaryV2Fixture.overall.accuracy_l2).toBeNull();
    expect(auditSummaryV2Fixture.concepts).toEqual([]);
    expect(auditSummaryV2Fixture.competitor_candidates).toEqual([]);
    expect(auditSummaryV2Fixture.model_summaries[0]?.execution_provider).toBe("openrouter");

    expect(auditAnswerMatrixFixture.columns[1]?.gateway_l2_experimental).toBe(true);
    expect(auditAnswerMatrixFixture.rows[0]?.cells[0]?.evaluation?.verdict).toBe("partial");
    expect(auditAnswerMatrixFixture.rows[0]?.cells[1]?.provider_error?.code).toBe("TIMEOUT");

    expect(sourceDomainsFixture.domains[0]?.domain).toBe("example.com");
    expect(sourceDomainsFixture.domains[0]?.urls[0]?.gateway_l2_experimental).toBe(true);
    expect(sourceDomainsFixture.warnings).toContain("Skipped 1 invalid source URL(s).");

    const dumped = JSON.stringify({
      auditSummaryV2Fixture,
      auditAnswerMatrixFixture,
      sourceDomainsFixture,
    });
    expect(dumped).not.toContain("raw_answer");
    expect(dumped).not.toContain("request_snapshot");
    expect(dumped).not.toContain("api_key");
    expect(dumped).not.toContain("authorization");
  });

  it("covers Web5 summary UI fixture states", () => {
    const web5Fixtures = [
      auditSummaryV2Fixture,
      completedAuditSummaryV2Fixture,
      failedAuditSummaryV2Fixture,
      l1OnlyAuditSummaryV2Fixture,
    ];

    for (const fixture of web5Fixtures) {
      expect(documentedAuditStatuses.has(fixture.status)).toBe(true);
      for (const level of fixture.totals.levels) {
        expect(documentedScdlLevels.has(level)).toBe(true);
      }
      for (const diagnostic of fixture.provider_diagnostics ?? []) {
        expect(documentedProviderDiagnosticCodes.has(diagnostic.code)).toBe(true);
      }
    }

    expect(completedAuditSummaryV2Fixture.status).toBe("completed");
    expect(completedAuditSummaryV2Fixture.overall.accuracy_l1).not.toBeNull();
    expect(auditSummaryV2Fixture.status).toBe("partial");
    expect(auditSummaryV2Fixture.overall.accuracy_l1).toBeNull();
    expect(failedAuditSummaryV2Fixture.status).toBe("failed");
    expect(failedAuditSummaryV2Fixture.provider_diagnostics).toHaveLength(1);
    expect(l1OnlyAuditSummaryV2Fixture.totals.levels).toEqual(["L1"]);
    expect(l1OnlyAuditSummaryV2Fixture.overall.mentionability_l2.percentage).toBeNull();
  });

  it("keeps frontend create fixture separate from backend wire payload shape", () => {
    expect(createAuditModelTargetsPayloadFixture.modelTargets).toHaveLength(2);
    expect(createAuditModelTargetsPayloadFixture).not.toHaveProperty("model_targets");
    expect(createAuditModelTargetsWireFixture.model_targets).toHaveLength(2);
    expect(createAuditModelTargetsWireFixture).not.toHaveProperty("modelTargets");
  });
});
