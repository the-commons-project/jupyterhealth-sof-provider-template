# Deploying this app

## Configure
Copy `.env.example` to `.env` and set:
- `JHE_URL` — your JupyterHealth Exchange base URL
- `JHE_TOKEN` — a JHE API token authorized to read your patients
- `MRN_IDENTIFIER_SYSTEM` — the Epic `Patient.identifier` system that holds the MRN
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
**blocks Epic from embedding the app** and shows a blank frame. `jupyter_server_config.py`
sets:
```
frame-ancestors 'self' {{ cookiecutter.epic_iframe_origin }}
```
If Epic shows a blank frame, verify the response `Content-Security-Policy` header
includes your Epic origin (DevTools → Network → the document response). Add more
origins as space-separated values.

## Concurrency note (POC scope)
`jupyter-smart-on-fhir` currently stores one token at a time, so this template targets
**single-session / one-provider-at-a-time** use. For concurrent providers, the fix lands
upstream in `jupyter-smart-on-fhir` (per-session tokens) or via JupyterHub; the app's
token access is isolated in `provider_app/launch_context.py` to make that swap clean.
