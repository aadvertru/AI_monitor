# TASK-U204 — Add Deterministic Competitor Candidate Extractor with EN/RU Patterns

## Status

Ready for implementation.

## Goal

Add a conservative deterministic competitor candidate extractor.

The extractor must support a minimal English and Russian competitive-context pattern set.

Do not use LLM classification in this task.

## Dependencies

Requires:

```text
TASK-U201
TASK-U202
TASK-U203
```

## Scope

Implement:

```text
competitor candidate extraction service
brand-like candidate detection
EN/RU competitive context detection
confidence calculation
evidence capture
task-scoped backend tests
```

## Mandatory competitive context signals

English:

```text
alternatives to
competitors of
vs
similar tools
similar services
best <category>
top <category>
```

Russian:

```text
альтернативы
конкуренты
похожие
похожие сервисы
похожие компании
лучшие
топ
сравнение
против
```

Keep pattern set small and deterministic.

## Brand-like signals

Candidate may be brand-like if:

```text
capitalized organization/product-like span
known domain nearby
matches user-provided competitor list if available
appears as named entity from existing extractor if available
has suffix/pattern indicating company/product/service brand
```

Avoid classifying generic phrases as competitors.

## Confidence

Use simple deterministic score:

```text
0.9 known competitor list match + comparison context
0.8 domain + comparison context
0.7 brand-like name + comparison context
0.5 brand-like name in category list
below threshold -> discard
```

Threshold:

```text
confidence >= 0.6
```

Document formula in code/comments.

## Evidence

Store:

```text
query_id
run_id
target_id
answer_excerpt
matched_phrase
evidence_type
level
model_id
language/pattern if available
```

Do not store full raw provider response.

## Tests

Backend tests:

```text
English alternative context extracts competitor
English vs context extracts competitor
Russian альтернативы context extracts competitor
Russian конкуренты context extracts competitor
Russian похожие context extracts competitor
known competitor list match extracted
generic phrase not extracted
concept phrase not extracted as competitor
confidence threshold filters weak candidates
evidence captured
no raw response stored
```

## Acceptance criteria

- Deterministic competitor extractor exists.
- Minimal EN and RU pattern sets implemented.
- Competitor candidates require brand-like signal and competitive context.
- Generic concepts are not competitors.
- Confidence/evidence generated.
- No LLM calls.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

## Escalate if

- Existing parser cannot provide enough text/evidence for deterministic extraction.
- Product wants LLM competitor classification now.
- Russian text normalization requires a broader NLP dependency.

## Commands

```bash
pytest <competitor extractor tests>
ruff check <touched backend files>
```

## Done means

Competitor extraction works deterministically for minimal EN/RU patterns and avoids generic phrase false positives.
