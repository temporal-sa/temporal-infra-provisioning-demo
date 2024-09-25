output "temporal_cloud_admin_user_id" {
  value = temporalcloud_user.namespace_admin
}

output "temporal_cloud_admin_user_state" {
  value = temporalcloud_user.namespace_admin.state
}
