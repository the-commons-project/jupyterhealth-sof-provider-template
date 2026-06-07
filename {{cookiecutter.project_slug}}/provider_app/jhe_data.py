"""Fetch a patient's device data from the JupyterHealth Exchange.

Returns one tidy pandas DataFrame per requested data type (the OMH types are
heterogeneous, so we keep them separate rather than forcing one schema).
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

import pandas as pd
from jupyterhealth_client import Code, JupyterHealthClient

from . import patient_resolver

# Friendly data-type name -> JHE code. Code enum members where available;
# string OMH codes otherwise. `steps` is provisional — confirm against the
# active ingestion path (Garmin shim / Validic). Override via JHE_DATA_TYPE_CODES.
_DEFAULT_DATA_TYPE_CODES: dict[str, object] = {
    "heart_rate": Code.HEART_RATE,
    "sleep": Code.SLEEP_STAGE_SUMMARY,
    "steps": "omh:step-count:3.0",
}

_TIME_COLUMN = "effective_time_frame_date_time"


class UnknownDataType(Exception):
    """Raised when a requested data type has no configured JHE code."""


def _configured_codes() -> dict[str, object]:
    codes = dict(_DEFAULT_DATA_TYPE_CODES)
    override = os.environ.get("JHE_DATA_TYPE_CODES")
    if override:
        codes.update(json.loads(override))
    return codes


def code_for(data_type: str) -> object:
    codes = _configured_codes()
    if data_type not in codes:
        raise UnknownDataType(
            f"No JHE code configured for data type {data_type!r}. "
            f"Add it via JHE_DATA_TYPE_CODES."
        )
    return codes[data_type]


def _filter_dates(df: pd.DataFrame, start: Optional[str], end: Optional[str]) -> pd.DataFrame:
    if df.empty or _TIME_COLUMN not in df.columns:
        return df
    if start is not None:
        df = df[df[_TIME_COLUMN] >= pd.Timestamp(start, tz="UTC")]
    if end is not None:
        df = df[df[_TIME_COLUMN] <= pd.Timestamp(end, tz="UTC")]
    return df


def fetch(
    mrn: str,
    types: list[str],
    client: Optional[Any] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> dict[str, pd.DataFrame]:
    """Resolve the MRN to a JHE patient and return {data_type: tidy DataFrame}.

    `client` defaults to a JupyterHealthClient built from $JHE_URL / $JHE_TOKEN.
    `start`/`end` are inclusive ISO dates applied client-side.
    """
    if client is None:
        client = JupyterHealthClient()
    patient_id = patient_resolver.resolve_patient(mrn, client=client)

    out: dict[str, pd.DataFrame] = {}
    for data_type in types:
        df = client.list_observations_df(patient_id=patient_id, code=code_for(data_type))
        out[data_type] = _filter_dates(df, start, end)
    return out
