variable "project_id" {
  description = "GCP project id"
  type        = string
  default     = "eu-econ-data-platform"
}

variable "region" {
  description = "Default region for regional resources (Frankfurt - home of the ECB)"
  type        = string
  default     = "europe-west3"
}
