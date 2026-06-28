"""Post-generation: create a ready-to-edit .env from the cookiecutter answers.

We intentionally ship NO .env.example. A file named ``*.example`` reads as
"safe to commit", but it would carry this deployment's real (non-secret) values
and people commit it without thinking. So the real config goes straight into
.env, which .gitignore excludes — and the required variables are documented in
README.md / docs/ instead.
"""
from pathlib import Path

ENV_CONTENTS = """\
# Local config for THIS deployment — gitignored, do NOT commit.
# Pre-filled from your cookiecutter answers. The app mints its JHE token at launch
# by exchanging the EHR id_token (RFC 8693), so there is no token to paste here.
JHE_URL={{ cookiecutter.jhe_base_url }}
SMART_CLIENT_ID={{ cookiecutter.client_id }}
SMART_SCOPES={{ cookiecutter.smart_scopes }}
EHR_IFRAME_ORIGIN={{ cookiecutter.ehr_iframe_origin }}
MRN_IDENTIFIER_SYSTEM={{ cookiecutter.mrn_identifier_system }}

# Optional:
# JHE_TRUSTED_ISS=
"""

Path(".env").write_text(ENV_CONTENTS)
print("\n  Created .env from your answers. Confirm JHE trusts your EHR issuer, then run.\n")
