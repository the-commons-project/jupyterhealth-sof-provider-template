"""End-to-end smoke test: run dashboard.ipynb's code against fakes.

Proves launch_context -> jhe_auth -> jhe_data.fetch -> notebook viz wire together without a
real EHR or JHE. Executes the notebook's code cells in-process with fakes injected
(a real kernel would not see in-process monkeypatches). Run from the project root:
`pytest tests/test_smoke.py`.
"""
import json
from pathlib import Path

import nbformat
import pandas as pd
import plotly.io as pio

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_notebook_code_executes(tmp_path, monkeypatch):
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from provider_app import launch_context, jhe_data

    # Fake SMART token file + env
    token_file = tmp_path / "smart_token.json"
    token_file.write_text(json.dumps({
        "token": {"access_token": "TEST", "patient": "P1", "scope": "patient/*.read"},
        "fhir_url": "https://fhir.test",
        "smart_config": {},
    }))
    monkeypatch.setenv("SMART_TOKEN_FILE", str(token_file))
    monkeypatch.setenv("MRN_IDENTIFIER_SYSTEM", "urn:mrn")
    # Static $JHE_TOKEN takes the dev/test shortcut in jhe_auth.client_for_launch,
    # so the smoke test skips real token exchange.
    monkeypatch.setenv("JHE_URL", "https://jhe.test")
    monkeypatch.setenv("JHE_TOKEN", "TEST-JHE-TOKEN")

    # Fake the EHR Patient fetch so the REAL launch_context.current() runs
    # (token read + MRN extraction). current() resolves requests.get at call
    # time, so patching it here takes effect.
    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"id": "P1", "identifier": [{"system": "urn:mrn", "value": "MRN-1"}]}

    monkeypatch.setattr(launch_context.requests, "get", lambda url, headers=None: _Resp())

    # Fake JHE data
    def _fake_fetch(mrn, types, client=None, start=None, end=None):
        return {
            t: pd.DataFrame({
                "effective_time_frame_date_time": pd.to_datetime(["2026-06-01T00:00:00Z"], utc=True),
                "heart_rate_value": [65],
            })
            for t in types
        }

    monkeypatch.setattr(jhe_data, "fetch", _fake_fetch)

    # Keep plotly headless (no browser) during fig.show().
    # Empty string means "no renderer" — show() becomes a no-op without
    # requiring IPython (the "json" MIME renderer needs ipython to display).
    pio.renderers.default = ""

    nb = nbformat.read(str(PROJECT_ROOT / "dashboard.ipynb"), as_version=4)
    namespace: dict = {}
    for cell in nb.cells:
        if cell.cell_type == "code":
            exec(compile(cell.source, "<dashboard-cell>", "exec"), namespace)

    # the scaffolded cell should have populated `data` with the fetched frames
    assert "data" in namespace
    assert "heart_rate" in namespace["data"]
