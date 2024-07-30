terraform {
  required_providers {
    temporalcloud = {
      source = "temporalio/temporalcloud"
    }
  }
}

provider "temporalcloud" {
	# TODO:
	# Also can be set by environment variable `TEMPORAL_CLOUD_API_KEY`
	# api_key = "my-temporalcloud-api-key"

	# Also can be set by environment variable `TEMPORAL_CLOUD_ENDPOINT`
	endpoint = "saas-api.tmprl.cloud:443"

	# Also can be set by environment variable `TEMPORAL_CLOUD_ALLOW_INSECURE`
	allow_insecure = false
}

resource "temporalcloud_namespace" "namespace" {
	# TODO: take as an arg
	name               = "neil-dahlke-terraform-test"
	# TODO: take as an arg
	regions            = ["aws-us-west-2"]
	# accepted_client_ca = base64encode(file("ca.pem"))
	accepted_client_ca = base64encode(file("/Users/neildahlke/.temporal_certs/ca.pem"))
	retention_days     = 14
}

/*
// TODO

resource "temporalcloud_user" "global_admin" {
  email          = "neil.dahlke@temporal.io"
  account_access = "admin"
}

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