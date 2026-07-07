"""CLI entry point: fetch all configured datasets and write tidy CSVs.

Usage:
    python -m ingestion.main --source all --output data/
    python -m ingestion.main --source ecb --last-n 30
"""

import argparse
import csv
from pathlib import Path

from ingestion import config, ecb, eurostat


def run_ecb(output_dir: Path, start_period: str | None, last_n: int | None) -> None:
    records = ecb.fetch_fx_rates(
        config.FX_CURRENCIES, start_period=start_period, last_n=last_n
    )
    _write_csv(output_dir / "ecb_fx_rates.csv", records)


def run_eurostat(output_dir: Path, last_periods: int | None) -> None:
    for name, spec in config.EUROSTAT_DATASETS.items():
        records = eurostat.fetch_dataset(
            spec["dataset"], spec["filters"], last_periods=last_periods
        )
        _write_csv(output_dir / f"eurostat_{name}.csv", records)


def _write_csv(path: Path, records: list[dict]) -> None:
    if not records:
        print(f"{path.name}: no records returned, skipping")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    print(f"{path.name}: {len(records)} rows")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest ECB and Eurostat data")
    parser.add_argument("--source", choices=["ecb", "eurostat", "all"], default="all")
    parser.add_argument("--output", type=Path, default=Path("data"))
    parser.add_argument("--start-period", help="ECB: fetch from this date (YYYY-MM-DD)")
    parser.add_argument("--last-n", type=int, help="ECB: fetch last N observations")
    parser.add_argument(
        "--last-periods", type=int, default=24,
        help="Eurostat: fetch last N time periods (default 24)",
    )
    args = parser.parse_args()

    if args.source in ("ecb", "all"):
        run_ecb(args.output, args.start_period, args.last_n)
    if args.source in ("eurostat", "all"):
        run_eurostat(args.output, args.last_periods)


if __name__ == "__main__":
    main()
