variable "compartment_ocid" {
  type        = string
  description = "Compartment that owns the monitor, policy and attachment."
}

variable "zone_ocid" {
  type        = string
  description = "DNS zone the steering policy attaches to."
}

variable "primary_endpoint" {
  type        = string
  description = "Primary endpoint IP/host the monitor probes and priority 1 serves."
}

variable "backup_endpoint" {
  type        = string
  description = "Backup endpoint IP/host served after failover."
}
