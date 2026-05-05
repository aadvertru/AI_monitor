# TASK-V204 — Implement Web5 General Summary Cards

## Goal

Implement the general summary cards for Web5-style audit summary.

Cards should display backend-provided metrics only.

---

## Scope

Implement cards for:

```text
Mentionability L1
Mentionability L2
Accuracy L1
Accuracy L2
Tone / Sentiment
```

Add task-scoped frontend tests.

---

## Data rules

Use only fields returned by summary v2.

Do not calculate mentionability, accuracy, scoring, or sentiment in frontend.

Frontend may format percentages/counts for display only.

---

## Card behavior

Each card should support:

```text
normal value
N/A / not evaluated
partial data
loading skeleton inherited from page shell
tooltip/help copy if available
```

### Mentionability

Show percentage and optionally numerator/denominator:

```text
25%
15 / 60
```

### Accuracy

If evaluation is unavailable:

```text
N/A
Not evaluated
```

Do not use visibility score as accuracy.

### Tone

Show tone/sentiment distribution if available:

```text
positive
neutral
negative
```

If unavailable, show safe empty state.

---

## i18n

Translate labels:

```text
Mentionability L1
Mentionability L2
Accuracy L1
Accuracy L2
Tone
Not evaluated
No data
```

Support future locales through translation keys.

---

## Tests

Frontend tests:

```text
mentionability cards render values
accuracy cards render values when available
accuracy cards render N/A when evaluation missing
tone card renders distribution
partial data safe
zero denominators safe
no frontend score calculation
i18n labels render
```

---

## Acceptance criteria

- General summary cards implemented.
- Cards consume backend summary v2 data.
- Accuracy not faked from visibility score.
- Missing/null data handled safely.
- i18n labels used.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement model summary.
- Do not implement fact-checking backend.
- Do not change summary v2 endpoint.
- Do not calculate metrics in frontend.
