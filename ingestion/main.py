"""CLI entry point: fetch all configured datasets and load them into a sink.

Usage:
    python -m ingestion.main --sink cloudsql --start-period 2020-01-01
    python -m ingestion.main --sink csv --output data/
"""

import argparse
import csv
from pathlib import Path

from ingestion import config, ecb, eurostat


def fetch_all(args) -> dict[str, list[dict]]:
    """Fetch every configured dataset; returns {name: tidy records}."""
    datasets = {}
    if args.source in ("ecb", "all"):
        datasets["fx_rates"] = ecb.fetch_fx_rates(
            config.FX_CURRENCIES,
            start_period=args.start_period,
            last_n=args.last_n,
        )
    if args.source in ("eurostat", "all"):
        for name, spec in config.EUROSTAT_DATASETS.items():
            records = eurostat.fetch_dataset(
                spec["dataset"], spec["filters"], last_periods=args.last_periods
            )
            # Keep only the reporting-relevant columns for the raw tables.
            datasets[name] = [
                {"geo": r["geo"], "time_period": r["time"], "value": r["value"]}
                for r in records
            ]
    return datasets


def sink_csv(datasets: dict[str, list[dict]], output_dir: Path) -> None:
    for name, records in datasets.items():
        path = output_dir / f"{name}.csv"
        if not records:
            print(f"{path.name}: no records returned, skipping")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
        print(f"{path.name}: {len(records)} rows")


def sink_cloudsql(datasets: dict[str, list[dict]]) -> None:
    from ingestion import db  # deferred: connector not needed for csv runs

    tables = {
        "fx_rates": ("raw.fx_rates", ["date", "currency"]),
        "inflation": ("raw.inflation", ["geo", "time_period"]),
        "unemployment": ("raw.unemployment", ["geo", "time_period"]),
    }
    connector, conn = db.connect()
    try:
        for name, records in datasets.items():
            table, key_cols = tables[name]
            n = db.upsert(conn, table, records, key_cols)
            print(f"{table}: upserted {n} rows")
    finally:
        conn.close()
        connector.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest ECB and Eurostat data")
    parser.add_argument("--source", choices=["ecb", "eurostat", "all"], default="all")
    parser.add_argument("--sink", choices=["csv", "cloudsql"], default="cloudsql")
    parser.add_argument("--output", type=Path, default=Path("data"),
                        help="csv sink: output directory")
    parser.add_argument("--start-period", help="ECB: fetch from this date (YYYY-MM-DD)")
    parser.add_argument("--last-n", type=int, help="ECB: fetch last N observations")
    parser.add_argument(
        "--last-periods", type=int, default=24,
        help="Eurostat: fetch last N time periods (default 24)",
    )
    args = parser.parse_args()

    datasets = fetch_all(args)
    if args.sink == "csv":
        sink_csv(datasets, args.output)
    else:
        sink_cloudsql(datasets)


if __name__ == "__main__":
    main()
