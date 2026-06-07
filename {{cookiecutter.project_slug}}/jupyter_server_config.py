# Jupyter server configuration for the generated SoF provider app.
# Loads the SMART-on-FHIR launch extension and Voilà in one server.

c.ServerApp.jpserver_extensions = {  # noqa: F821
    "jupyter_smart_on_fhir": True,
    "voila": True,
}

# --- SMART on FHIR launch (jupyter-smart-on-fhir) ---
c.SMARTExtensionApp.client_id = "{{ cookiecutter.client_id }}"  # noqa: F821
c.SMARTExtensionApp.scopes = [{{ cookiecutter.smart_scopes.split(' ') | map('tojson') | join(', ') }}]  # noqa: F821

# --- Voilà (renders dashboard.ipynb as the provider-facing app) ---
c.VoilaConfiguration.file_whitelist = ["dashboard.ipynb"]  # noqa: F821
c.VoilaConfiguration.strip_sources = True  # noqa: F821
c.VoilaConfiguration.theme = "light"  # noqa: F821

# --- Embed in the EHR iframe ---
# Voilà/Jupyter default to frame-ancestors 'self', which blocks Epic embedding.
# Allow the configured EHR origin. Add more origins as space-separated values.
c.ServerApp.tornado_settings = {  # noqa: F821
    "headers": {
        "Content-Security-Policy": "frame-ancestors 'self' {{ cookiecutter.epic_iframe_origin }}"
    }
}
