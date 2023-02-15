variable "project_id" {
  default = "project-work-gcp"
  type = string
  description = "Project ID"
}

variable "location" {
  default = "US"
  type = string
  description = "Project Location"
}

variable "region" {
  default = "us-central1"
  type = string
  description = "Project Region"
}

variable "zone" {
  default = "us-central1-c"
  type = string
  description = "Project Zone"
}

variable "bucket_name" {
  default = "bucket-work-gcp"
  type = string
  description = "Storage Bucket name"
}

variable "cf_dataset_id" {
  default = "cf_dataset_gcp_srp_hw"
  type = string
  description = "BigQuery CF Dataset ID"
}

variable "df_dataset_id" {
  default = "df_dataset_gcp_srp_hw"
  type = string
  description = "BigQuery DF Dataset ID"
}

variable "sample_table_id" {
  default = "table-gcp-srp-hw"
  type = string
  description = "BigQuery Table ID"
}

variable "success_table_id" {
  default = "table-gcp-srp-hw-success"
  type = string
  description = "BigQuery Table ID for success data"
}

variable "error_table_id" {
  default = "table-gcp-srp-hw-error"
  type = string
  description = "BigQuery Table ID for error data"
}

variable "function_name" {
  default = "function-gcp-srp-hw"
  type = string
  description = "Cloud Function name"
}

variable "topic_name" {
  default = "topic-gcp-srp-hw"
  type = string
  description = "PubSub topic name"
}

variable "subscription_name" {
  default = "subscription-gcp-srp-hw"
  type = string
  description = "PubSub Subscription name"
}

variable "trigger_name" {
  default = "trigger-gcp-srp-hw"
  type = string
  description = "Trigger for GitHub repository"
}

variable "dataflow_name" {
  default = "dataflow-gcp-srp-hw"
  type = string
  description = "Dataflow name"
}