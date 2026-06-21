"""Authenticate to the JupyterHealth Exchange from the SMART launch.

The provider authenticates once into the EHR; JHE exchanges that EHR access token
for its own token via RFC 8693 token exchange, so there is no second OAuth login.
JHE must be configured to trust the EHR issuer (its TRUSTED_TOKEN_IDP) and have the
launching Practitioner on file keyed by the issuer's identifier.

A static $JHE_TOKEN, when set, is used instead as a dev/test shortcut.
"""
from __future__ import annotations

import os
from typing import Optional

import requests
from jupyterhealth_client import JupyterHealthClient

from .launch_context import LaunchContext

_ACCESS_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:access_token"
_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:token-exchange"


class TokenExchangeError(Exception):
    """Raised when JHE token exchange fails."""


def _jhe_url(jhe_url: Optional[str]) -> str:
    url = (jhe_url or os.environ.get("JHE_URL", "")).rstrip("/")
    if not url:
        raise TokenExchangeError("JHE_URL environment variable is not set.")
    return url


def exchange_token(context: LaunchContext, jhe_url: Optional[str] = None) -> str:
    """Exchange the SMART access token for a JHE access token (RFC 8693).

    JHE rejects issuers it is not configured to trust; the issuer defaults to the
    EHR FHIR base and can be overridden via $JHE_TRUSTED_ISS for proxy setups
    where the OIDC issuer differs from the FHIR base.
    """
    url = _jhe_url(jhe_url)
    iss = os.environ.get("JHE_TRUSTED_ISS", context.fhir_base).rstrip("/")
    try:
        response = requests.post(
            f"{url}/o/token-exchange",
            data={
                "subject_token": context.access_token,
                "subject_token_type": _ACCESS_TOKEN_TYPE,
                "requested_token_type": _ACCESS_TOKEN_TYPE,
                "audience": url,
                "grant_type": _GRANT_TYPE,
                "iss": iss,
                "scope": "openid",
            },
        )
        response.raise_for_status()
    except requests.RequestException as e:
        raise TokenExchangeError(f"JHE token exchange failed: {e}") from e
    return response.json()["access_token"]


def client_for_launch(context: LaunchContext, jhe_url: Optional[str] = None) -> JupyterHealthClient:
    """Return a JupyterHealthClient for this launch.

    Uses a static $JHE_TOKEN when set (dev/test shortcut); otherwise mints a JHE
    token from the SMART launch via token exchange.
    """
    url = _jhe_url(jhe_url)
    if os.environ.get("JHE_TOKEN"):
        return JupyterHealthClient(url=url)
    return JupyterHealthClient(url=url, token=exchange_token(context, url))
