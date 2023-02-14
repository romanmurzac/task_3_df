# Define the provider
terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "4.51.0"
    }
  }
}

# Define the provider options
provider "google" {
  project = var.project_id
  region = var.region
  zone = var.zone
  credentials = file("project-gcp-srp-hw-085eccd0cd34.json")
}

# Define the bucket
resource "google_storage_bucket" "bucket" {
  name = var.bucket_name
  location = var.location
}

# Archive the function files
data "archive_file" "source" {
  type = "zip"
  source_dir = "../function"
  output_path = "function.zip"
}

# Define the bucket content
resource "google_storage_bucket_object" "archive" {
  name = "source.zip"
  content_type = "application/zip"
  bucket = google_storage_bucket.bucket.name
  source = data.archive_file.source.output_path

  depends_on = [
    google_storage_bucket.bucket,
    data.archive_file.source]
}

# Define the Templates folder
resource "google_storage_bucket_object" "templates_folder" {
  name = "templates/"
  bucket = google_storage_bucket.bucket.name
  content = "Templates Cloud location"
  depends_on = [
    google_storage_bucket.bucket]
}

# Define the Temporary folder
resource "google_storage_bucket_object" "temp_folder" {
  name = "temp_dir/"
  bucket = google_storage_bucket.bucket.name
  content = "Temporary Cloud location"
  depends_on = [
    google_storage_bucket.bucket]
}

# Define the cloud function
resource "google_cloudfunctions_function" "function" {
  name = var.function_name
  description = "Function for HW tasks"
  runtime = "python310"
  available_memory_mb = 128
  source_archive_bucket = google_storage_bucket.bucket.name
  source_archive_object = google_storage_bucket_object.archive.name
  timeout = 120
  entry_point = "main"
  trigger_http = true

  environment_variables = {
    FUNCTION_REGION = var.region
    PROJECT_ID = var.project_id
    OUTPUT_TABLE = google_bigquery_table.table_cf.table_id
    OUTPUT_DATASET = google_bigquery_dataset.dataset_cf.dataset_id
    TOPIC_NAME = var.topic_name
  }
}

# Define the invoker for all users
resource "google_cloudfunctions_function_iam_member" "invoker" {
  cloud_function = google_cloudfunctions_function.function.name
  role = "roles/cloudfunctions.invoker"
  member = "allUsers"
}

# Define the CF dataset for BigQuery
resource "google_bigquery_dataset" "dataset_cf" {
  dataset_id = var.cf_dataset_id
  description = "BigQuery Dataset fo CF task"
  location = var.location
  default_table_expiration_ms = 3600000
}

# Define the DF dataset for BigQuery
resource "google_bigquery_dataset" "dataset_df" {
  dataset_id = var.df_dataset_id
  description = "BigQuery Dataset for DF task"
  location = var.location
  default_table_expiration_ms = 3600000
}

# Define the table for BigQuery
resource "google_bigquery_table" "table_cf" {
  table_id = var.sample_table_id
  dataset_id = google_bigquery_dataset.dataset_cf.dataset_id
  deletion_protection = false
  schema = file("../schemas/task-cf.json")
}

# Define the BigQuery table for success data
resource "google_bigquery_table" "success_table_df" {
  table_id = var.success_table_id
  dataset_id = google_bigquery_dataset.dataset_df.dataset_id
  deletion_protection = false
  schema = file("../schemas/task-df.json")
}

# Define the BigQuery table for error data
resource "google_bigquery_table" "error_table_df" {
  table_id = var.error_table_id
  dataset_id = google_bigquery_dataset.dataset_df.dataset_id
  deletion_protection = false
  schema = file("../schemas/task-df-error.json")
}

# Define the PubSub topic
resource "google_pubsub_topic" "topic_cf" {
  name = var.topic_name
  message_retention_duration = "86600s"
}

# Define the PubSub subscription
resource "google_pubsub_subscription" "subscription_cf" {
  name = var.subscription_name
  topic = google_pubsub_topic.topic_cf.name
  message_retention_duration = "1200s"
  retain_acked_messages = true
}

# Define the GitHub trigger
#resource "google_cloudbuild_trigger" "github_trigger" {
#  project = var.project_id
#  name = var.trigger_name
#  filename = "cloudbuild.yaml"
#
#  github {
#    owner = "romanmurzac"
#    name = "google-cloud"
#    push {
#      branch = "^main"
#    }
#  }
#}

# Define the Dataflow job
resource "google_dataflow_job" "dataflow_job_df" {
  name = var.dataflow_name
  template_gcs_path = "gs://bucket-gcp-srp-hw/templates/dataflow-gcp-srp-hw"
  temp_gcs_location = "gs://bucket-gcp-srp-hw/temp_dir"

}

