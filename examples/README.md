# Example dashboards

Drop-in notebooks for a generated provider app. Each is launch-scoped: it reads the
SMART-launched patient via `provider_app.launch_context`, resolves the MRN to a JHE
patient, fetches that patient's data, and renders under Voilà.

> **These are optional starting points — not a step in setting up a project.** The normal
> workflow is to edit the `dashboard.ipynb` that ships in your generated project (the cell
> marked `ADD YOUR ANALYTICS + VISUALIZATION`) with your own analytics. Copy one of these
> examples over `dashboard.ipynb` *only* if it's a better starting point than writing your
> own. These notebooks live in the **template repo** (not inside generated projects), so
> you copy them from your template checkout, e.g.
> `cp <template>/examples/cgm-dashboard.ipynb <your-project>/dashboard.ipynb`.

## `cgm-dashboard.ipynb` — Continuous Glucose Monitoring (AGP report)

A single-patient CGM report: glycemic metrics (Mean, GMI, CV, Time-in-Range, GRI),
an Ambulatory Glucose Profile (AGP) percentile chart, and a Time-in-Range bar. The
analytics are adapted from the JupyterHealth
[CGM tutorial](https://jupyterhealth.github.io/software-documentation/tutorial/tutorial-cgm/),
rewired to run off the launch context instead of hardcoded ids.

### Use it in a generated project

1. Copy it over the generated dashboard (Voilà only serves a notebook named
   `dashboard.ipynb` — see `file_whitelist` in `jupyter_server_config.py`):
   ```
   cp examples/cgm-dashboard.ipynb <your-project>/dashboard.ipynb
   ```
2. It needs `matplotlib` (already in the template's `pyproject.toml`). No `cgmquantify`.
3. Iterate on visuals without a live launch using the **dev fallback** in the scaffold
   cell (comment the launch lines, hardcode `patient_id = 40006`; needs `$JHE_URL`/`$JHE_TOKEN`).

### Auth model (current)

JHE does not yet honor the EHR provider identity token, so this is **double auth**:
the provider logs into the **EHR** (Medplum) during the SMART launch, and the app holds a
**static `JHE_TOKEN`** for JHE (minted once, set in `.env`). There is no second interactive
JHE login per launch. `provider_app/jhe_auth.py` already supports token exchange too —
when JHE trusts the EHR issuer, drop `JHE_TOKEN` and it switches automatically.

## Reproducible demo values — Medplum (EHR) + jhe.fly.dev (JHE)

Verified against the fly.dev iglu seed (study **30006 — Iglu CGM Test Data**).

### The demo patient (recreate in Medplum)

| Field | Value |
|---|---|
| Given name | May |
| Family name | Nguyen |
| Birth date | 1984-07-11 |
| **`Patient.identifier.value`** | **`1636-69-001`** (confirm in the JHE portal → Patients → 40006) |
| `Patient.identifier.system` | whatever you set as `MRN_IDENTIFIER_SYSTEM` (you control both sides) |
| JHE patient id | 40006 |
| Data | ~1,846 `blood-glucose` (MGDL), Jan 2023 → Mar 2024, + some sleep/HR/SpO2 |

The resolver matches on identifier **value** only, so the EHR and JHE identifier
*systems* need not agree — just make the **values equal**.

### `.env` (static-token path)

```
JHE_URL=https://jhe.fly.dev
JHE_TOKEN=<token minted from the JHE portal /o/ PKCE flow>
MRN_IDENTIFIER_SYSTEM=<the system you stamped on the Medplum patient>
# JHE_TRUSTED_ISS=    # leave unset — no token exchange while double-auth
```

### cookiecutter answers that matter

```
jhe_base_url          = https://jhe.fly.dev
client_id             = <your Medplum SMART client_id>
ehr_iframe_origin     = https://app.medplum.com      # CSP frame-ancestors — NOT the default
mrn_identifier_system = <same system as the Medplum patient identifier>
```

Generation writes these into a gitignored `.env` (no `.env.example`); you add `JHE_TOKEN`.
(`data_types` and `ehr_fhir_base` are no longer prompts — the CGM notebook fetches
`blood_glucose` directly, and the FHIR base comes from the SMART launch token.)

### Medplum app registration

- Launch URL:   `http://localhost:8888/smart-on-fhir/launch`
- Redirect URL: `http://localhost:8888/smart-on-fhir/callback`
- Scopes:       `openid fhirUser launch patient/*.read`
