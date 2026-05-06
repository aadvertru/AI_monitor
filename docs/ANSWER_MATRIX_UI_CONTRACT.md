# Answer Matrix UI Contract

## Purpose

The answer matrix is the Web6/Web7 audit view for comparing how each saved seed
query performs across the selected model/level targets.

The frontend must render backend-provided matrix data. It must not calculate
scores, evaluation verdicts, classifications, source intelligence, or provider
diagnostics.

## Data Source

The UI reads matrix data from:

```http
GET /audits/{id}/answer-matrix
```

The response is the source of truth for:

- matrix rows
- matrix columns
- cell status
- safe answer excerpts
- evaluation verdicts and rationales
- source counts
- provider diagnostics
- target/model/level metadata

## Matrix Shape

The matrix layout is:

```text
rows = saved seed queries / questions
columns = model + SCDL level targets
cells = answer state for one query x one target
```

Frontend rules:

- Render rows from backend `rows`.
- Render columns from backend `columns`.
- Align cells by `target_id`.
- Do not infer missing columns from provider names.
- Do not recalculate matrix shape from results.
- Missing cells render a safe placeholder.

## Layout

The UI should use a compact dashboard layout:

- sticky or fixed left question column where practical
- horizontal scroll for model columns
- columns grouped or labeled by model display name and SCDL level
- each cell includes status, safe answer excerpt, evaluation verdict badge,
  rationale preview, and source count where available
- each cell has an expand action for details

Long query text should wrap or truncate safely without breaking row alignment.
Many columns should remain usable through horizontal scrolling.

## Cell States

Cells must support these states:

- `completed`
- `failed`
- `partial`
- `not_run`
- `processing`
- `missing`

State handling:

- `completed`: show safe answer excerpt, verdict if available, rationale preview
  if available, and source count if available.
- `failed`: show failed status and safe provider diagnostic if available.
- `partial`: show partial status and the safe fields that exist.
- `not_run`, `processing`, `missing`: show a safe empty/progress placeholder.

Unknown states should render a safe fallback label and must not expose raw data.

## Verdict Display

Evaluation verdict codes:

- `correct`
- `partial`
- `incorrect`
- `unknown`
- `not_applicable`

The frontend translates labels through i18n keys. UI code must not hardcode
Russian-only labels.

Suggested English labels:

- `correct`: Correct
- `partial`: Partial
- `incorrect`: Incorrect
- `unknown`: Unknown
- `not_applicable`: Not applicable

Suggested Russian labels:

- `correct`: Верно
- `partial`: Частично
- `incorrect`: Неверно
- `unknown`: Неизвестно
- `not_applicable`: Неприменимо

Color may reinforce status, but text or an icon must also be present.

## Filters

Matrix filters are frontend view filters over the backend matrix response. They
must not mutate audit data or calculate scores.

Required filters:

- SCDL level
- AI family
- model
- verdict
- query type
- status

Filtering must preserve row/column alignment. Empty filtered results should show
a clear empty state.

## Expand Details

Expanded cell details may show:

- query text
- model/target label
- SCDL level
- cell status
- safe answer text if provided
- otherwise safe answer excerpt only
- evaluation verdict
- evaluation rationale
- evaluation confidence if provided
- provider diagnostic if failed
- source count and safe source links if provided
- concepts and competitor candidates if provided

Full answer text may only come from a safe normalized field or endpoint, for
example:

- `cell.safe_answer_text`
- `cell.answer_text`
- a safe result detail endpoint returning normalized `answer_text`

If no safe full-answer source exists, the UI must show excerpt-only details and
the missing backend capability should be escalated separately.

## Raw Content Safety

The matrix UI must never display:

- raw provider response
- raw prompt
- raw tool result
- raw annotations
- request headers
- authorization values
- API keys
- stack traces
- tracebacks

Answer excerpts and full answers may be shown only from safe normalized fields.
Provider diagnostics may be shown only through normalized safe diagnostic fields.

## Non-Goals

- Backend matrix redesign.
- Frontend scoring or evaluation logic.
- Raw response inspection.
- Exporting the matrix.
- Changing parser, scoring, provider, or source aggregation behavior.
