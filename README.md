# jupyterhealth-sof-provider-template

Cookiecutter template that scaffolds a SMART on FHIR **provider-launch** application
backed by the JupyterHealth Exchange (JHE). The generated app embeds in an EHR iframe,
resolves the launched patient to a JHE record **by MRN**, fetches their device data,
and renders it via a Voilà-served Jupyter notebook. You add analytics/viz by editing
one notebook cell.

## Before you generate — have these ready

Generating takes a minute; the values it prompts for come from two systems you set up
first. Gather these so the answers are obvious:

**From your EHR (Epic, Medplum, …) — where the app launches:**
- The EHR's **web origin** that will embed the app in an iframe (e.g. `https://app.medplum.com`) — needed for the CSP.
- A registered **SMART app** there, which gives you a **`client_id`**. You can register
  *after* generating and paste the real `client_id` into `.env` (`SMART_CLIENT_ID`) — a
  placeholder works at generation time.
- A choice of which **`Patient.identifier` system** holds the MRN. You'll set this same
  system + value on your test patient in the EHR.

**From your JupyterHealth Exchange (JHE) instance — where the data lives:**
- Its **base URL** (e.g. `https://jhe.fly.dev`).
- A **patient with data**, and that patient's **external identifier** (the MRN). The EHR
  patient's identifier *value* must equal this — it's the join key between the two systems.
- JHE configured to **trust your EHR** so it accepts the id_token exchange (the app reads
  data with the token it mints at launch — no separate JHE token). See the generated
  `docs/QUICKSTART.md`.

**On your machine:** Python 3.11+, `cookiecutter`, and (optionally) Docker.

## Generate a project

    pip install cookiecutter
    # from a local checkout (current):
    cookiecutter /path/to/jupyterhealth-sof-provider-template
    # or, once published to the jupyterhealth org (public):
    cookiecutter gh:jupyterhealth/jupyterhealth-sof-provider-template

You'll be prompted for: project name, SMART `client_id`, JHE base URL, SMART scopes,
the EHR iframe origin (for CSP), and the MRN identifier system. Each prompt shows a
one-line description of what to enter. The generator then writes a ready-to-edit `.env`
from your answers (no `.env.example` — see below); the app mints its JHE token at launch
via the id_token exchange, so there's nothing to paste in.

## What you get
- `dashboard.ipynb` — **edit the marked cell** to add your analytics/visualization.
- `provider_app/` — launch context, MRN→JHE resolution, and data fetch (don't need to touch).
- `jupyter_server_config.py` — SMART + Voilà + CSP, pre-filled from your answers.
- `Dockerfile`, `docker-compose.yml`, `fly.toml.example` — deploy.
- `docs/QUICKSTART.md` — end-to-end walkthrough (configure the id_token exchange, simulate a launch, see data).
- `docs/ehr-registration.md`, `docs/deployment.md` — register and ship it.

## Develop
    cd <your-project>
    pip install -e ".[test]"
    docker compose up --build      # run; complete a SMART launch from your EHR/MedPlum
    pytest tests/test_smoke.py     # end-to-end smoke against fakes

## Built on
- [`jupyter-smart-on-fhir`](https://github.com/jupyterhealth/jupyter-smart-on-fhir) (SMART launch)
- [`jupyterhealth-client`](https://github.com/jupyterhealth/jupyterhealth-client) (JHE Read API)
- [Voilà](https://voila.readthedocs.io/) (notebook → web app)

## Scope
Generic infrastructure (a POC scaffold). You own clinical analytics, EHR registration,
security review, production deployment, and concurrent-provider hardening. See the
generated `docs/`.
