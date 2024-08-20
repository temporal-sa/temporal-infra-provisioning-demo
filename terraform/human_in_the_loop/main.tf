terraform {
  required_providers {
    temporalcloud = {
      source = "temporalio/temporalcloud"
    }
    tls = {
      source = "hashicorp/tls"
    }
  }
}

provider "temporalcloud" {
	endpoint = var.endpoint # or env var `TEMPORAL_CLOUD_ENDPOINT`
	allow_insecure = var.allow_insecure # or env var `TEMPORAL_CLOUD_ALLOW_INSECURE`
}

provider "tls" {}

provider "random" {}

resource "random_id" "random_suffix" {
  byte_length = 4
}

resource "temporalcloud_user" "global_admin" {
	email          = "${var.prefix}-terraform-demo-${random_id.random_suffix.hex}@temporal.io"
  account_access = "admin"
}
