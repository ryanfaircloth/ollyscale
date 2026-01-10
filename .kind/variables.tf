variable "strimzi_cluster_instance_version" {
  description = "Version of the tinyolly-instance Helm chart"
  type        = string
  default     = "*"
}

variable "gateway_dns_suffix" {
  description = "DNS suffix for gateway routes"
  type        = string
  default     = "tinyolly.test"
}

variable "bootstrap" {
  description = "Bootstrap mode - true for initial cluster creation (no HTTPRoutes), false for subsequent runs"
  type        = bool
  default     = false
}
