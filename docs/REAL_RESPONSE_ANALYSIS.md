# Real response analysis

Date: 2026-05-01

## Available Pilot Data

The first OpenAI pilot attempt produced controlled error raw responses for both
SCDL levels:

- `L1`: `sdk_not_installed`
- `L2`: `sdk_not_installed`

No successful real OpenAI raw answer is available yet in the current
environment.

## Provider Adapter

The adapter selected the OpenAI path through the dry-run pipeline and persisted
normalized provider errors through the existing `RawResponse` storage path. This
is acceptable behavior for the current environment because the OpenAI SDK is not
installed.

No API key appeared in stored error objects, dry-run metadata, logs, or committed
documentation.

## Parser

No successful raw answer was available for parser comparison. Parser behavior on
real OpenAI prose remains unvalidated.

Follow-up classification: missing data, not a parser failure.

## Scoring

No parsed result or score was expected for the controlled provider-error runs.
Score boundedness on successful real OpenAI responses remains unvalidated.

Follow-up classification: missing data, not a scoring failure.

## Aggregation

The pilot produced error runs only. Aggregation should treat these as failed
runs and keep successful-run metrics empty or zero according to existing API
contracts.

Follow-up classification: acceptable behavior for provider-error runs.

## UI

The UI should be able to display the failed/error run state through the existing
results and summary pages. Real response shape issues cannot be evaluated until
successful raw answers and citations exist.

Follow-up classification: pending real data.

## L1 Versus L2

Both levels reached the same controlled environment error before any OpenAI
Responses API request could be made. No L1/L2 content, citation, or visibility
difference can be evaluated yet.

## Follow-Up Tasks

- Install and pin an OpenAI SDK version compatible with the Responses API.
- Re-run the controlled pilot with a real local API key outside version control.
- Re-run this analysis once at least one successful L1 and one successful L2 raw
  response are stored.
- Add redacted successful real-response fixtures only after sensitive data is
  reviewed and removed.
