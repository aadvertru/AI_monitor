# Pipeline verification

Date: 2026-05-01

## Scope

This document records `TASK-144` verification for the reusable backend audit
pipeline.

Pipeline order:

```text
schedule jobs -> execute jobs -> store raw responses -> post-process -> final status
```

## Mock Provider Verification

- Audit id: `11`
- UI-relative audit number: `9`
- Provider: `mock`
- SCDL level: `L1`
- Query count: `1`
- Runs per query: `1`
- Command:

```powershell
.\venv\Scripts\python.exe scripts\run_audit_pipeline.py --audit-id 11
```

- CLI result:

```json
{
  "audit_id": 11,
  "fatal_error": null,
  "final_audit_status": "completed",
  "scheduling": {
    "scheduled_jobs": 1,
    "total_jobs": 1
  },
  "execution": {
    "jobs_executed": 1,
    "jobs_skipped": 0,
    "success_count": 1,
    "error_count": 0,
    "timeout_count": 0,
    "rate_limited_count": 0
  },
  "post_processing": {
    "runs_processed": 1,
    "skipped_already_processed": 0,
    "skipped_missing_raw_response": 0,
    "skipped_non_successful_run": 0
  }
}
```

Backend verification:

- Final audit status: `completed`
- Raw response created: yes
- Parsed result created: yes
- Score created: yes
- Results endpoint row:
  - provider: `mock`
  - status: `success`
  - visible brand: `true`
  - rank: `1`
  - final score: `0.49`
- Summary endpoint:
  - total runs: `1`
  - successful runs: `1`
  - completion ratio: `1.0`
  - visibility ratio: `1.0`
  - average score: `0.49`
  - provider scores: `{"mock": 0.49}`
  - source summary: two mock sources

Result: mock pipeline verification passed.

## OpenAI Provider Verification

OpenAI pipeline verification was run from the local PowerShell session where
the real-provider environment was configured:

```powershell
$env:REAL_PROVIDER_ENABLED="1"
$env:PROVIDER_MODE="openai"
$env:DATABASE_URL="sqlite:///./ai_monitor.db"
```

### OpenAI L1

- Audit id: `12`
- Provider: `openai`
- SCDL level: `L1`
- Query count: `1`
- Runs per query: `1`
- Command:

```powershell
.\venv\Scripts\python.exe scripts\run_audit_pipeline.py --audit-id 12
```

- CLI result:

```json
{
  "audit_id": 12,
  "fatal_error": null,
  "final_audit_status": "completed",
  "scheduling": {
    "scheduled_jobs": 1,
    "total_jobs": 1
  },
  "execution": {
    "jobs_executed": 1,
    "jobs_skipped": 0,
    "success_count": 1,
    "error_count": 0,
    "timeout_count": 0,
    "rate_limited_count": 0
  },
  "post_processing": {
    "runs_processed": 1,
    "skipped_already_processed": 0,
    "skipped_missing_raw_response": 0,
    "skipped_non_successful_run": 0
  }
}
```

Backend verification:

- Final audit status: `completed`
- Raw response created: yes
- Parsed result created: yes
- Score created: yes
- Results endpoint row:
  - provider: `openai`
  - status: `success`
  - visible brand: `true`
  - rank: `1`
  - final score: `0.75`
  - raw answer reference present: yes
- Summary endpoint:
  - total runs: `1`
  - successful runs: `1`
  - completion ratio: `1.0`
  - visibility ratio: `1.0`
  - average score: `0.75`
  - provider scores: `{"openai": 0.75}`
  - source summary: empty, as expected for `L1` without web citations

Result: OpenAI `L1` pipeline verification passed.

### OpenAI L2

- Audit id: `13`
- Provider: `openai`
- SCDL level: `L2`
- Query count: `1`
- Runs per query: `1`
- Command:

```powershell
.\venv\Scripts\python.exe scripts\run_audit_pipeline.py --audit-id 13
```

- CLI result:

```json
{
  "audit_id": 13,
  "fatal_error": null,
  "final_audit_status": "completed",
  "scheduling": {
    "scheduled_jobs": 1,
    "total_jobs": 1
  },
  "execution": {
    "jobs_executed": 1,
    "jobs_skipped": 0,
    "success_count": 1,
    "error_count": 0,
    "timeout_count": 0,
    "rate_limited_count": 0
  },
  "post_processing": {
    "runs_processed": 1,
    "skipped_already_processed": 0,
    "skipped_missing_raw_response": 0,
    "skipped_non_successful_run": 0
  }
}
```

Backend verification:

- Final audit status: `completed`
- Raw response created: yes
- Parsed result created: yes
- Score created: yes
- Raw citation count: `18`
- Results endpoint row:
  - provider: `openai`
  - status: `success`
  - visible brand: `true`
  - rank: `1`
  - final score: `0.79`
  - parsed source count: `13`
  - raw answer reference present: yes
- Summary endpoint:
  - total runs: `1`
  - successful runs: `1`
  - completion ratio: `1.0`
  - visibility ratio: `1.0`
  - average score: `0.79`
  - provider scores: `{"openai": 0.79}`
  - source summary count: `13`
  - sample source domains: `company.marimekko.com`, `marimekko.com`

Result: OpenAI `L2` pipeline verification passed.

No API keys, auth cookies, full raw provider answers, or local `.env` values are
included in this document.
