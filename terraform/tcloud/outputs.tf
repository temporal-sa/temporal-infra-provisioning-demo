output "terraform_test_namespace_name" {
  value = temporalcloud_namespace.terraform_test.name
}

output "terraform_test_namespace_endpoints" {
	  value = temporalcloud_namespace.terraform_test.endpoints
}

output "terraform_test_namespace_id" {
	  value = temporalcloud_namespace.terraform_test.id
}

output "terraform_test_client_certificate" {
  value = tls_self_signed_cert.terraform_test.cert_pem
}

output "terraform_test_private_key" {
  value     = tls_private_key.terraform_test.private_key_pem
  sensitive = true
}
