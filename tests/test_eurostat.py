"""Unit tests for the JSON-stat 2.0 parser."""

from ingestion.eurostat import parse_jsonstat

# Minimal JSON-stat payload: 2 geos x 3 months, one missing observation.
PAYLOAD = {
    "id": ["freq", "geo", "time"],
    "size": [1, 2, 3],
    "dimension": {
        "freq": {"category": {"label": {"M": "Monthly"}}},
        "geo": {"category": {"index": {"DE": 0, "FR": 1}}},
        "time": {"category": {"index": {"2025-10": 0, "2025-11": 1, "2025-12": 2}}},
    },
    "value": {"0": 2.1, "1": 2.2, "2": 2.0, "3": 1.1, "5": 0.9},
}


def test_unravels_flat_indices_to_dimension_codes():
    records = parse_jsonstat(PAYLOAD)
    assert len(records) == 5
    de_dec = next(r for r in records if r["geo"] == "DE" and r["time"] == "2025-12")
    assert de_dec == {"freq": "M", "geo": "DE", "time": "2025-12", "value": 2.0}


def test_missing_observations_are_skipped():
    records = parse_jsonstat(PAYLOAD)
    # index 4 (FR, 2025-11) is absent from "value" and must not appear
    assert not any(r["geo"] == "FR" and r["time"] == "2025-11" for r in records)


def test_empty_value_map_returns_no_records():
    assert parse_jsonstat({**PAYLOAD, "value": {}}) == []
