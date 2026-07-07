# Analytics layer: BigQuery datasets + a federated connection to Cloud SQL.
# Dataform models pull raw tables through EXTERNAL_QUERY over this
# connection and build staging views and reporting marts on top.

resource "google_bigquery_dataset" "raw" {
  dataset_id  = "raw"
  description = "Raw tables synced from Cloud SQL via EXTERNAL_QUERY"
  location    = var.region
}

resource "google_bigquery_dataset" "staging" {
  dataset_id  = "staging"
  description = "Dataform staging views (cleaned + typed)"
  location    = var.region
}

resource "google_bigquery_dataset" "marts" {
  dataset_id  = "marts"
  description = "Dataform reporting marts"
  location    = var.region
}

resource "google_bigquery_dataset" "assertions" {
  dataset_id  = "dataform_assertions"
  description = "Dataform data-quality assertion results"
  location    = var.region
}

# BigQuery's Cloud SQL connections authenticate with a database user and
# password (IAM database auth is not supported for federation), so this
# is the one password-based database user: read-only, scoped to raw.
resource "random_password" "bq_reader" {
  length  = 24
  special = false
}

resource "google_sql_user" "bq_reader" {
  name     = "bq_reader"
  instance = google_sql_database_instance.raw.name
  password = random_password.bq_reader.result
}

resource "google_bigquery_connection" "cloudsql" {
  connection_id = "econ-cloudsql"
  location      = var.region
  description   = "Federated connection to the Cloud SQL raw landing zone"

  cloud_sql {
    instance_id = google_sql_database_instance.raw.connection_name
    database    = google_sql_database.econ.name
    type        = "POSTGRES"

    credential {
      username = google_sql_user.bq_reader.name
      password = random_password.bq_reader.result
    }
  }
}

# The connection gets a Google-managed service account that must be able
# to reach the Cloud SQL instance.
resource "google_project_iam_member" "bq_connection_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_bigquery_connection.cloudsql.cloud_sql[0].service_account_id}"
}

output "bq_connection_id" {
  description = "Fully-qualified connection id for EXTERNAL_QUERY"
  value       = "${var.project_id}.${var.region}.${google_bigquery_connection.cloudsql.connection_id}"
}
