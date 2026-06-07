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
