import pytest
from provider_app import patient_resolver


class FakeClient:
    def __init__(self, patients):
        self._patients = patients  # {external_id: {"id": int, "identifier": str}}

    def lookup_patient(self, *, email=None, external_id=None):
        if external_id in self._patients:
            return self._patients[external_id]
        raise KeyError(f"No patient found with external identifier: {external_id!r}")


def test_resolve_patient_returns_jhe_id():
    client = FakeClient({"MRN-1": {"id": 42, "identifier": "MRN-1"}})
    assert patient_resolver.resolve_patient("MRN-1", client=client) == 42


def test_resolve_patient_not_found_raises_patientnotin_jhe():
    client = FakeClient({})
    with pytest.raises(patient_resolver.PatientNotInJHE):
        patient_resolver.resolve_patient("MRN-MISSING", client=client)


def test_resolver_override_hook():
    client = FakeClient({})
    patient_resolver.set_resolver(lambda mrn, c: 999)
    try:
        assert patient_resolver.resolve_patient("anything", client=client) == 999
    finally:
        patient_resolver.set_resolver(None)  # reset to default
