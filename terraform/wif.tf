# Workload Identity Federation: GitHub Actions authenticates to GCP by
# exchanging its OIDC token for short-lived credentials of the
# econ-ingestion service account. No long-lived SA keys anywhere.

variable "github_repo" {
  type    = string
  default = "Nishanthkeelanur/eu-econ-data-platform"
}

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-actions"
  display_name              = "GitHub Actions"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-oidc"
  display_name                       = "GitHub OIDC"

  # Only workflows from this exact repository may authenticate.
  attribute_condition = "assertion.repository == \"${var.github_repo}\""

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
  }

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_member" "github_impersonation" {
  service_account_id = google_service_account.ingestion.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}

# The scheduled workflow also runs dataform, so the ingestion SA needs to
# create BigQuery jobs and write to the datasets.
resource "google_project_iam_member" "ingestion_bq_jobs" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.ingestion.email}"
}

resource "google_project_iam_member" "ingestion_bq_data" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.ingestion.email}"
}

# EXTERNAL_QUERY in the dataform raw layer goes through the connection.
resource "google_project_iam_member" "ingestion_bq_connection" {
  project = var.project_id
  role    = "roles/bigquery.connectionUser"
  member  = "serviceAccount:${google_service_account.ingestion.email}"
}

output "workload_identity_provider" {
  description = "Full provider name for google-github-actions/auth"
  value       = google_iam_workload_identity_pool_provider.github.name
}
