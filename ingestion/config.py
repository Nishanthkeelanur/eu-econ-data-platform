"""Dataset definitions for all ingested sources.

Adding a new Eurostat dataset means adding one entry to EUROSTAT_DATASETS;
the client and CLI pick it up automatically.
"""

# Cloud SQL raw landing zone (created by terraform/cloudsql.tf).
SQL_CONNECTION_NAME = "eu-econ-data-platform:europe-west3:econ-raw"
SQL_DATABASE = "econ"

# Currencies quoted against EUR in the ECB EXR dataflow.
FX_CURRENCIES = ["USD", "GBP", "JPY", "CHF"]

# Countries / aggregates pulled from Eurostat. EA20 = euro area.
GEOS = ["EA20", "DE", "FR", "IT", "ES", "NL"]

EUROSTAT_DATASETS = {
    "inflation": {
        "dataset": "prc_hicp_manr",
        "table": "raw.inflation",
        "filters": {
            "coicop": "CP00",  # all-items HICP
            "unit": "RCH_A",   # annual rate of change
            "geo": GEOS,
        },
    },
    "unemployment": {
        "dataset": "une_rt_m",
        "table": "raw.unemployment",
        "filters": {
            "s_adj": "SA",      # seasonally adjusted
            "age": "TOTAL",
            "sex": "T",
            "unit": "PC_ACT",   # % of active population
            "geo": GEOS,
        },
    },
}
