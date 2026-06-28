# Jupyter server configuration for the SoF provider app.
# Loads the SMART-on-FHIR launch extension and Voilà in one server.
import os

from dotenv import load_dotenv

# Load .env so the settings below use your .env values — and so the notebook kernel,
# which inherits this process's environment, sees them too. Edit .env, not this file.
load_dotenv()

c.ServerApp.jpserver_extensions = {  # noqa: F821
    "jupyter_smart_on_fhir": True,
    "voila": True,
}

# --- SMART on FHIR launch (jupyter-smart-on-fhir) ---
# client_id comes from .env (SMART_CLIENT_ID) so you can paste the real value from your
# EHR app registration without editing this file; the fallback is a neutral placeholder.
# Public client + PKCE — no client secret is used.
c.SMARTExtensionApp.client_id = os.environ.get("SMART_CLIENT_ID", "00000000-0000-0000-0000-000000000000")  # noqa: F821
c.SMARTExtensionApp.scopes = os.environ.get("SMART_SCOPES", "openid fhirUser launch patient/*.read").split()  # noqa: F821

# --- Authentication ---
# The SMART launch + OAuth IS the auth layer for this app. jupyter-smart-on-fhir's
# launch/callback handlers are @authenticated, but the EHR reaches them with NO Jupyter
# token — so disable Jupyter's own token/password login, or the launch gets bounced to
# Jupyter's /login page. Access is gated by completing the EHR's OAuth flow instead.
# POC single-session model — see docs/deployment.md before exposing this publicly.
c.ServerApp.token = ""  # noqa: F821
c.ServerApp.password = ""  # noqa: F821

# --- Voilà (renders dashboard.ipynb as the provider-facing app) ---
c.VoilaConfiguration.file_allowlist = ["dashboard.ipynb"]  # noqa: F821
c.VoilaConfiguration.strip_sources = True  # noqa: F821
c.VoilaConfiguration.theme = "light"  # noqa: F821

# Land the provider on the dashboard. An EHR launch carries no 'next', so the SMART flow
# redirects to the server root — point the root at the Voilà-rendered notebook.
c.ServerApp.default_url = "/voila/render/dashboard.ipynb"  # noqa: F821

# --- Embed in the EHR iframe ---
# Voilà/Jupyter default to frame-ancestors 'self', which blocks the EHR from embedding.
# Allow the configured EHR origin. Add more origins as space-separated values.
c.ServerApp.tornado_settings = {  # noqa: F821
    "headers": {
        "Content-Security-Policy": "frame-ancestors 'self' " + os.environ.get("EHR_IFRAME_ORIGIN", "https://app.medplum.com")
    }
}
