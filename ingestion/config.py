"""Dataset definitions for all ingested sources.

Adding a new Eurostat dataset means adding one entry to EUROSTAT_DATASETS;
the client and CLI pick it up automatically.
"""

# Currencies quoted against EUR in the ECB EXR dataflow.
FX_CURRENCIES = ["USD", "GBP", "JPY", "CHF"]

# Countries / aggregates pulled from Eurostat. EA20 = euro area.
GEOS = ["EA20", "DE", "FR", "IT", "ES", "NL"]

EUROSTAT_DATASETS = {
    "inflation": {
        "dataset": "prc_hicp_manr",
        "filters": {
            "coicop": "CP00",  # all-items HICP
            "unit": "RCH_A",   # annual rate of change
            "geo": GEOS,
        },
    },
    "unemployment": {
        "dataset": "une_rt_m",
        "filters": {
            "s_adj": "SA",      # seasonally adjusted
            "age": "TOTAL",
            "sex": "T",
            "unit": "PC_ACT",   # % of active population
            "geo": GEOS,
        },
    },
}
