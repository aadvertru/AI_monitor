# Core Models Mapping (T3)

- `Brand`: stores brand identity and metadata from product input (`brand_name`, `brand_domain`, `brand_description`).
- `Audit`: root object of one audit cycle with settings and lifecycle status (`created/running/partial/completed/failed`).
- `Query`: normalized query unit linked to an audit.
- `Run`: execution unit for `query x provider x run_number` with run status (`pending/success/error/timeout/rate_limited`).
- `RawResponse`: raw-layer storage for provider output (`raw_answer`, `citations`, `provider metadata`, `provider status`, `request snapshot`, `error object`).
- `ParsedResult`: parsed-layer storage for extracted signals (`visible_brand`, rank, sentiment, competitors, sources, parsed payload).
- `Score`: score-layer storage for component metrics and `final_score`.

Separation is preserved by keeping `RawResponse`, `ParsedResult`, and `Score` in separate tables, each linked one-to-one to `Run`.

