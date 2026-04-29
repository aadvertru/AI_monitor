# AI Monitor Web

## Smoke Test

Run the authenticated SCDL happy-path smoke flow with:

```bash
npm run test:smoke
```

The smoke test uses the real React Router app and mocked backend responses for auth, audit creation, run trigger, summary, and results. It does not start a backend server and fails if the UI attempts an external provider request.
