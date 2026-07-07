"""Client for the ECB Data Portal API (SDMX-JSON).

Docs: https://data.ecb.europa.eu/help/api/overview
"""

import requests

BASE_URL = "https://data-api.ecb.europa.eu/service/data"
TIMEOUT = 30


def fetch_fx_rates(
    currencies: list[str],
    start_period: str | None = None,
    last_n: int | None = None,
) -> list[dict]:
    """Fetch daily EUR reference rates for the given currencies.

    Returns tidy records: {"date", "currency", "rate"}.
    Exactly one of start_period ("YYYY-MM-DD") or last_n should be given;
    with neither, the full history is returned.
    """
    key = f"D.{'+'.join(currencies)}.EUR.SP00.A"
    params: dict = {"format": "jsondata", "detail": "dataonly"}
    if start_period:
        params["startPeriod"] = start_period
    if last_n:
        params["lastNObservations"] = last_n

    resp = requests.get(f"{BASE_URL}/EXR/{key}", params=params, timeout=TIMEOUT)
    if resp.status_code == 404:  # no observations for the requested window
        return []
    resp.raise_for_status()
    return _parse_sdmx_json(resp.json())


def _parse_sdmx_json(payload: dict) -> list[dict]:
    """Flatten an SDMX-JSON dataset into tidy records.

    Series are keyed by colon-joined dimension indices ("0:1:0:0:0") that
    index into structure.dimensions.series; observation keys index into the
    TIME_PERIOD values under structure.dimensions.observation.
    """
    structure = payload["structure"]
    series_dims = structure["dimensions"]["series"]
    time_values = structure["dimensions"]["observation"][0]["values"]

    records = []
    for series_key, series in payload["dataSets"][0]["series"].items():
        dim_indices = [int(i) for i in series_key.split(":")]
        dims = {
            dim["id"]: dim["values"][idx]["id"]
            for dim, idx in zip(series_dims, dim_indices)
        }
        for obs_key, obs in series["observations"].items():
            if obs[0] is None:  # holidays / missing fixings
                continue
            records.append(
                {
                    "date": time_values[int(obs_key)]["id"],
                    "currency": dims["CURRENCY"],
                    "rate": obs[0],
                }
            )
    records.sort(key=lambda r: (r["date"], r["currency"]))
    return records
