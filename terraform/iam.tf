# Service account used by the ingestion job (GitHub Actions / local runs).

resource "google_service_account" "ingestion" {
  account_id   = "econ-ingestion"
  display_name = "Economic data ingestion job"
}

# Connect to Cloud SQL through the connector...
resource "google_project_iam_member" "ingestion_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.ingestion.email}"
}

# ...and log in as an IAM database user.
resource "google_project_iam_member" "ingestion_sql_user" {
  project = var.project_id
  role    = "roles/cloudsql.instanceUser"
  member  = "serviceAccount:${google_service_account.ingestion.email}"
}
