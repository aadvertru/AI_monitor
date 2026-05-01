# Real response analysis

Date: 2026-05-01

## Available Pilot Data

Two successful real OpenAI responses are available in the local pilot database.
Both use non-sensitive test queries for the same brand.

| Audit | SCDL | Provider | Run | Result |
| --- | --- | --- | --- | --- |
| 8 | L1 | openai | 10 | Successful raw response, parsed, scored, visible brand = false |
| 10 | L2 | openai | 12 | Successful raw response, parsed, scored, visible brand = false |

Target brand:

```text
Окна Лабрадор
```

Target domain:

```text
labrador-spb.ru
```

Target query:

```text
пластиковые окна в санкт-петербурге
```

No API keys, auth cookies, or full raw provider answers are included in this
document.

## Provider Adapter Issues

L1 execution stored a normal Russian-language answer. The provider adapter
returned a successful normalized response, persisted raw response metadata, and
post-processing converted the stored answer into parsed and scored records.

L2 execution also stored a successful raw response, but the original request for
audit `10` was created from a PowerShell here-string that had already corrupted
Cyrillic text into question marks before the provider call. The stored audit and
query were repaired afterward for UI inspection, but the actual L2 provider
answer reflects the corrupted prompt that was sent at execution time.

Classification:

- L1 provider path: acceptable behavior.
- L2 provider path: pilot data quality issue caused by local console/database
  input encoding before the provider call, not a source-mapping or parser
  finding.
- Request proof gap: stored `request_snapshot` currently does not prove the L2
  web-search request shape. Adapter tests prove the code path includes web
  search tooling for L2, but raw response records should store safe execution
  metadata such as `scdl_level`, `web_search_enabled`, model, and requested
  include keys.

## Russian Brand Detection

L1 raw answer discussed plastic windows in Saint Petersburg and named several
general window brands/manufacturers. It did not mention `Окна Лабрадор` or
`labrador-spb.ru`.

Parsed result:

- `visible_brand`: `false`
- `brand_position_rank`: `null`
- `match_type`: `none`
- `mention_count`: `0`

Classification: acceptable behavior. This is not a false negative for the exact
brand because the stored answer did not mention the brand or domain.

The current data does not validate Russian inflection or variant handling,
because no successful response contained a brand variant such as a quoted,
lowercase, inflected, or domain-only mention.

Follow-up task proposal:

- Add redacted Russian fixtures where the answer includes exact brand, lowercase
  brand, quoted brand, domain-only mention, and likely inflected variants.

## Russian Competitor Extraction

The L1 answer included recognizable competing/manufacturer names in Russian
context, but `competitors` was saved as an empty list.

Classification: missed competitor extraction / unsupported Russian extraction
pattern.

Likely cause: current competitor extraction was mostly validated on mock/English
patterns and does not reliably extract competitor lists from Russian prose or
manufacturer-list sections.

Follow-up task proposal:

- Add Russian competitor extraction fixtures from redacted real response
  snippets.
- Extend extraction patterns for Russian list structures such as "такие марки
  как", "производители", "бренды", and comma-separated brand lists.
- Keep the parser contract unchanged; only improve extraction internals and
  tests.

## Russian Sentiment And Recommendation

Both L1 and L2 parsed records saved:

- `sentiment_score`: `0.5`
- `recommendation_score`: `0.0`

For L1, the raw answer was informational and did not recommend the target brand.
Neutral sentiment is acceptable. Recommendation score `0.0` for the target brand
is also acceptable because the answer did not recommend `Окна Лабрадор`.

However, this data does not validate Russian recommendation detection for cases
where the brand is actually recommended.

Classification:

- Current L1 result: acceptable behavior.
- Coverage gap: unsupported or unvalidated Russian recommendation language.

Follow-up task proposal:

- Add Russian recommendation fixtures with wording like "рекомендуем",
  "советуем", "лучший выбор", "топ", "стоит обратить внимание", and weak or
  indirect recommendations.

## Scoring Issues

L1 and L2 scored as:

- `visibility_score`: `0.0`
- `prominence_score`: `0.0`
- `sentiment_score`: `0.5`
- `recommendation_score`: `0.0`
- `source_quality_score`: `0.0`
- `final_score`: `0.0`

Classification: acceptable behavior for brand-not-visible runs. The visibility
cap correctly forces final score to zero when the brand is not visible.

Coverage gap: the pilot still lacks a real Russian response where the target
brand is visible, so prominence ranking, sentiment contribution, recommendation
contribution, and final score calibration remain unvalidated on positive
Russian-language examples.

Follow-up task proposal:

- Run a tiny positive-control audit query that names the brand directly, for
  example a query about `Окна Лабрадор`, and verify that scoring is non-zero
  only when the parser finds the brand.

## Aggregation Issues

After post-processing, summaries for audits `8` and `10` are refreshed and
consistent with saved run-level records:

- total runs: `1`
- successful runs: `1`
- visibility ratio: `0.0`
- average score: `0.0`
- provider scores: `{"openai": 0.0}`
- critical query reason: `not_visible`

Classification: acceptable behavior.

No aggregation contract change is needed for these examples.

## Source And Citation Issues

Both stored real responses have empty citations:

```json
[]
```

For L1 this is expected. For L2, this means source mapping and source
intelligence UI could only be verified as an empty state, not as populated
source extraction.

Classification:

- L1 empty sources: acceptable behavior.
- L2 empty sources: inconclusive because the executed prompt was corrupted
  before the provider call.

Follow-up task proposal:

- Re-run a clean L2 audit after verifying UTF-8 input at creation time.
- Store safe request-shape metadata proving web search was enabled.
- If OpenAI returns sources, add redacted mocked unit tests for citation
  normalization and source summary display.

## UI Issues

UI displayed the repaired audit `10` with correct Cyrillic after the local
database fields were fixed. Before the repair, the UI correctly displayed the
data it received: question marks stored in the database.

Classification:

- Frontend Cyrillic rendering: acceptable behavior.
- Local data creation path: encoding bug in ad hoc PowerShell here-string usage,
  now documented.

Normal user-facing UI does not expose full raw answers. Results and summary
views expose `raw_answer_ref`-level data only.

Follow-up task proposal:

- Prefer API-created audits or Python Unicode escapes for local Cyrillic test
  data.
- Add a small local seed/helper command for pilot audits so Cyrillic data is not
  manually inserted through shell-sensitive strings.

## L1 Versus L2

L1 produced a substantive answer about the query topic but did not mention the
target brand.

L2 produced a successful answer to the corrupted prompt and therefore cannot be
used to judge real L2 search quality, source availability, or brand visibility.

Classification: L1/L2 comparison is inconclusive until a clean L2 response is
collected.

## Follow-Up Bugs And Tasks

1. Store safe L2 execution evidence in `RawResponse.request_snapshot` or
   provider metadata:
   - `scdl_level`
   - `web_search_enabled`
   - model
   - requested include keys
   - no API keys or raw headers

2. Add a safe pilot-audit creation helper for Cyrillic data to avoid local shell
   encoding loss.

3. Add Russian competitor extraction fixtures and improve unsupported Russian
   list-pattern handling.

4. Add Russian brand-detection fixtures for exact, lowercase, quoted, domain,
   and variant mentions.

5. Add Russian recommendation/sentiment fixtures for explicit and weak
   recommendation language.

6. Run a clean L2 positive-control audit after the encoding-safe creation path
   exists, then repeat source/citation mapping analysis.

7. Add redacted real-response fixtures only after manually confirming they do
   not contain secrets, personal data, or full sensitive raw content.
