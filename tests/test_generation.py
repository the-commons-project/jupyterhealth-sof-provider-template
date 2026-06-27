import tomllib


def test_bake_generates_project(cookies):
    result = cookies.bake(extra_context={"project_slug": "demo_app"})
    assert result.exit_code == 0
    assert result.exception is None
    assert result.project_path.name == "demo_app"
    assert (result.project_path / "provider_app").is_dir()
    assert (result.project_path / "dashboard.ipynb").is_file()
    assert (result.project_path / "jupyter_server_config.py").is_file()


def test_bake_renders_client_id(cookies):
    result = cookies.bake(extra_context={
        "project_slug": "demo_app",
        "client_id": "my-sof-client",
        "ehr_iframe_origin": "https://ehr.example.org",
    })
    assert result.exit_code == 0
    config = (result.project_path / "jupyter_server_config.py").read_text()
    assert "my-sof-client" in config
    assert "https://ehr.example.org" in config


def test_server_config_is_valid_python_and_wires_extensions(cookies):
    result = cookies.bake(extra_context={
        "project_slug": "demo_app",
        "client_id": "abc",
        "smart_scopes": "openid fhirUser launch patient/*.read",
        "ehr_iframe_origin": "https://ehr.example.org",
    })
    assert result.exit_code == 0
    config_path = result.project_path / "jupyter_server_config.py"
    source = config_path.read_text()
    # must compile as Python
    compile(source, str(config_path), "exec")
    assert "jupyter_smart_on_fhir" in source
    assert "voila" in source
    assert "frame-ancestors 'self'" in source
    assert "https://ehr.example.org" in source
    assert "openid fhirUser launch patient/*.read" in source
    # Jupyter's own token/password login must be disabled, else the EHR launch
    # (which carries no Jupyter token) is bounced to /login.
    assert 'c.ServerApp.token = ""' in source
    assert 'c.ServerApp.password = ""' in source


def test_voila_json_present_and_valid(cookies):
    import json as _json
    result = cookies.bake(extra_context={"project_slug": "demo_app"})
    voila = result.project_path / "voila.json"
    assert voila.is_file()
    data = _json.loads(voila.read_text())
    assert data["VoilaConfiguration"]["file_allowlist"] == ["dashboard.ipynb"]


def test_dashboard_notebook_structure(cookies):
    import nbformat
    result = cookies.bake(extra_context={"project_slug": "demo_app"})
    nb_path = result.project_path / "dashboard.ipynb"
    nb = nbformat.read(str(nb_path), as_version=4)
    source = "\n".join(cell["source"] for cell in nb.cells)
    assert "from provider_app import launch_context, jhe_auth, jhe_data" in source
    assert "jhe_auth.client_for_launch" in source
    assert "ADD YOUR ANALYTICS" in source
    assert "jhe_data.fetch" in source


def test_generated_pyproject_pins_deps(cookies):
    import tomllib
    result = cookies.bake(extra_context={"project_slug": "demo_app"})
    pyproject = (result.project_path / "pyproject.toml").read_text()
    data = tomllib.loads(pyproject)
    deps = data["project"]["dependencies"]
    assert any("jupyter-smart-on-fhir" in d for d in deps)
    assert any(d.startswith("jupyterhealth-client>=0.2.0") for d in deps)
    assert any(d.startswith("voila") for d in deps)


def test_env_created_by_hook_and_no_example(cookies):
    result = cookies.bake(extra_context={
        "project_slug": "demo_app", "jhe_base_url": "https://jhe.test"
    })
    # The post-gen hook writes .env from the answers; we intentionally ship NO .env.example.
    assert not (result.project_path / ".env.example").exists()
    env = (result.project_path / ".env").read_text()
    for var in ["JHE_URL", "JHE_TOKEN", "SMART_CLIENT_ID", "SMART_SCOPES",
                "EHR_IFRAME_ORIGIN", "MRN_IDENTIFIER_SYSTEM"]:
        assert var in env
    assert "https://jhe.test" in env


def test_docs_present_with_key_sections(cookies):
    result = cookies.bake(extra_context={
        "project_slug": "demo_app",
        "smart_scopes": "openid fhirUser launch patient/*.read",
    })
    ehr_doc = (result.project_path / "docs" / "ehr-registration.md").read_text()
    deploy = (result.project_path / "docs" / "deployment.md").read_text()
    assert "patient/*.read" in ehr_doc
    assert "security review" in ehr_doc.lower()
    assert "frame-ancestors" in deploy
    assert "MRN_IDENTIFIER_SYSTEM" in deploy


def test_quickstart_walks_user_through(cookies):
    result = cookies.bake(extra_context={"project_slug": "demo_app"})
    quickstart = (result.project_path / "docs" / "QUICKSTART.md").read_text()
    # the end-to-end journey is covered
    assert "Prerequisites" in quickstart
    assert "JHE_TOKEN" in quickstart
    assert "Admin SPA" in quickstart  # how to get a JHE token
    assert "smart-on-fhir/launch" in quickstart  # how to simulate a launch
    assert "MedPlum" in quickstart
    assert "Troubleshooting" in quickstart


def test_baked_project_smoke_runs(cookies):
    import subprocess
    import sys
    result = cookies.bake(extra_context={"project_slug": "demo_app"})
    assert result.exit_code == 0
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_smoke.py", "-q"],
        cwd=str(result.project_path), capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
