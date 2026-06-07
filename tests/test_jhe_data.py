import json
import pandas as pd
import pytest
from provider_app import jhe_data


class FakeClient:
    def __init__(self):
        self.calls = []

    def lookup_patient(self, *, email=None, external_id=None):
        return {"id": 7, "identifier": external_id}

    def list_observations_df(self, patient_id=None, code=None, limit=2000):
        self.calls.append((patient_id, code))
        return pd.DataFrame(
            {
                "effective_time_frame_date_time": pd.to_datetime(
                    ["2026-06-01T00:00:00Z", "2026-06-05T00:00:00Z"], utc=True
                ),
                "heart_rate_value": [60, 72],
            }
        )


def test_fetch_returns_dict_of_dataframes():
    client = FakeClient()
    result = jhe_data.fetch("MRN-1", types=["heart_rate"], client=client)
    assert set(result.keys()) == {"heart_rate"}
    assert isinstance(result["heart_rate"], pd.DataFrame)
    assert len(result["heart_rate"]) == 2
    # patient resolved to id 7, queried with the heart-rate code
    assert client.calls[0][0] == 7


def test_fetch_filters_by_date_range():
    client = FakeClient()
    result = jhe_data.fetch(
        "MRN-1", types=["heart_rate"], client=client,
        start="2026-06-03", end="2026-06-10",
    )
    assert len(result["heart_rate"]) == 1  # only the 2026-06-05 row


def test_fetch_end_date_includes_intraday_observations():
    # `end` is an inclusive calendar date: a non-midnight reading on the end day is kept.
    class IntradayClient(FakeClient):
        def list_observations_df(self, patient_id=None, code=None, limit=2000):
            return pd.DataFrame({
                "effective_time_frame_date_time": pd.to_datetime(
                    ["2026-06-10T10:30:00Z", "2026-06-11T00:00:00Z"], utc=True
                ),
                "heart_rate_value": [80, 90],
            })

    result = jhe_data.fetch(
        "MRN-1", types=["heart_rate"], client=IntradayClient(),
        start="2026-06-01", end="2026-06-10",
    )
    # the 2026-06-10 10:30 reading is kept; the 2026-06-11 reading is excluded
    assert len(result["heart_rate"]) == 1


def test_data_type_codes_env_override(monkeypatch):
    monkeypatch.setenv("JHE_DATA_TYPE_CODES", json.dumps({"steps": "omh:step-count:9.9"}))
    assert jhe_data.code_for("steps") == "omh:step-count:9.9"


def test_unknown_data_type_raises():
    with pytest.raises(jhe_data.UnknownDataType):
        jhe_data.code_for("blood_pressure_made_up")
