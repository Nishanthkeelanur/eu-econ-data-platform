# Raw landing zone: smallest possible Cloud SQL PostgreSQL instance.
# Connections go through the Cloud SQL Python Connector with IAM database
# authentication - no passwords, no 0.0.0.0/0 authorized networks.

resource "google_sql_database_instance" "raw" {
  name             = "econ-raw"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier    = "db-f1-micro" # shared-core, cheapest tier
    edition = "ENTERPRISE"

    ip_configuration {
      ipv4_enabled = true # public IP, but no authorized networks:
      # access only via Cloud SQL connector (IAM-authenticated)
    }

    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }

    backup_configuration {
      enabled = false # raw data is fully re-derivable from the source APIs
    }

    insights_config {
      query_insights_enabled = true
    }
  }

  deletion_protection = false # portfolio project: allow terraform destroy
}

resource "google_sql_database" "econ" {
  name     = "econ"
  instance = google_sql_database_instance.raw.name
}

# IAM database user for the ingestion service account. Postgres truncates
# the username to the SA email without the ".gserviceaccount.com" suffix.
resource "google_sql_user" "ingestion" {
  name     = trimsuffix(google_service_account.ingestion.email, ".gserviceaccount.com")
  instance = google_sql_database_instance.raw.name
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"
}

# IAM database user for the human owner (psql access from the console).
resource "google_sql_user" "owner" {
  name     = "keelanurnishanth@gmail.com"
  instance = google_sql_database_instance.raw.name
  type     = "CLOUD_IAM_USER"
}
