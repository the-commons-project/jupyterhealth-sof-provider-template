"""End-to-end smoke test: run dashboard.ipynb's code against fakes.

Proves launch_context -> jhe_data.fetch -> notebook viz wire together without a
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

    # Fake EHR Patient fetch (MRN extraction).
    # launch_context.current() uses `http_get=requests.get` as a default arg
    # bound at definition time, so we patch the whole `current` function to
    # return a fake LaunchContext directly — simpler and process-safe.
    fake_ctx = launch_context.LaunchContext(
        access_token="TEST",
        fhir_base="https://fhir.test",
        fhir_patient_id="P1",
        patient_mrn="MRN-1",
    )
    monkeypatch.setattr(launch_context, "current", lambda: fake_ctx)

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
