variable "name" {
  description = "Name of the kind cluster"
  type        = string
  default     = "tinyolly"
}

variable "kubeconfig_path" {
  description = "Path to the kubeconfig file"
  type        = string
  default     = null
}

variable "export_kubectl_conf" {
  description = "Whether to export the kubeconfig after cluster creation"
  type        = bool
  default     = true
}

variable "kafka_nodeport" {
  description = "NodePort for Kafka TLS traffic (container_port in Kind)"
  type        = number
  default     = 30994
}

variable "https_nodeport" {
  description = "NodePort for HTTPS traffic (container_port in Kind)"
  type        = number
  default     = 30943
}

variable "mgmt_https_nodeport" {
  description = "NodePort for management HTTPS traffic (container_port in Kind)"
  type        = number
  default     = 30949
}
