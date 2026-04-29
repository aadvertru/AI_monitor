import { describe, expect, it } from "vitest";

import type { AuditStatus, RunStatus, SCDLLevel } from "../lib/api/types";
import {
  auditListFixture,
  auditResultsFixture,
  auditSummaryFixture,
  currentUserFixture,
  emptyAuditResultsFixture,
  emptyAuditSummaryFixture,
  failedAuditSummaryFixture,
  partialAuditSummaryFixture,
} from "./fixtures";

const documentedAuditStatuses = new Set<AuditStatus>([
  "created",
  "running",
  "partial",
  "completed",
  "failed",
]);
const documentedRunStatuses = new Set<RunStatus>([
  "pending",
  "success",
  "error",
  "timeout",
  "rate_limited",
]);
const documentedScdlLevels = new Set<SCDLLevel>(["L1", "L2"]);

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
  });

  it("covers results, competitors, critical queries, and source citations", () => {
    expect(auditResultsFixture.rows.some((row) => row.run_status === "success")).toBe(true);
    expect(auditResultsFixture.rows.some((row) => row.run_status === "error")).toBe(true);
    expect(auditResultsFixture.rows.some((row) => row.run_status === "timeout")).toBe(true);
    for (const row of auditResultsFixture.rows) {
      expect(documentedRunStatuses.has(row.run_status)).toBe(true);
      expect(documentedScdlLevels.has(row.scdl_level)).toBe(true);
    }

    expect(auditSummaryFixture.competitors.length).toBeGreaterThan(0);
    expect(auditSummaryFixture.critical_queries.length).toBeGreaterThan(0);
    expect(auditSummaryFixture.sources.length).toBeGreaterThan(0);
    expect(emptyAuditSummaryFixture.sources).toHaveLength(0);
  });
});
