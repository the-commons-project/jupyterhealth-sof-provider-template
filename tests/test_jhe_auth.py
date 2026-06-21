import pytest
from provider_app import jhe_auth
from provider_app.launch_context import LaunchContext


def _context():
    return LaunchContext(
        access_token="ehr-access-token",
        fhir_base="https://ehr.example.org/fhir",
        fhir_patient_id="pat-1",
        patient_mrn="MRN-1",
    )


class FakeResponse:
    def __init__(self, payload, ok=True):
        self._payload = payload
        self.status_code = 200 if ok else 400
        self.text = "" if ok else "denied"

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError("token exchange failed")

    def json(self):
        return self._payload


def test_exchange_token_posts_subject_token_and_returns_jhe_token(monkeypatch):
    monkeypatch.setenv("JHE_URL", "https://jhe.example.org")
    captured = {}

    def fake_post(url, data=None, **kwargs):
        captured["url"] = url
        captured["data"] = data
        return FakeResponse({"access_token": "jhe-token"})

    monkeypatch.setattr(jhe_auth.requests, "post", fake_post)

    token = jhe_auth.exchange_token(_context())

    assert token == "jhe-token"
    assert captured["url"] == "https://jhe.example.org/o/token-exchange"
    assert captured["data"]["subject_token"] == "ehr-access-token"
    assert captured["data"]["audience"] == "https://jhe.example.org"
    # issuer defaults to the EHR FHIR base
    assert captured["data"]["iss"] == "https://ehr.example.org/fhir"


def test_exchange_token_issuer_override(monkeypatch):
    monkeypatch.setenv("JHE_URL", "https://jhe.example.org")
    monkeypatch.setenv("JHE_TRUSTED_ISS", "https://trusted.example.org/fhir")
    seen = {}
    monkeypatch.setattr(
        jhe_auth.requests, "post",
        lambda url, data=None, **kw: seen.update(data) or FakeResponse({"access_token": "t"}),
    )

    jhe_auth.exchange_token(_context())

    assert seen["iss"] == "https://trusted.example.org/fhir"


def test_exchange_token_raises_on_failure(monkeypatch):
    monkeypatch.setenv("JHE_URL", "https://jhe.example.org")
    monkeypatch.setattr(
        jhe_auth.requests, "post", lambda url, data=None, **kw: FakeResponse({}, ok=False)
    )
    with pytest.raises(jhe_auth.TokenExchangeError):
        jhe_auth.exchange_token(_context())


def test_client_for_launch_uses_static_token_when_set(monkeypatch):
    monkeypatch.setenv("JHE_URL", "https://jhe.example.org")
    monkeypatch.setenv("JHE_TOKEN", "static-token")

    def fail_post(*a, **kw):
        raise AssertionError("token exchange must not run when JHE_TOKEN is set")

    monkeypatch.setattr(jhe_auth.requests, "post", fail_post)

    client = jhe_auth.client_for_launch(_context())
    assert client.session.headers["Authorization"] == "Bearer static-token"


def test_client_for_launch_exchanges_when_no_static_token(monkeypatch):
    monkeypatch.setenv("JHE_URL", "https://jhe.example.org")
    monkeypatch.delenv("JHE_TOKEN", raising=False)
    monkeypatch.setattr(
        jhe_auth.requests, "post", lambda url, data=None, **kw: FakeResponse({"access_token": "minted"})
    )

    client = jhe_auth.client_for_launch(_context())
    assert client.session.headers["Authorization"] == "Bearer minted"
