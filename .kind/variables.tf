variable "gateway_dns_suffix" {
  description = "DNS suffix for gateway routes"
  type        = string
  default     = "ollyscale.test"
}

variable "bootstrap" {
  description = "Bootstrap mode - true for initial cluster creation (no HTTPRoutes), false for subsequent runs"
  type        = bool
  default     = false
}

variable "use_local_registry" {
  description = "Use local registry (docker-registry.registry.svc.cluster.local:5000) instead of remote (ghcr.io)"
  type        = bool
  default     = true
}

# OllyScale image versions - use "latest" for local builds
variable "ollyscale_tag" {
  description = "OllyScale API image tag"
  type        = string
  default     = "latest"
}

variable "webui_tag" {
  description = "OllyScale Web UI image tag"
  type        = string
  default     = "latest"
}

variable "opamp_tag" {
  description = "OpAMP server image tag"
  type        = string
  default     = "latest"
}

variable "ollyscale_chart_tag" {
  description = "Version of the OllyScale Helm chart to deploy (use current Chart.yaml version for local builds)"
  type        = string
  default     = "0.3.0"
}

variable "postgres_chart_tag" {
  description = "Version of the PostgreSQL Helm chart to deploy"
  type        = string
  default     = "0.1.0"
}

variable "ollyscale_otel_chart_tag" {
  description = "Version of the OllyScale OpenTelemetry Helm chart to deploy"
  type        = string
  default     = "0.1.0"
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

variable "ai_agent_chart_tag" {
  description = "AI agent demo chart tag"
  type        = string
  default     = "latest"
}

variable "ai_agent_image" {
  description = "AI agent demo image repository"
  type        = string
  default     = "docker-registry.registry.svc.cluster.local:5000/ollyscale/demo-otel-agent"
}

variable "ai_agent_tag" {
  description = "AI agent demo image tag"
  type        = string
  default     = "latest"
}

# Demo application settings
variable "custom_demo_frontend_image" {
  description = "Custom demo frontend image repository (unified demo image)"
  type        = string
  default     = "docker-registry.registry.svc.cluster.local:5000/ollyscale/demo"
}

variable "custom_demo_frontend_tag" {
  description = "Custom demo frontend image tag"
  type        = string
  default     = "latest"
}

variable "custom_demo_backend_image" {
  description = "Custom demo backend image repository (unified demo image)"
  type        = string
  default     = "docker-registry.registry.svc.cluster.local:5000/ollyscale/demo"
}

variable "custom_demo_backend_tag" {
  description = "Custom demo backend image tag"
  type        = string
  default     = "latest"
}

variable "ollyscale_demos_chart_tag" {
  description = "ollyscale-demos Helm chart version"
  type        = string
  default     = "latest"
}

variable "ollyscale_demos_image_tag" {
  description = "ollyscale-demos image tag"
  type        = string
  default     = "latest"
}
