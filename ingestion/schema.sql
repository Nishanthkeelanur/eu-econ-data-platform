-- Raw landing schema. Applied by ingestion/migrate.py as the postgres
-- admin user. IAM authentication only opens the door; regular Postgres
-- GRANTs below give the ingestion identities access to the tables.

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.fx_rates (
    date        date        NOT NULL,
    currency    text        NOT NULL,
    rate        numeric     NOT NULL,
    loaded_at   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (date, currency)
);

CREATE TABLE IF NOT EXISTS raw.inflation (
    geo         text        NOT NULL,
    time_period text        NOT NULL, -- 'YYYY-MM'
    value       numeric     NOT NULL,
    loaded_at   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (geo, time_period)
);

CREATE TABLE IF NOT EXISTS raw.unemployment (
    geo         text        NOT NULL,
    time_period text        NOT NULL, -- 'YYYY-MM'
    value       numeric     NOT NULL,
    loaded_at   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (geo, time_period)
);

GRANT USAGE ON SCHEMA raw
    TO "econ-ingestion@eu-econ-data-platform.iam", "keelanurnishanth@gmail.com";

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA raw
    TO "econ-ingestion@eu-econ-data-platform.iam", "keelanurnishanth@gmail.com";

ALTER DEFAULT PRIVILEGES IN SCHEMA raw
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES
    TO "econ-ingestion@eu-econ-data-platform.iam", "keelanurnishanth@gmail.com";

-- Read-only access for the BigQuery federated connection user
-- (created by terraform/bigquery.tf).
GRANT USAGE ON SCHEMA raw TO bq_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA raw TO bq_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT SELECT ON TABLES TO bq_reader;
