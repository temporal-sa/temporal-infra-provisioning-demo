terraform {
  required_providers {
    temporalcloud = {
      source = "temporalio/temporalcloud"
    }
  }
}

provider "temporalcloud" {
	# Also can be set by environment variable `TEMPORAL_CLOUD_ENDPOINT`
	endpoint = var.endpoint
	# Also can be set by environment variable `TEMPORAL_CLOUD_ALLOW_INSECURE`
	allow_insecure = var.allow_insecure
}

// TODO: do we want to take arguments for each namespace or be declarative?
// whatever we decide, note it here in a comment. Generate certs? Put this in a
// module and have the the users call the module, the module creates the key
// for the namespace.
resource "temporalcloud_namespace" "terraform_test" {
	name               = "neil-dahlke-terraform-test"
	regions            = ["aws-us-west-2"]
	accepted_client_ca = base64encode(file("/Users/neildahlke/.temporal_certs/ca.pem"))
	retention_days     = 14
}

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