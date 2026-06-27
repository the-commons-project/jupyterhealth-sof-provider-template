# {{ cookiecutter.project_name }}

A SMART on FHIR provider-launch app generated from
jupyterhealth-sof-provider-template. It launches inside an EHR (e.g. Epic), resolves
the launched patient to a JupyterHealth Exchange record by MRN, fetches their device
data, and renders it via a Voilà-served Jupyter notebook.

## Where to start
- **`docs/QUICKSTART.md`** — **start here.** End-to-end: get a JHE token, configure,
  simulate a SMART launch (MedPlum or fully local), and see data on screen.
- **`dashboard.ipynb`** — edit the cell marked `ADD YOUR ANALYTICS + VISUALIZATION`
  to add your own analytics/visualization. The cells above it (launch context + data
  fetch) are scaffolded; you normally don't touch them.
- **`docs/deployment.md`** — configure (`.env`), run, deploy, and the iframe/CSP gotcha.
- **`docs/ehr-registration.md`** — register the app with your EHR and start security review.

## Develop
    # generation already created .env from your answers (it is gitignored).
    # Edit .env: add JHE_TOKEN (JHE_URL / SMART_CLIENT_ID / SMART_SCOPES /
    # EHR_IFRAME_ORIGIN / MRN_IDENTIFIER_SYSTEM are pre-filled). All config is read
    # from .env at runtime, so edits take effect on the next run — no code changes.
    pip install -e ".[test]"
    docker compose up --build      # run; complete a SMART launch from your EHR / MedPlum
    pytest tests/test_smoke.py     # end-to-end smoke against fakes

## Notes
- This is a POC scaffold. It targets **one provider session at a time** — see the
  concurrency note in `docs/deployment.md`. You own clinical analytics, EHR
  registration, security review, and production hardening.
- Voilà is the notebook renderer used here; it is one option. Other tools (Panel,
  voici, plain nbconvert) can turn a notebook into a web page if you prefer.
