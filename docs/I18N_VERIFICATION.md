# i18n Verification Checklist

Manual QA checklist for English/Russian localization and future-locale readiness.

## Result Values

| Status | Meaning |
| --- | --- |
| Not run | Scenario has not been executed yet. |
| Pass | Scenario passed exactly as expected. |
| Fail | Scenario failed and needs an issue entry. |
| Blocked | Scenario cannot be executed because a prerequisite is unavailable. |
| Partial | Scenario mostly passed but has non-blocking gaps. |

## Scenarios

### O-S01 — Default locale loads

Purpose: Verify the app starts in the default locale.
Preconditions: No `ai-monitor.locale` value in browser storage.
Steps: Open the app, log in if needed, navigate to `/audits`.
Expected result: UI labels render in English; raw audit content is unchanged.
Actual result: Automated route smoke passed in Vitest i18n regression coverage.
Status: Pass
Issue ID:

### O-S02 — Switch to Russian

Purpose: Verify runtime locale switching.
Preconditions: App is open in English.
Steps: Use the interface language switcher and select Russian.
Expected result: Shell, auth, audit list/create/detail/results labels switch to Russian without reload.
Actual result: Automated shell/list/create/detail/results switching passed in Vitest.
Status: Pass
Issue ID:

### O-S03 — Switch back to English

Purpose: Verify bidirectional switching.
Preconditions: App is open in Russian.
Steps: Select English in the interface language switcher.
Expected result: UI labels switch back to English without changing audit data.
Actual result: LanguageSwitcher test passed for Russian to English switching.
Status: Pass
Issue ID:

### O-S04 — Locale persists after reload

Purpose: Verify persisted locale behavior.
Preconditions: Russian is selected.
Steps: Reload the page.
Expected result: Russian remains selected and labels stay Russian.
Actual result: Locale persistence test passed through localStorage assertions.
Status: Pass
Issue ID:

### O-S05 — Invalid stored locale falls back safely

Purpose: Verify fallback behavior.
Preconditions: Set `ai-monitor.locale` to an unsupported value such as `xx`.
Steps: Reload the app.
Expected result: App falls back to English and remains usable.
Actual result: Invalid stored locale fallback test passed.
Status: Pass
Issue ID:

### O-S06 — App shell/auth translated

Purpose: Verify shell and auth pages.
Preconditions: App can reach login/register routes.
Steps: Check login, register, shell navigation, sign out, and session loading states in both locales.
Expected result: Static labels and validation messages are localized.
Actual result: App shell, login, and register tests passed in English and Russian.
Status: Pass
Issue ID:

### O-S07 — Audit create/list/detail translated

Purpose: Verify audit management localization.
Preconditions: At least one active audit exists.
Steps: Check audit list, create audit, edit audit, detail, archive badge, actions, provider diagnostics, and validation in both locales.
Expected result: Static UI labels and status labels are localized; brand names, domains, descriptions, provider ids, model ids, and seed query text are not translated.
Actual result: Audit list/create/detail scoped tests passed in English and Russian; raw audit fields remained unchanged in regression tests.
Status: Pass
Issue ID:

### O-S08 — Results/profile labels translated

Purpose: Verify results surfaces and profile keys where UI exists.
Preconditions: At least one audit has summary/results/sources data.
Steps: Open summary, results, and sources tabs in both locales. Check profile/account labels only if a profile screen exists.
Expected result: Static table headers, filters, empty states, summary cards, source labels, and profile labels are localized. Raw answers and source snippets are unchanged.
Actual result: Summary/results/sources labels passed automated checks. Profile UI is not implemented; profile namespace keys exist only.
Status: Pass
Issue ID:

### O-S09 — Status/error/verdict labels translated

Purpose: Verify code-to-label mappings.
Preconditions: Test data includes multiple audit statuses, run statuses, provider diagnostics, and verdict labels if present.
Steps: Inspect status badges, run badges, provider diagnostic blocks, and verdict displays in both locales.
Expected result: Codes are mapped to localized labels; backend codes remain stable and are not localized in API payloads.
Actual result: Audit status, run status, provider diagnostic, and unknown query type label tests passed.
Status: Pass
Issue ID:

### O-S10 — Raw answers/user content not translated

Purpose: Verify raw content safety.
Preconditions: Audit contains non-English seed queries, brand description, source titles/snippets, and provider answer text.
Steps: Switch locales across detail/results/sources.
Expected result: User-entered text, raw AI answer text, source titles/snippets, provider ids, model ids, email/name values remain unchanged.
Actual result: Raw seed query, brand description, provider id, and source domain preservation passed automated regression tests.
Status: Pass
Issue ID:

### O-S11 — Date/number/percent formatting changes by locale

Purpose: Verify locale-aware display formatting.
Preconditions: Audit list/detail/summary shows dates, counts, and percentages.
Steps: Compare English and Russian display for timestamps, large counts, and percentages.
Expected result: Formatting follows active locale; numeric values are not changed semantically.
Actual result: Intl formatter unit tests passed for date, number, percent, fallback, and null/invalid handling.
Status: Pass
Issue ID:

### O-S12 — Mobile language switcher smoke test

Purpose: Verify mobile usability.
Preconditions: App is accessible from a mobile viewport/device.
Steps: Open login and an authenticated audit route on mobile, switch languages, and navigate between audit tabs.
Expected result: Switcher is reachable without hover-only behavior; labels fit and navigation remains usable.
Actual result: Not executed on a mobile viewport/device in this pass.
Status: Not run
Issue ID: O-I01

## Captured Issues

Use this template for every non-pass scenario.

```text
Issue ID:
Scenario:
Severity: blocker | major | minor
Summary:
Steps to reproduce:
Expected:
Actual:
Decision: fix now | defer with rationale | blocked
Owner:
```

## Final Verification Run

Date: 2026-05-05

Automated checks:

```bash
cd apps/web
npm run typecheck
npm test -- src/lib/i18n/config.test.ts src/lib/i18n/format.test.ts src/components/layout/LanguageSwitcher.test.tsx src/App.test.tsx src/features/auth/LoginPage.test.tsx src/features/auth/RegisterPage.test.tsx src/features/audits/AuditsDashboardPage.test.tsx src/features/audits/CreateAuditPage.test.tsx src/features/audits/EditAuditPage.test.tsx src/features/audits/AuditDetailPage.test.tsx src/features/audits/AuditSummaryPage.test.tsx src/features/audits/AuditResultsPage.test.tsx src/features/audits/AuditSourcesPage.test.tsx src/features/audits/AuditTargetSelector.test.tsx src/test/i18nRegression.test.tsx
```

Result: Pass. TypeScript passed. 15 test files passed, 136 tests passed.

## Captured Issue O-I01

Issue ID: O-I01
Scenario: O-S12 — Mobile language switcher smoke test
Severity: minor
Summary: Mobile-device language switcher smoke was not run during automated Phase O verification.
Steps to reproduce: Open the app from a mobile device or narrow mobile viewport, switch locale on login and authenticated audit routes, navigate audit tabs.
Expected: Switcher is reachable without hover-only behavior; labels fit and navigation remains usable.
Actual: Not run in this pass.
Decision: defer with rationale — requires manual mobile/browser QA outside the automated Vitest pass.
Owner: QA/manual verification
