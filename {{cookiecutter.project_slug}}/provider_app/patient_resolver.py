"""Resolve an EHR MRN to a JupyterHealth Exchange patient id.

Default strategy: JHE stores the MRN as the patient's external identifier, so we
look the patient up by external_id. Override via set_resolver() for institutions
whose mapping differs.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

_override: Optional[Callable[[str, Any], int]] = None


class PatientNotInJHE(Exception):
    """Raised when no JHE patient matches the given MRN."""


def set_resolver(resolver: Optional[Callable[[str, Any], int]]) -> None:
    """Install a custom MRN -> jhe_patient_id resolver, or None to reset to default."""
    global _override
    _override = resolver


def _default_resolver(mrn: str, client: Any) -> int:
    try:
        patient = client.lookup_patient(external_id=mrn)
    except KeyError as e:
        raise PatientNotInJHE(
            f"No JupyterHealth patient found for MRN {mrn!r}."
        ) from e
    return patient["id"]


def resolve_patient(mrn: str, client: Any) -> int:
    """Return the JHE patient id for the given MRN."""
    resolver = _override or _default_resolver
    return resolver(mrn, client)
