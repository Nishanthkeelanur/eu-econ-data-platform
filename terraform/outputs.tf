output "sql_connection_name" {
  description = "Cloud SQL connection name for the Python connector"
  value       = google_sql_database_instance.raw.connection_name
}

output "sql_database" {
  value = google_sql_database.econ.name
}

output "ingestion_service_account" {
  value = google_service_account.ingestion.email
}

output "ingestion_db_user" {
  description = "IAM database username of the ingestion service account"
  value       = google_sql_user.ingestion.name
}
