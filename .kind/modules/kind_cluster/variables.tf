variable "name" {
  description = "Name of the kind cluster"
  type        = string
  default     = "ollyscale"
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

variable "kafka_host_port" {
  description = "Host port for Kafka TLS traffic"
  type        = number
  default     = 9094
}

variable "https_nodeport" {
  description = "NodePort for HTTPS traffic (container_port in Kind)"
  type        = number
  default     = 30943
}

variable "https_host_port" {
  description = "Host port for HTTPS traffic"
  type        = number
  default     = 9443
}

variable "mgmt_https_nodeport" {
  description = "NodePort for management HTTPS traffic (container_port in Kind)"
  type        = number
  default     = 30949
}

variable "mgmt_https_host_port" {
  description = "Host port for management HTTPS traffic"
  type        = number
  default     = 49443
}

variable "registry_nodeport" {
  description = "NodePort for container registry (container_port in Kind)"
  type        = number
  default     = 30500
}

variable "registry_host_port" {
  description = "Host port for container registry"
  type        = number
  default     = 30500
}
