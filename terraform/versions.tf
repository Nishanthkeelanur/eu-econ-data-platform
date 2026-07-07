terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  backend "gcs" {
    bucket = "eu-econ-data-platform-tfstate"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region

  # Bill API calls (e.g. billingbudgets) to this project instead of relying
  # on the ADC default quota project.
  user_project_override = true
  billing_project       = var.project_id
}
