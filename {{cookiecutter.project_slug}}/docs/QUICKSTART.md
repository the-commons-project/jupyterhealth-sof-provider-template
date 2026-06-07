# Quickstart

This walks you from a freshly generated project to seeing a patient's device data
rendered by a SMART on FHIR launch — end to end. Plan ~1–2 hours the first time.

There are two test paths for the SMART launch:
- **MedPlum** (recommended) — JupyterHealth's hosted demonstration Provider. No local
  EHR to run.
- **Fully local** — the self-contained
  [`jhe-smart-demo`](https://github.com/jupyterhealth/jhe-smart-demo) (HAPI FHIR + a
  mock EHR SMART App Launcher + JHE in docker compose). Use this if you want everything
  on your machine.

---

## 0. Prerequisites

- Python 3.11+ and Docker (with `docker compose`).
- Access to a **JupyterHealth Exchange (JHE) instance** — your own deployment, a shared
  `*.fly.dev` instance, or a local JHE (see
  [jupyterhealth-exchange](https://github.com/jupyterhealth/jupyterhealth-exchange)).
- In that JHE instance: a **Study**, at least one **Patient**, and some **Observations**
  for that patient (heart rate / sleep / steps).
- The patient's **MRN** must be stored on the JHE patient as its **external identifier**,
  and must match the MRN the EHR exposes on `Patient.identifier`. This is the join key.

> **Two credentials, don't confuse them.** The SMART launch gives you an *EHR* access
> token (used only to read the EHR `Patient` resource for the MRN). Reading device data
> from JHE uses a *separate* `JHE_TOKEN`. Unifying these via token exchange is a future
> improvement (tracked upstream in `jhe-smart-demo`).

---

## 1. Get your JHE base URL and a `JHE_TOKEN`

`jupyterhealth-client` (used inside the notebook) authenticates to JHE with a bearer
token. You get one by registering this app as an **OAuth2 Client** in the **JHE Admin
SPA**, then completing JHE's OAuth flow.

1. Open your JHE instance's Admin SPA — the `/portal` path on your JHE host, e.g.
   `https://jhe.fly.dev/portal` (or `http://localhost:8000/` for a local JHE). Log in as
   a **Practitioner** with access to your Study.
2. Register a **Client** for this app under your Study (JHE → your instance's client
   management). JHE issues an **OAuth 2.0 Client ID** for it. (JHE uses the Authorization
   Code grant with PKCE — see the
   [JHE README → Authorization](https://github.com/jupyterhealth/jupyterhealth-exchange#readme).)
3. Complete the OAuth flow to obtain an **access token**. For a quick start, the simplest
   path is to use the practitioner web-login token from your JHE instance. That access
   token is your `JHE_TOKEN`.
4. Note your JHE base URL — that's your `JHE_URL` (e.g. `https://jhe.fly.dev`).

> Registering your deployed app's host (e.g. your `*.fly.dev` URL) as a Client/redirect in
> the JHE Admin SPA is required before it can obtain tokens in production, too.

---

## 2. Configure

```
cp .env.example .env
```
Set in `.env`:
- `JHE_URL` — from step 1 (e.g. `https://jhe.fly.dev`)
- `JHE_TOKEN` — from step 1
- `MRN_IDENTIFIER_SYSTEM` — the EHR `Patient.identifier` system that holds the MRN
  (see [epic-registration.md](epic-registration.md) §3 for how to find it; MedPlum has
  its own identifier system)
- `JHE_DATA_TYPE_CODES` (optional) — only if your data types differ from the defaults

---

## 3. Run the app

```
docker compose up --build
```
This starts the Jupyter server with the SMART launch extension and Voilà. It listens on
`http://localhost:8888`. It does nothing useful until an EHR launches it (next step) —
the launch is what supplies the patient context.

---

## 4. Simulate a SMART launch

### Path A — MedPlum (recommended)
Follow the upstream tutorial, *Launch a JupyterHealth dashboard via SMART-on-FHIR
(MedPlum example)*, in
[jupyterhealth/software-documentation](https://github.com/jupyterhealth/software-documentation).
In short: register this app in MedPlum as a SMART app with:
- Launch URL: `http://localhost:8888/smart-on-fhir/launch`
- Redirect URL: `http://localhost:8888/smart-on-fhir/callback`

Then launch it from a MedPlum Patient's "Apps". MedPlum populates the launch context
(patient + token); the app reads the MRN and queries JHE.

### Path B — Fully local
Clone and run [`jhe-smart-demo`](https://github.com/jupyterhealth/jhe-smart-demo): its
docker compose brings up HAPI FHIR, a **mock EHR SMART App Launcher**, and JHE with a
seeded practitioner/patient. Point its launcher at this app's
`/smart-on-fhir/launch`. This is the closest local mirror of a real EHR launch.

If the launch succeeds you'll see the rendered notebook (your viz) where the patient's
data appears.

---

## 5. Develop your dashboard

The data plumbing is done — you write analytics/viz in **`dashboard.ipynb`**, in the cell
marked `ADD YOUR ANALYTICS + VISUALIZATION`.

Inner loop (faster than rebuilding the container each time):
```
pip install -e ".[test]"
jupyter lab            # open dashboard.ipynb, iterate on the viz cell
```
In Jupyter Lab the launch context isn't present, so `launch_context.current()` will
raise. For iterating on visuals, either run the smoke-test fakes pattern (see
`tests/test_smoke.py`) or temporarily hardcode a known MRN and call `jhe_data.fetch`
directly. When the viz looks right, `docker compose up --build` and re-launch to see it
in the SMART flow. Voilà renders exactly what the notebook produces.

Validate the wiring at any time without a server:
```
pytest tests/test_smoke.py
```

---

## 6. Register with Epic and deploy

- [epic-registration.md](epic-registration.md) — register the app with Epic, scopes,
  and starting your security review.
- [deployment.md](deployment.md) — deploy (Docker / fly.io), the **iframe/CSP gotcha**,
  and the POC single-provider concurrency limitation.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Blank frame in the EHR | CSP `frame-ancestors` blocks embedding | See deployment.md → "iframe/CSP gotcha"; confirm your EHR origin is in the CSP header |
| `LaunchContextError: SMART_TOKEN_FILE is not set` | App opened without a SMART launch | Launch it from the EHR (step 4), not directly |
| `LaunchContextError: No identifier with system ... found` | `MRN_IDENTIFIER_SYSTEM` doesn't match the EHR's MRN system | Inspect the EHR `Patient.identifier` and set the correct system |
| `PatientNotInJHE: No JupyterHealth patient found for MRN ...` | JHE has no patient whose external id == that MRN | Add/align the patient's external identifier in JHE |
| `LaunchContextError: Failed to fetch Patient/...` | EHR token/scope issue or wrong FHIR base | Check the SMART scopes include `patient/*.read` and the EHR FHIR base |
| JHE calls return 401 | `JHE_TOKEN` missing/expired, or app not registered as a JHE Client | Re-issue the token (step 1); confirm the Client is registered in the JHE Admin SPA |
| "No <type> data for this patient" | No observations of that type in JHE for the patient | Confirm data exists; check `JHE_DATA_TYPE_CODES` (esp. the provisional `steps` code) |
