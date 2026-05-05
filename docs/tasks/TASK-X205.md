# TASK-X205 — Add Export Download API Endpoints

## Goal

Add authenticated owner-only API endpoints for downloading Excel and DOCX audit exports.

---

## Scope

Implement:

```text
GET /audits/{id}/exports/excel
GET /audits/{id}/exports/docx
auth/ownership guard
safe file response
filename generation
task-scoped backend/API tests
```

---

## Endpoints

```http
GET /audits/{id}/exports/excel
GET /audits/{id}/exports/docx
```

Use existing route conventions if different.

---

## Rules

- Requires login.
- Enforces audit ownership.
- Uses Excel/DOCX generators from previous tasks.
- Does not expose raw provider responses.
- Filename must be safe and sanitized.
- Exports should work for completed and partial audits.
- Failed/no-data audits may return safe export with available sections or 422 according to product decision.

Recommended:

```text
allow export for completed/partial audits
allow export for failed audits if there is any reportable data
otherwise return safe 422
```

---

## Response headers

Set appropriate content type:

```text
Excel: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
DOCX: application/vnd.openxmlformats-officedocument.wordprocessingml.document
```

Set safe content-disposition filename.

---

## Tests

Backend/API tests:

```text
unauthenticated rejected
non-owner rejected
owner can download Excel
owner can download DOCX
content type correct
filename safe
completed audit export works
partial audit export works
no-data audit safe behavior
no raw provider/secrets in file
```

---

## Acceptance criteria

- Excel export endpoint exists.
- DOCX export endpoint exists.
- Auth/ownership enforced.
- File responses have correct content types.
- Filenames safe.
- No raw provider payloads/secrets included.
- Task-scoped backend/API tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement frontend buttons.
- Do not add async export jobs.
- Do not implement PDF.
- Do not change result aggregation.
