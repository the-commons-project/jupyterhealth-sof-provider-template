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

> **How the app reaches JHE.** The SMART launch gives the app an *EHR* access token. By
> default the app exchanges that token for a JHE token (RFC 8693, JHE's `/o/token-exchange`),
> so the provider does **not** sign into JHE separately. For that to work JHE must be
> configured to trust the EHR issuer (`TRUSTED_TOKEN_IDP`) and have the launching
> Practitioner on file. As a dev/test shortcut you can instead set a static `JHE_TOKEN`
> (see step 1), which bypasses the exchange.

---

## 1. Get your JHE base URL (token exchange needs no `JHE_TOKEN`)

Note your JHE base URL — that's your `JHE_URL` (e.g. `https://jhe.fly.dev`). With token
exchange (the default), the app mints its JHE token from the SMART launch, so there is no
`JHE_TOKEN` to create. Two things must be true on the JHE instance for the exchange to
succeed (coordinate with whoever runs it):

- `TRUSTED_TOKEN_IDP` is set to the EHR's issuer so JHE trusts the launch token. If your
  EHR's OIDC issuer differs from its FHIR base, set `JHE_TRUSTED_ISS` in `.env` to match.
- The launching **Practitioner** exists in JHE keyed by the issuer's identifier, and the
  patient you'll view is enrolled with the MRN as their external id.

**Dev/test shortcut — a static `JHE_TOKEN`.** To skip the exchange, register this app as an
**OAuth2 Client** in the **JHE Admin SPA** (the `/portal` path on your JHE host, e.g.
`https://jhe.fly.dev/portal`), complete JHE's Authorization-Code-with-PKCE flow, and use the
resulting practitioner access token as `JHE_TOKEN`. When `JHE_TOKEN` is set the app uses it
and skips token exchange.

---

## 2. Configure

Generation already created `.env` from your answers (it's gitignored — there is no
`.env.example`). The app loads `.env` at runtime, so edits take effect on the next run.
Open `.env` and set:
- `JHE_TOKEN` — leave blank to use token exchange; set it only for the dev/test shortcut
- `JHE_URL` — from step 1 (e.g. `https://jhe.fly.dev`); pre-filled from your answer
- `SMART_CLIENT_ID` — the `client_id` from your EHR app registration (public client +
  PKCE; no secret); pre-filled, override here after registering
- `SMART_SCOPES` — SMART scopes for the launch; pre-filled
- `EHR_IFRAME_ORIGIN` — the EHR origin allowed to embed the app (CSP); pre-filled
- `MRN_IDENTIFIER_SYSTEM` — the EHR `Patient.identifier` system that holds the MRN
  (see [ehr-registration.md](ehr-registration.md) §3 for how to find it; MedPlum has
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

## 6. Register with your EHR and deploy

- [ehr-registration.md](ehr-registration.md) — register the app with your EHR, scopes,
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
| `TokenExchangeError` / "trusted issuer" / "Practitioner not found" | JHE doesn't trust the EHR issuer, or the Practitioner isn't on file | Set the issuer JHE expects via `JHE_TRUSTED_ISS`; confirm JHE's `TRUSTED_TOKEN_IDP` and that the Practitioner exists in JHE |
| JHE calls return 401 | `JHE_TOKEN` missing/expired, or app not registered as a JHE Client | Re-issue the token (step 1); confirm the Client is registered in the JHE Admin SPA |
| "No <type> data for this patient" | No observations of that type in JHE for the patient | Confirm data exists; check `JHE_DATA_TYPE_CODES` (esp. the provisional `steps` code) |
