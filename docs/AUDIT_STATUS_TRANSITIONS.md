# Audit status transitions

Audit status is shared by scheduling, execution, post-processing, CLI, and UI
refresh flows. The canonical final-status rule lives in
`libs/execution/audit_status.py`.

## Status meanings

- `created`: audit exists and has not started pipeline execution.
- `running`: scheduling, provider execution, or post-processing is in progress.
- `completed`: all expected runs are terminal and accounted for. The target
  brand may be visible or not visible; brand-not-found is a valid completed
  result when the provider response was successfully parsed and scored.
- `partial`: at least one usable result exists, but some provider execution,
  raw response, parser, or scoring step failed or was skipped.
- `failed`: no usable scored data can be produced, or a fatal pipeline error
  prevents completion.

## Pipeline order

```text
created
-> running
-> schedule jobs
-> execute pending jobs
-> post-process stored raw responses
-> completed | partial | failed
```

## Final status rules

- Fatal orchestration error: `failed`.
- All expected runs terminal, at least one usable score, no recoverable errors:
  `completed`.
- Brand not found after successful provider execution: `completed` with a low or
  zero score, not `failed`.
- Usable scored data exists, but one or more terminal provider/parser/scoring
  issues also exist: `partial`.
- Terminal provider failures exist and no usable scored data exists: `failed`.
- Expected work is not terminal/accounted for yet: `running`.

Results and summary endpoints must remain inspectable for `partial` and
`failed` audits when data exists.
