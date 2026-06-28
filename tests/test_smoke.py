"""End-to-end smoke test: run dashboard.ipynb's code against fakes.

Proves launch_context -> jhe_auth -> jhe_data.fetch -> notebook viz wire together without a
real EHR or JHE. Executes the notebook's code cells in-process with fakes injected
(a real kernel would not see in-process monkeypatches). Run from the project root:
`pytest tests/test_smoke.py`.

Asserts the DEFAULT scaffold's contract (a `data` dict containing `heart_rate`). If you
replace dashboard.ipynb — e.g. `cp examples/cgm-dashboard.ipynb dashboard.ipynb` — or
change the scaffold cell, adapt these assertions or skip this test.
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
    from provider_app import launch_context, jhe_auth, jhe_data

    # Fake SMART token file + env
    token_file = tmp_path / "smart_token.json"
    token_file.write_text(json.dumps({
        "token": {"access_token": "TEST", "id_token": "TEST-ID-TOKEN", "patient": "P1", "scope": "patient/*.read openid fhirUser"},
        "fhir_url": "https://fhir.test",
        "smart_config": {},
    }))
    monkeypatch.setenv("SMART_TOKEN_FILE", str(token_file))
    monkeypatch.setenv("MRN_IDENTIFIER_SYSTEM", "urn:mrn")
    monkeypatch.setenv("JHE_URL", "https://jhe.test")
    # Mock the JHE token exchange so jhe_auth.client_for_launch runs its real code
    # path (there's no static-token shortcut) without hitting a live JHE.
    monkeypatch.setattr(jhe_auth, "exchange_token", lambda ctx, *a, **k: "TEST-JHE-TOKEN")

    # Fake the EHR Patient fetch so the REAL launch_context.current() runs
    # (token read + MRN extraction). current() resolves requests.get at call
    # time, so patching it here takes effect.
    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"id": "P1", "identifier": [{"system": "urn:mrn", "value": "MRN-1"}]}

    monkeypatch.setattr(launch_context.requests, "get", lambda url, headers=None: _Resp())

    # Fake JHE data. fetch() now takes the LaunchContext (and runs the identity
    # guard internally); we stub the whole thing so the smoke test stays focused on
    # the notebook wiring rather than the EHR/JHE identity round-trip.
    def _fake_fetch(ctx, types, client=None, start=None, end=None):
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
