# TASK-N209 — Add Model Catalog and Target Selector Verification Checklist

## Goal

Create a manual QA checklist for model catalog and audit target selector.

This task is documentation-only. Do not change runtime code.

---

## File to create

```text
docs/MODEL_CATALOG_SELECTOR_VERIFICATION.md
```

---

## Required scenarios

Use standard scenario format.

Scenarios:

```text
N-S01 — Model catalog loads
N-S02 — Catalog cache works or cache metadata visible
N-S03 — ChatGPT family default block renders
N-S04 — Model multiselect works
N-S05 — Plus button adds another AI family
N-S06 — L1/L2 toggles create correct targets
N-S07 — Experimental L2 marker visible
N-S08 — Unsupported L2 disabled
N-S09 — Create audit saves modelTargets
N-S10 — Edit audit loads modelTargets
N-S11 — Legacy audit still editable
N-S12 — Run estimate correct
N-S13 — Over-cap validation shown
N-S14 — No arbitrary model id can execute
```

---

## Result table

Include result table with `Not run | Pass | Fail | Blocked | Partial`.

---

## Captured issues section

Use standard issue template.

---

## Acceptance criteria

- Checklist file exists.
- Scenarios N-S01 through N-S14 included.
- Result table included.
- Captured issue template included.
- Checklist verifies catalog, selector, modelTargets, caps, and legacy compatibility.
- No runtime code changed.

---

## Non-goals

- Do not run checklist.
- Do not fix bugs.
