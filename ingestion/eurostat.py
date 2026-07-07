"""Client for the Eurostat dissemination API (JSON-stat 2.0).

Docs: https://ec.europa.eu/eurostat/web/query-builder/getting-started/api
"""

import requests

BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
TIMEOUT = 30


def fetch_dataset(
    dataset: str,
    filters: dict,
    since_period: str | None = None,
    last_periods: int | None = None,
) -> list[dict]:
    """Fetch a Eurostat dataset and return tidy records.

    Each record maps every dimension id (lowercased) to its code, plus a
    "value" key, e.g. {"freq": "M", "geo": "DE", "time": "2025-12", "value": 2.0}.
    Dimension filters accept scalars or lists (sent as repeated params).
    """
    params: dict = {"format": "JSON", "lang": "EN", **filters}
    if since_period:
        params["sinceTimePeriod"] = since_period
    if last_periods:
        params["lastTimePeriod"] = last_periods

    resp = requests.get(f"{BASE_URL}/{dataset}", params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return parse_jsonstat(resp.json())


def parse_jsonstat(payload: dict) -> list[dict]:
    """Unravel a JSON-stat 2.0 response into tidy records.

    payload["value"] maps a flattened row-major index (as a string) to the
    observation value; the index is decoded against payload["size"] with the
    dimension order given by payload["id"].
    """
    dim_ids = payload["id"]
    sizes = payload["size"]
    position_to_code = [
        _position_to_code(payload["dimension"][dim_id]["category"])
        for dim_id in dim_ids
    ]

    records = []
    for flat_index, value in payload.get("value", {}).items():
        remaining = int(flat_index)
        coords = [0] * len(sizes)
        for i in range(len(sizes) - 1, -1, -1):
            coords[i] = remaining % sizes[i]
            remaining //= sizes[i]
        record = {
            dim_id.lower(): position_to_code[i][coords[i]]
            for i, dim_id in enumerate(dim_ids)
        }
        record["value"] = value
        records.append(record)
    records.sort(key=lambda r: (r.get("time", ""), r.get("geo", "")))
    return records


def _position_to_code(category: dict) -> dict[int, str]:
    """Map ordinal positions to category codes for one dimension."""
    index = category.get("index")
    if index is None:  # single-category dimension: index is implicit
        return {0: next(iter(category["label"]))}
    if isinstance(index, list):
        return dict(enumerate(index))
    return {position: code for code, position in index.items()}
