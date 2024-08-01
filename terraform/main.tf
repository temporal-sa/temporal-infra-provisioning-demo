terraform {
  required_providers {
    temporalcloud = {
      source = "temporalio/temporalcloud"
    }
  }
}

provider "temporalcloud" {
	endpoint = var.endpoint # or env var `TEMPORAL_CLOUD_ENDPOINT`
	allow_insecure = var.allow_insecure # or env var `TEMPORAL_CLOUD_ALLOW_INSECURE`
}

resource "temporalcloud_namespace" "terraform_test" {
	name               = "neil-dahlke-terraform-test"
	regions            = ["aws-us-west-2"]
	accepted_client_ca = base64encode(file("/Users/neildahlke/.temporal_certs/ca.pem"))
	retention_days     = 14
}

/*
resource "temporalcloud_namespace" "terraform_test2" {
	name               = "neil-dahlke-terraform-test2"
	regions            = ["aws-us-west-2"]
	accepted_client_ca = base64encode(file("/Users/neildahlke/.temporal_certs/ca.pem"))
	retention_days     = 14
}
*/

/*
resource "temporalcloud_user" "global_admin" {
  email          = "neil@dahlke.io"
  account_access = "admin"
}

// TODO
resource "temporalcloud_user" "namespace_admin" {
  email          = "developer@yourdomain.com"
  account_access = "developer"
  namespace_accesses = [
    {
      namespace  = temporalcloud_namespace.namespace.id
      permission = "admin"
    }
  ]
}
*/