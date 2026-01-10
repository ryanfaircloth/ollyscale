variable "strimzi_cluster_instance_version" {
  description = "Version of the tinyolly-instance Helm chart"
  type        = string
  default     = "*"
}
variable "endpoint" {
  description = "Kubernetes API server endpoint"
  type        = string
}

variable "cluster_ca_certificate" {
  description = "Kubernetes cluster CA certificate"
  type        = string
}

variable "client_certificate" {
  description = "Kubernetes client certificate"
  type        = string
}

variable "client_key" {
  description = "Kubernetes client key"
  type        = string
}

variable "flux_namespace" {
  description = "The namespace to deploy Flux resources into."
  type        = string
  default     = "flux-system"
}

variable "gateway_dns_suffix" {
  description = "DNS suffix for gateway routes"
  type        = string
  default     = "tinyolly.test"
}
