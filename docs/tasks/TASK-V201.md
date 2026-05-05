# TASK-V201 — Define Web5 Summary UI Implementation Contract

## Goal

Define how the Web5-style audit summary screen should be implemented using existing backend contracts.

This task is documentation/contract only. Do not change runtime code.

---

## Context

The target Web5 screen includes:

```text
Header/action area
"What was tested" collapsible section
General summary cards
Mentionability L1/L2
Accuracy L1/L2
Tone/sentiment
Model summary section
Actions: rerun fact-checking, DOCX, Excel, repeat audit
```

The UI must consume backend data from Results v2 and Evaluation contracts. Frontend must not calculate scoring, parsing, source classification, or competitor logic.

---

## File to create/update

Preferred new file:

```text
docs/WEB5_SUMMARY_UI_CONTRACT.md
```

If UI contracts are centralized elsewhere, update:

```text
docs/FRONTEND_CONTEXT.md
docs/PRODUCT_SPEC.md
docs/TASKS.md
```

---

## Required decisions

### 1. Data source

Document that Web5 summary uses backend-provided endpoints:

```text
GET /audits/{id}/summary-v2
POST /audits/{id}/rerun-evaluation
```

Optional/future:

```text
DOCX export endpoint
Excel export endpoint
Repeat audit endpoint
```

### 2. UI sections

Document sections:

```text
Audit header
Tested scope
General summary cards
Model summary
Actions
Diagnostics/empty states
```

### 3. Metrics

Document that frontend displays backend metrics only:

```text
mentionability_l1
mentionability_l2
accuracy_l1
accuracy_l2
tone/sentiment
model summaries
deltas
```

Frontend must not calculate score/accuracy/mentionability.

### 4. Evaluation dependency

Document:

```text
Accuracy is based on AnswerEvaluation records.
If evaluation is unavailable, accuracy shows N/A / Not evaluated.
```

### 5. Actions

Document MVP behavior:

```text
Rerun fact-checking: real action if backend endpoint exists
DOCX: stub or disabled if export not implemented
Excel: stub or disabled if export not implemented
Repeat audit: stub or existing rerun/duplicate action if implemented
```

### 6. i18n

Document:

```text
All static labels must use translation keys.
Raw AI answers, query text, brand description, and source snippets must not be translated.
The implementation must support future locales beyond en/ru.
```

---

## Testing plan to document

Frontend tests:

```text
renders header
renders tested scope
renders summary cards
renders model summaries
handles null accuracy
handles partial audit
handles provider diagnostics
rerun fact-checking action
DOCX/Excel disabled or wired correctly
i18n labels
responsive layout
```

---

## Acceptance criteria

- Web5 summary UI contract exists.
- Data sources are documented.
- UI sections are documented.
- Metrics and frontend/backend responsibility are documented.
- Evaluation unavailable state is documented.
- Actions are documented.
- i18n and raw-content rules are documented.
- No runtime code changed.

---

## Non-goals

- Do not implement summary UI.
- Do not implement exports.
- Do not implement rerun evaluation backend.
- Do not change backend DTOs.
- Do not change parser/scoring.
