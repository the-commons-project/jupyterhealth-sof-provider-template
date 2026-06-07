import sys
from pathlib import Path

# Make the template's provider_app importable directly for unit tests.
_TEMPLATE_BODY = Path(__file__).parent / "{{cookiecutter.project_slug}}"
sys.path.insert(0, str(_TEMPLATE_BODY))
