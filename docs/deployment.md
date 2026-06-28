# Deploying this app

> **New here?** Start with [QUICKSTART.md](QUICKSTART.md) — it walks the full path from a
> fresh clone to data on screen (how to configure the id_token exchange, how to
> simulate a SMART launch). This file is the deployment-specific reference.

## Configure
Copy `.env.example` to `.env` (gitignored) and fill it in — `cp .env.example .env`, or
run `make init`. The app loads `.env` at runtime — edit it and the change takes effect on
the next run. Values:
- `JHE_URL` — your JupyterHealth Exchange base URL (e.g. `https://jhe.fly.dev`). The app
  mints its JHE bearer token at launch by exchanging the EHR id_token (RFC 8693); JHE must
  be configured to trust the EHR issuer — see [QUICKSTART.md](QUICKSTART.md) §1.
- `SMART_CLIENT_ID` — the SMART `client_id` from your EHR app registration (public
  client + PKCE; no secret).
- `SMART_SCOPES` — SMART scopes requested at launch (space-separated).
- `EHR_IFRAME_ORIGIN` — the EHR web origin allowed to embed the app (CSP frame-ancestors).
- `MRN_IDENTIFIER_SYSTEM` — the EHR `Patient.identifier` system that holds the MRN
- `JHE_DATA_TYPE_CODES` (optional) — JSON to override the data-type → OMH code map.
  **Note:** the `steps` code default (`omh:step-count:3.0`) is provisional; set it to
  whatever your ingestion path (Garmin shim / Validic) actually emits.

## Run locally
```
docker compose up --build
```
Then complete a SMART launch from your EHR test environment (or MedPlum dev instance)
pointed at `https://<host>/smart-on-fhir/launch`.

## Deploy
A `Dockerfile` and `fly.toml.example` are provided. Any container host works.

## The iframe / CSP gotcha (read this)
Voilà and Jupyter default to `Content-Security-Policy: frame-ancestors 'self'`, which
**blocks the EHR from embedding the app** and shows a blank frame. `jupyter_server_config.py`
sets the header from the `EHR_IFRAME_ORIGIN` value in your `.env`:
```
frame-ancestors 'self' <EHR_IFRAME_ORIGIN>
```
If the EHR shows a blank frame, set `EHR_IFRAME_ORIGIN` in `.env` to the EHR's origin and
verify the response `Content-Security-Policy` header includes it (DevTools → Network → the
document response). Add more
origins as space-separated values.

## Concurrency note (POC scope)
`jupyter-smart-on-fhir` currently stores one token at a time, so this template targets
**single-session / one-provider-at-a-time** use. For concurrent providers, the fix lands
upstream in `jupyter-smart-on-fhir` (per-session tokens) or via JupyterHub; the app's
token access is isolated in `provider_app/launch_context.py` to make that swap clean.
