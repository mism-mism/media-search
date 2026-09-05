terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.40"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

data "google_project" "current" {
  project_id = var.project_id
}

variable "project_id" {
  type        = string
  description = "GCP project id"
}

variable "region" {
  type    = string
  default = "asia-northeast1"
}

variable "name_prefix" {
  type    = string
  default = "media-search"
}

variable "image" {
  type        = string
  description = "Container image (Artifact Registry) for Cloud Run"
  default     = ""
}

variable "embedder" {
  type    = string
  default = "local"
}

variable "allow_unauthenticated" {
  type        = bool
  description = "If true, public invoker (002 v0 / non-prod). If false, IAP mode (production)."
  default     = true
}

variable "iap_members" {
  type        = list(string)
  description = "IAP allowlist, e.g. [\"user:you@gmail.com\"]. Required when allow_unauthenticated=false."
  default     = []
}

locals {
  iap_mode     = !var.allow_unauthenticated
  deploy_run   = var.image != ""
  iap_sa_email = "service-${data.google_project.current.number}@gcp-sa-iap.iam.gserviceaccount.com"
}

resource "google_project_service" "services" {
  for_each = toset(compact([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
    local.iap_mode ? "iap.googleapis.com" : "",
  ]))
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "app" {
  location      = var.region
  repository_id = "${var.name_prefix}-repo"
  format        = "DOCKER"
  depends_on    = [google_project_service.services]
}

resource "google_storage_bucket" "media" {
  name                        = "${var.name_prefix}-${var.project_id}-media"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true
  depends_on                  = [google_project_service.services]
}

resource "google_service_account" "run" {
  account_id   = "${var.name_prefix}-run"
  display_name = "media-search Cloud Run"
}

resource "google_storage_bucket_iam_member" "run_media" {
  bucket = google_storage_bucket.media.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.run.email}"
}

resource "google_cloud_run_v2_service" "app" {
  count    = local.deploy_run ? 1 : 0
  name     = var.name_prefix
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  # IAP enablement: prefer `gcloud beta run services update --iap=enabled` or Console
  # after IAM below (provider attribute support varies). See docs/run-gcp-iap.md.

  template {
    service_account = google_service_account.run.email
    containers {
      image = var.image
      ports {
        container_port = 8080
      }
      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
      }
      env {
        name  = "EMBEDDER"
        value = var.embedder
      }
      env {
        name  = "MEDIA_BACKEND"
        value = "gcs"
      }
      env {
        name  = "GCS_BUCKET"
        value = google_storage_bucket.media.name
      }
      env {
        name  = "GCS_PREFIX"
        value = "incoming"
      }
      env {
        name  = "MEDIA_SEARCH_DATA"
        value = "/tmp/media-search"
      }
      env {
        name  = "MEDIA_SEARCH_DB"
        value = "/tmp/media-search/media-local-cos.db"
      }
      env {
        name  = "MEDIA_SEARCH_DB_GCS"
        value = "gs://${google_storage_bucket.media.name}/state/media-local-cos.db"
      }
      env {
        name  = "MEDIA_SEARCH_WORK"
        value = "/tmp/media-search/work"
      }
    }
    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }
  }

  depends_on = [google_project_service.services]

  lifecycle {
    precondition {
      condition     = var.allow_unauthenticated || length(var.iap_members) > 0
      error_message = "iap_members must be non-empty when allow_unauthenticated=false (production IAP)."
    }
  }
}

# 002 v0 / non-prod: public access
resource "google_cloud_run_v2_service_iam_member" "public" {
  count    = local.deploy_run && var.allow_unauthenticated ? 1 : 0
  name     = google_cloud_run_v2_service.app[0].name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Production IAP: only IAP service agent may invoke Cloud Run
resource "google_cloud_run_v2_service_iam_member" "iap_invoker" {
  count    = local.deploy_run && local.iap_mode ? 1 : 0
  name     = google_cloud_run_v2_service.app[0].name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${local.iap_sa_email}"
}

resource "google_iap_web_cloud_run_service_iam_member" "access" {
  for_each               = local.deploy_run && local.iap_mode ? toset(var.iap_members) : toset([])
  project                = tostring(data.google_project.current.number)
  location               = var.region
  cloud_run_service_name = google_cloud_run_v2_service.app[0].name
  role                   = "roles/iap.httpsResourceAccessor"
  member                 = each.value
}

output "artifact_registry" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}"
}

output "media_bucket" {
  value = google_storage_bucket.media.name
}

output "service_account" {
  value = google_service_account.run.email
}

output "cloud_run_uri" {
  value = try(google_cloud_run_v2_service.app[0].uri, null)
}

output "allow_unauthenticated" {
  value = var.allow_unauthenticated
}

output "iap_mode" {
  value = local.iap_mode
}
