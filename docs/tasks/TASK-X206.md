# TASK-X206 — Wire Frontend Export Buttons

## Goal

Wire DOCX and Excel buttons in the Web5 summary UI to backend export endpoints.

---

## Scope

Implement:

```text
frontend API download helpers
DOCX button wiring
Excel button wiring
loading/error states
safe filename/download handling
task-scoped frontend tests
```

---

## Endpoints

Use:

```http
GET /audits/{id}/exports/excel
GET /audits/{id}/exports/docx
```

---

## UX behavior

- Button shows loading state during download.
- Button disabled while request is active.
- Safe error displayed on failure.
- Do not display raw response body.
- If endpoint unavailable, show disabled state with explanatory tooltip.

---

## Tests

Frontend tests:

```text
Excel button calls export endpoint
DOCX button calls export endpoint
loading state works
download handler invoked
safe error state works
buttons disabled when audit has no exportable data if applicable
raw API error not displayed
```

---

## Acceptance criteria

- Excel download button works.
- DOCX download button works.
- Loading/error states work.
- No raw API/provider payload displayed.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement backend export endpoints.
- Do not implement PDF.
- Do not redesign summary page.
- Do not implement export history.
