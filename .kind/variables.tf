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

variable "use_local_registry" {
  description = "Use local registry (docker-registry.registry.svc.cluster.local:5000) instead of remote (ghcr.io)"
  type        = bool
  default     = false
}

# TinyOlly image versions (used when use_local_registry=true)
variable "tinyolly_tag" {
  description = "TinyOlly image tag"
  type        = string
  default     = "latest"
}

variable "opamp_tag" {
  description = "OpAMP server image tag"
  type        = string
  default     = "latest"
}

variable "demo_tag" {
  description = "Demo application image tag"
  type        = string
  default     = "latest"
}

variable "demo_agent_tag" {
  description = "Demo OTel agent image tag"
  type        = string
  default     = "latest"
}

# Demo application settings
variable "custom_demo_frontend_image" {
  description = "Custom demo frontend image repository (unified demo image)"
  type        = string
  default     = "docker-registry.registry.svc.cluster.local:5000/tinyolly/demo"
}

variable "custom_demo_frontend_tag" {
  description = "Custom demo frontend image tag"
  type        = string
  default     = "latest"
}

variable "custom_demo_backend_image" {
  description = "Custom demo backend image repository (unified demo image)"
  type        = string
  default     = "docker-registry.registry.svc.cluster.local:5000/tinyolly/demo"
}

variable "custom_demo_backend_tag" {
  description = "Custom demo backend image tag"
  type        = string
  default     = "latest"
}
