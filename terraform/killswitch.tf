# Billing kill-switch: budget -> Pub/Sub -> Cloud Function that detaches
# billing from the project once cumulative monthly spend reaches the
# threshold, hard-stopping all billable services.
#
# Note: this is a backstop. The free trial itself never auto-charges -
# GCP pauses resources when credits run out unless explicitly upgraded.

variable "billing_account_id" {
  type    = string
  default = "010AE0-C59CC6-586C05"
}

variable "kill_threshold_gbp" {
  description = "Monthly spend (GBP) at which billing is detached"
  type        = string
  default     = "180"
}

resource "google_pubsub_topic" "billing_alerts" {
  name = "billing-alerts"
}

resource "google_billing_budget" "kill_switch" {
  billing_account = var.billing_account_id
  display_name    = "KILL SWITCH - detach billing at 100%"

  budget_filter {
    projects = ["projects/${var.project_id}"]
  }

  amount {
    specified_amount {
      currency_code = "GBP"
      units         = var.kill_threshold_gbp
    }
  }

  threshold_rules {
    threshold_percent = 0.5
  }
  threshold_rules {
    threshold_percent = 1.0
  }

  all_updates_rule {
    pubsub_topic   = google_pubsub_topic.billing_alerts.id
    schema_version = "1.0"
  }
}

# Runtime identity for the function: may read/detach project billing, nothing else.
resource "google_service_account" "killswitch" {
  account_id   = "billing-killswitch"
  display_name = "Billing kill-switch function"
}

resource "google_project_iam_member" "killswitch_billing" {
  project = var.project_id
  role    = "roles/billing.projectManager"
  member  = "serviceAccount:${google_service_account.killswitch.email}"
}

# Function source: zipped and uploaded to a private bucket.
data "archive_file" "killswitch_src" {
  type        = "zip"
  source_dir  = "${path.module}/functions/billing_killswitch"
  output_path = "${path.module}/.build/billing_killswitch.zip"
}

resource "google_storage_bucket" "functions" {
  name                        = "${var.project_id}-functions"
  location                    = var.region
  uniform_bucket_level_access = true
}

resource "google_storage_bucket_object" "killswitch_src" {
  name   = "billing_killswitch-${data.archive_file.killswitch_src.output_md5}.zip"
  bucket = google_storage_bucket.functions.name
  source = data.archive_file.killswitch_src.output_path
}

resource "google_cloudfunctions2_function" "killswitch" {
  name     = "billing-killswitch"
  location = var.region

  build_config {
    runtime     = "python312"
    entry_point = "stop_billing"
    source {
      storage_source {
        bucket = google_storage_bucket.functions.name
        object = google_storage_bucket_object.killswitch_src.name
      }
    }
  }

  service_config {
    max_instance_count    = 1
    available_memory      = "256M"
    timeout_seconds       = 60
    service_account_email = google_service_account.killswitch.email
    environment_variables = {
      GCP_PROJECT_ID = var.project_id
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.billing_alerts.id
    retry_policy   = "RETRY_POLICY_DO_NOT_RETRY"
  }
}
