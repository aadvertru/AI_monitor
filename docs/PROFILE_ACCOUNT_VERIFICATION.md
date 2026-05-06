# Profile / Account Verification

Profile plan and token usage are demo data in this phase. This checklist verifies
that demo status is clear and that no billing, payment, token enforcement, or
sensitive fields are exposed.

## Result Table

| Scenario | Status | Notes | Issue ID |
|---|---|---|---|
| P-S01 | Pass | Browser opened `/profile` after backend restart and rendered authenticated profile data. |  |
| P-S02 | Pass | Covered by `ProfilePage.test.tsx` unauthenticated route test. |  |
| P-S03 | Pass | Covered by backend profile tests and frontend render tests. |  |
| P-S04 | Pass | Covered by backend demo DTO tests and frontend render tests. |  |
| P-S05 | Pass | Covered by frontend notification settings render test. |  |
| P-S06 | Pass | Covered by frontend save/cancel tests and backend persistence tests. |  |
| P-S07 | Pass | Covered by frontend non-editable field test and backend extra-field rejection tests. |  |
| P-S08 | Pass | Browser verified EN->RU save/reload and automated tests cover locale persistence/backend validation. |  |
| P-S09 | Pass | Covered by backend response contract tests and frontend unsafe-field regression test. |  |
| P-S10 | Not run | Mobile viewport was not available in the current browser automation surface; automated route/layout tests passed. |  |

## P-S01 - Authenticated User Can Open Profile

### Purpose
Verify that a logged-in user can access the Profile page.

### Preconditions
- User is authenticated.
- Backend and frontend are running.

### Steps
1. Log in.
2. Open `/profile`.

### Expected Result
- Profile page opens.
- No login redirect occurs.

### Actual Result
Browser opened `/profile` after backend restart and rendered profile data.

### Status
Pass

### Issue ID

## P-S02 - Unauthenticated User Cannot Open Profile

### Purpose
Verify that profile access is protected.

### Preconditions
- User is logged out or session cookie is cleared.

### Steps
1. Open `/profile`.

### Expected Result
- User is redirected to login or blocked by the protected route.

### Actual Result
Automated frontend route test redirects unauthenticated visitors to login.

### Status
Pass

### Issue ID

## P-S03 - Profile Displays User Identity

### Purpose
Verify that profile identity comes from authenticated user data.

### Preconditions
- User is authenticated.

### Steps
1. Open `/profile`.
2. Inspect Account section.

### Expected Result
- Email is displayed.
- Display name is shown as read-only or "not set" if unavailable.
- Password hashes and tokens are not displayed.

### Actual Result
Automated backend and frontend tests verify email/display name rendering and
absence of password/token fields.

### Status
Pass

### Issue ID

## P-S04 - Demo Plan And Token Usage Render Clearly

### Purpose
Verify that plan and usage are visible and clearly marked as demo.

### Preconditions
- User is authenticated.

### Steps
1. Open `/profile`.
2. Inspect Plan and Usage sections.

### Expected Result
- Plan name is shown.
- Token remaining and token total are shown.
- Demo marker is visible.
- No payment or billing controls are shown.

### Actual Result
Automated backend and frontend tests verify demo plan, demo usage totals, and no
billing/payment controls.

### Status
Pass

### Issue ID

## P-S05 - Notification Preferences Render

### Purpose
Verify notification preferences are visible.

### Preconditions
- User is authenticated.

### Steps
1. Open `/profile`.
2. Inspect Notifications section.

### Expected Result
- Email notification setting is visible.
- Audit completed notification setting is visible.
- Provider error notification setting is visible.

### Actual Result
Automated frontend tests verify all three notification settings render.

### Status
Pass

### Issue ID

## P-S06 - Editable Preferences Save/Cancel Works

### Purpose
Verify preferences can be changed and saved or reset.

### Preconditions
- User is authenticated.

### Steps
1. Open `/profile`.
2. Change notification toggles.
3. Click Cancel and verify values reset.
4. Change notification toggles again.
5. Click Save.
6. Reload the page.

### Expected Result
- Cancel resets unsaved changes.
- Save persists changes through backend-backed preferences.
- Reload shows saved preferences.

### Actual Result
Automated frontend tests verify cancel resets form state, save persists
preferences-only payload, and backend tests verify persistence.

### Status
Pass

### Issue ID

## P-S07 - Non-Editable Fields Cannot Be Changed

### Purpose
Verify identity, plan, and token fields remain read-only.

### Preconditions
- User is authenticated.

### Steps
1. Open `/profile`.
2. Inspect Account, Plan, and Usage sections.

### Expected Result
- Email is not editable.
- Display name is not editable.
- Plan is not editable.
- Token totals are not editable.

### Actual Result
Automated frontend tests verify identity, plan, and token fields are not editable.

### Status
Pass

### Issue ID

## P-S08 - Language Preference Works If i18n Is Available

### Purpose
Verify locale preference can be changed when i18n is enabled.

### Preconditions
- User is authenticated.
- i18n language support is available.

### Steps
1. Open `/profile`.
2. Change language preference.
3. Save.
4. Reload `/profile`.

### Expected Result
- Locale preference saves.
- Profile labels remain translated by frontend i18n.
- Raw user values are not translated.

### Actual Result
Browser QA changed language preference from English to Russian, saved it,
verified translated profile labels, reloaded `/profile`, and confirmed the saved
locale persisted. The preference was restored to English after QA. Automated
tests also cover locale persistence and backend invalid-locale rejection.

### Status
Pass

### Issue ID

## P-S09 - Unsafe Fields Are Not Rendered

### Purpose
Verify profile API/UI do not expose secrets or internal fields.

### Preconditions
- User is authenticated.
- Test/mocked response can include unsafe extra fields.

### Steps
1. Open `/profile` with a response containing unsafe extra fields.
2. Inspect rendered UI.

### Expected Result
- UI does not display password, hashed password, JWT, secrets, API keys,
  provider keys, billing secrets, or raw config.

### Actual Result
Automated backend and frontend tests include unsafe extra fields and verify they
are not exposed in the response/UI.

### Status
Pass

### Issue ID

## P-S10 - Mobile/Profile Layout Smoke Test

### Purpose
Verify profile layout and controls remain usable on a mobile viewport.

### Preconditions
- User is authenticated.
- Browser viewport is set to mobile width.

### Steps
1. Open `/profile`.
2. Inspect all profile sections.
3. Toggle a preference.
4. Save or cancel.

### Expected Result
- Sections stack cleanly.
- Text does not overlap.
- Save/cancel controls are reachable.

### Actual Result
Not run in a mobile viewport because this browser automation surface did not
expose viewport resizing. Desktop browser QA passed and automated route/layout
tests passed.

### Status
Not run

### Issue ID

# Captured Issues

## ISSUE-P-001 - Running API Process Did Not Expose Profile Routes

### Scenario
P-S01

### Severity
Minor

### Actual Result
Browser opens `/profile`, but the currently running backend at
`http://127.0.0.1:8000/profile` returns `{"detail":"Not Found"}`.

### Expected Result
After restarting the backend with Phase P code, authenticated users should get a
profile response and the UI should render profile sections.

### Evidence
`Invoke-WebRequest http://127.0.0.1:8000/profile` returned 404 during manual QA.
The local Alembic migration to `c6d7e8f9a0b1` was already applied.

### Suggested Next Step
Restart the backend process on port 8000, then rerun P-S01 and P-S10 manually.

### Resolution
Resolved by restarting the backend. `GET /profile` now requires authentication
instead of returning 404, and authenticated browser QA renders the profile page.
