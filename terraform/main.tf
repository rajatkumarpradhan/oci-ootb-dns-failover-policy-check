# OCI DNS Traffic Management (steering policy) + Health Checks monitor wiring.
# TEMPLATE ONLY: not plan/apply validated. No zone, policy, monitor or attachment
# was actually created; no failover was exercised. Provided as the native-service
# half of this project.

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
  }
}

provider "oci" {
  # Configure via environment (OCI_CLI_AUTH / config file) in a real deployment.
}

# Probe the primary endpoint so the steering policy can see its health.
resource "oci_health_checks_http_monitor" "primary" {
  compartment_id = var.compartment_ocid
  display_name   = "payments-primary-probe"
  protocol       = "HTTPS"
  path           = "/healthz"
  interval_in_seconds = 30
  timeout_in_seconds  = 10
  is_enabled          = true

  targets = [var.primary_endpoint]
}

# FAILOVER steering policy: priority 1 serves until the health check says down,
# then priority 2 takes over.
resource "oci_dns_steering_policy" "payments_failover" {
  compartment_id = var.compartment_ocid
  display_name   = "payments-failover"
  template       = "FAILOVER"
  ttl            = 60
  health_check_monitor_id = oci_health_checks_http_monitor.primary.id

  answers {
    name  = "primary-a"
    rtype = "A"
    rdata = var.primary_endpoint
    pool  = "primary"
  }

  answers {
    name  = "backup-a"
    rtype = "A"
    rdata = var.backup_endpoint
    pool  = "backup"
  }

  rules {
    rule_type = "PRIORITY"
    default_answer_data {
      answer_condition = "answer.isEnabled == true"
      should_keep      = true
    }
  }
}

# Bind the policy to the zone so it actually answers DNS queries.
resource "oci_dns_steering_policy_attachment" "payments_zone" {
  steering_policy_id = oci_dns_steering_policy.payments_failover.id
  zone_id            = var.zone_ocid
  display_name       = "payments-zone-attachment"
}
