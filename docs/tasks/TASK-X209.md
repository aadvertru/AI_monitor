# TASK-X209 — Add Export Verification Checklist

## Goal

Create a manual QA checklist for DOCX/Excel exports and Repeat Audit.

This task is documentation-only. Do not change runtime code.

---

## File to create

```text
docs/EXPORTS_VERIFICATION.md
```

---

## Required scenarios

Use standard scenario format with purpose, preconditions, steps, expected result, actual result, status, and issue ID.

Scenarios:

```text
X-S01 — Excel export for completed audit
X-S02 — Excel export for partial audit
X-S03 — DOCX export for completed audit
X-S04 — DOCX export for partial audit
X-S05 — Export with no evaluation
X-S06 — Export with no sources
X-S07 — Export includes model summary
X-S08 — Export includes answer matrix/report section
X-S09 — Export includes source domains
X-S10 — Export includes concepts/competitors
X-S11 — Export does not include raw provider data
X-S12 — Non-owner cannot download export
X-S13 — Repeat audit copies configuration only
X-S14 — Repeat audit does not copy results
```

---

## Result table

Include standard result table with `Not run | Pass | Fail | Blocked | Partial`.

---

## Captured issues section

Use standard issue template.

---

## Acceptance criteria

- `docs/EXPORTS_VERIFICATION.md` exists.
- Scenarios X-S01 through X-S14 included.
- Result table included.
- Captured issue template included.
- Checklist verifies export content, auth, safety, repeat audit behavior.
- No runtime code changed.

---

## Non-goals

- Do not run checklist.
- Do not fix export bugs.
