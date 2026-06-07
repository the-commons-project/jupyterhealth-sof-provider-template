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
        "epic_iframe_origin": "https://epic.example.org",
    })
    assert result.exit_code == 0
    config = (result.project_path / "jupyter_server_config.py").read_text()
    assert "my-sof-client" in config
    assert "https://epic.example.org" in config


def test_server_config_is_valid_python_and_wires_extensions(cookies):
    result = cookies.bake(extra_context={
        "project_slug": "demo_app",
        "client_id": "abc",
        "smart_scopes": "openid fhirUser launch patient/*.read",
        "epic_iframe_origin": "https://epic.example.org",
    })
    assert result.exit_code == 0
    config_path = result.project_path / "jupyter_server_config.py"
    source = config_path.read_text()
    # must compile as Python
    compile(source, str(config_path), "exec")
    assert "jupyter_smart_on_fhir" in source
    assert "voila" in source
    assert "frame-ancestors 'self' https://epic.example.org" in source
    assert '"openid", "fhirUser", "launch", "patient/*.read"' in source


def test_voila_json_present_and_valid(cookies):
    import json as _json
    result = cookies.bake(extra_context={"project_slug": "demo_app"})
    voila = result.project_path / "voila.json"
    assert voila.is_file()
    data = _json.loads(voila.read_text())
    assert data["VoilaConfiguration"]["file_whitelist"] == ["dashboard.ipynb"]


def test_dashboard_notebook_structure(cookies):
    import nbformat
    result = cookies.bake(extra_context={"project_slug": "demo_app"})
    nb_path = result.project_path / "dashboard.ipynb"
    nb = nbformat.read(str(nb_path), as_version=4)
    source = "\n".join(cell["source"] for cell in nb.cells)
    assert "from provider_app import launch_context, jhe_data" in source
    assert "ADD YOUR ANALYTICS" in source
    assert "jhe_data.fetch" in source


def test_generated_pyproject_pins_deps(cookies):
    import tomllib
    result = cookies.bake(extra_context={"project_slug": "demo_app"})
    pyproject = (result.project_path / "pyproject.toml").read_text()
    data = tomllib.loads(pyproject)
    deps = data["project"]["dependencies"]
    assert any(d.startswith("jupyter-smart-on-fhir==0.1.0a3") for d in deps)
    assert any(d.startswith("jupyterhealth-client>=0.2.0") for d in deps)
    assert any(d.startswith("voila") for d in deps)


def test_env_example_lists_required_vars(cookies):
    result = cookies.bake(extra_context={
        "project_slug": "demo_app", "jhe_base_url": "https://jhe.test"
    })
    env = (result.project_path / ".env.example").read_text()
    for var in ["JHE_URL", "JHE_TOKEN", "MRN_IDENTIFIER_SYSTEM"]:
        assert var in env
    assert "https://jhe.test" in env
