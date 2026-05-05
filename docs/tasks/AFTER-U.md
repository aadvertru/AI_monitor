# AFTER-U — Testing Checklist After Concepts and Competitors Split

## Phase covered

Phase U — Concepts and Competitors Split.

## Primary goal to verify

Generic phrases/concepts are no longer mislabeled as competitors, while real competitor candidates are extracted conservatively with evidence and confidence.

---

## Backend tests

### Models/DTOs

Verify:

```text
Concept model/DTO exists
CompetitorCandidate model/DTO exists
evidence can be represented
audit-owned relationship exists
confidence bounded
empty arrays safe
```

### Legacy mapping

Verify:

```text
legacy extracted competitors map to concepts
competitor_candidates empty for generic phrases
legacy field remains backward-compatible if still needed
parser/scoring unchanged
```

### Deterministic competitor extractor

Verify mandatory EN/RU pattern support:

```text
English alternative context extracts competitor
English vs context extracts competitor
English competitors/similar/best/top context extracts competitor
Russian 'альтернативы' context extracts competitor
Russian 'конкуренты' context extracts competitor
Russian 'похожие' / 'похожие компании' context extracts competitor
Russian 'лучшие' / 'топ' context extracts competitor
Russian 'сравнение' / 'против' context extracts competitor
known competitor list match extracted if available
generic phrase not extracted
concept phrase not extracted as competitor
confidence threshold filters weak candidates
evidence captured
no raw response stored
```

### Persistence

Verify:

```text
post-processing creates concepts
post-processing creates competitor candidates when evidence exists
rerun post-processing idempotent
concept counts update correctly
competitor evidence merges
failed/no-answer runs skipped
legacy audits safe
```

### API fields

Verify:

```text
concepts returned
competitor_candidates returned
empty arrays safe
legacy competitors field still available if needed
evidence summaries safe
auth/ownership enforced
raw provider responses not exposed
generic phrases not returned as competitors
```

---

## Frontend tests

Verify:

```text
Results Details shows Concepts section
Results Details shows Competitor Candidates section
generic phrases appear under Concepts
generic phrases do not appear under Competitors
competitor candidates show name/domain/confidence/evidence count
empty states render
legacy competitors fallback goes to concepts if needed
i18n labels used if available
unsafe fields not rendered
```

---

## Manual QA

Run:

```text
open result details with generic phrases
verify they are under Concepts
open result with clear EN competitor comparison
verify competitor candidate appears
open result with clear RU competitor comparison
verify competitor candidate appears
verify evidence/confidence displayed
verify empty competitor state when no competitor evidence
verify legacy audit detail safe
```

---

## Safety checks

Must not expose:

```text
raw provider response
raw prompts
headers
API keys
stack traces
```

---

## Exit criteria

Phase U is stable when:

```text
concepts and competitors are semantically separated
generic phrases are not mislabeled
competitor candidates require evidence
minimal EN/RU competitor patterns are mandatory and tested
legacy data safe
Results Details labels are correct
```
