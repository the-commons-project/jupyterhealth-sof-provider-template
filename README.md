# jupyterhealth-sof-provider-template

Cookiecutter template that scaffolds a SMART on FHIR **provider-launch** application
backed by the JupyterHealth Exchange (JHE). The generated app embeds in an EHR iframe,
resolves the launched patient to a JHE record **by MRN**, fetches their device data,
and renders it via a Voilà-served Jupyter notebook. You add analytics/viz by editing
one notebook cell.

## Generate a project

    pip install cookiecutter
    cookiecutter gh:the-commons-project/jupyterhealth-sof-provider-template

You'll be prompted for: project name, SMART `client_id`, JHE base URL, Epic FHIR base,
SMART scopes, the Epic iframe origin (for CSP), the MRN identifier system, and the
default data types.

## What you get
- `dashboard.ipynb` — **edit the marked cell** to add your analytics/visualization.
- `provider_app/` — launch context, MRN→JHE resolution, and data fetch (don't need to touch).
- `jupyter_server_config.py` — SMART + Voilà + CSP, pre-filled from your answers.
- `Dockerfile`, `docker-compose.yml`, `fly.toml.example` — deploy.
- `docs/epic-registration.md`, `docs/deployment.md` — register and ship it.

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
Generic infrastructure (a POC scaffold). You own clinical analytics, Epic registration,
security review, production deployment, and concurrent-provider hardening. See the
generated `docs/`.
