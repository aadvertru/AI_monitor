# Real provider pilot

The first real-provider pilot is OpenAI-only and must use the OpenAI Responses
API. Chat Completions are not approved for this pilot unless a later task
explicitly escalates and documents the change.

## Defaults

Real provider execution is disabled by default:

```text
REAL_PROVIDER_ENABLED=false
PROVIDER_MODE=mock
REAL_PROVIDER_MAX_PROVIDERS=1
REAL_PROVIDER_MAX_QUERIES=5
REAL_PROVIDER_MAX_RUNS_PER_QUERY=1
REAL_PROVIDER_MAX_TOTAL_RUNS=5
```

`PROVIDER_MODE=mock` allows mock execution only. `PROVIDER_MODE=openai` allows
OpenAI execution only, and mixed provider lists are rejected during the pilot.

## SCDL policy

- `L1` = OpenAI answer without web search.
- `L2` = OpenAI answer with web search when the OpenAI adapter supports it.

TASK-128 only defines policy and caps. It does not configure secrets, implement
the OpenAI adapter, or call the OpenAI API.

## OpenAI configuration

OpenAI settings are loaded from environment variables only. Real secrets must
stay in local environment files or shell configuration and must never be
committed.

```text
OPENAI_API_KEY=
OPENAI_L1_MODEL=gpt-4.1-mini
OPENAI_L2_MODEL=gpt-4.1-mini
OPENAI_REQUEST_TIMEOUT_SECONDS=30
OPENAI_MAX_OUTPUT_TOKENS=1200
```

When OpenAI mode is enabled, `OPENAI_API_KEY` is required. In mock mode the key
may be absent.

## Local dry-run

Dry-run execution is local-only and must be explicitly enabled. It uses the same
pilot policy guard and caps as the audit run trigger.

```powershell
$env:REAL_PROVIDER_ENABLED="true"
$env:PROVIDER_MODE="openai"
$env:DATABASE_URL="sqlite:///./ai_monitor.db"
$env:OPENAI_API_KEY="<local secret>"
.\venv\Scripts\python.exe scripts\run_real_provider_dry_run.py --audit-id 1 --db-url $env:DATABASE_URL
```

The command logs only safe execution metadata: audit id, provider mode,
providers, SCDL level, query/run counts, job counts, status counts, and final
audit status. It does not log prompts, raw answers, or API keys.

## Raw response inspection

Admins can inspect a stored raw response for local pilot debugging:

```text
GET /audits/{audit_id}/runs/{run_id}/raw
```

The response uses existing `RawResponse` storage and includes audit/run context,
the query, raw answer, citations, provider metadata, normalized error object,
response time, and creation time. Provider metadata and error objects are
redacted recursively for secret-like keys before serialization. Regular users
receive `403`.
