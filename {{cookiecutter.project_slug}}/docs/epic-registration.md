# Registering this app with Epic

This app is a **SMART on FHIR provider-launch** application. Register it under your
own Epic organization; The Commons Project is not involved in your registration or
security review.

## 1. Create the app in the Epic App Orchard / vendor portal
- App type: **Provider-facing (EHR launch)**
- Launch URL: `https://<your-host>/smart-on-fhir/launch`
- Redirect/OAuth callback URL: `https://<your-host>/smart-on-fhir/callback`
- Client type: **Public client (PKCE)**

## 2. Request these SMART scopes
```
{{ cookiecutter.smart_scopes }}
```
`launch` is required for EHR launch; `patient/*.read` lets the app read the launched
patient. Add `fhirUser`/`openid` for identity.

## 3. Find your MRN identifier system
The app matches the Epic patient to JHE by MRN. In Epic, inspect a test
`Patient.identifier` and copy the `system` value of the MRN identifier into
`MRN_IDENTIFIER_SYSTEM` (see deployment.md).

## 4. Start your institutional security review
Provide your security team: the deploy host, the SMART scopes above, and a note that
no PHI is persisted by the app (data is fetched per-session from JHE). Your security
review timeline is owned by your institution.
