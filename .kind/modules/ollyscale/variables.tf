
variable "gateway_dns_suffix" {
  description = "DNS suffix for gateway routes"
  type        = string
}

variable "custom_demo_frontend_image" {
  description = "Custom demo frontend image"
  type        = string
  default     = "ghcr.io/ryanfaircloth/ollyscale-demo-frontend"
}

variable "custom_demo_frontend_tag" {
  description = "Custom demo frontend tag"
  type        = string
  default     = "latest"
}

variable "custom_demo_backend_image" {
  description = "Custom demo backend image"
  type        = string
  default     = "ghcr.io/ryanfaircloth/ollyscale-demo-backend"
}

variable "custom_demo_backend_tag" {
  description = "Custom demo backend tag"
  type        = string
  default     = "latest"
}

variable "ai_agent_image" {
  description = "AI agent demo image"
  type        = string
  default     = "docker-registry.registry.svc.cluster.local:5000/ollyscale/demo-otel-agent"
}

variable "ai_agent_tag" {
  description = "AI agent demo tag"
  type        = string
  default     = "latest"
}

variable "ai_agent_chart_tag" {
  description = "AI agent demo chart tag"
  type        = string
  default     = "latest"
}
