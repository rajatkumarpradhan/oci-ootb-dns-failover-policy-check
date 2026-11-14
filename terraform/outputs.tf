output "steering_policy_id" {
  value       = oci_dns_steering_policy.payments_failover.id
  description = "ID of the DNS steering policy (template output; never applied)."
}

output "health_monitor_id" {
  value       = oci_health_checks_http_monitor.primary.id
  description = "ID of the Health Checks monitor (template output; never applied)."
}
