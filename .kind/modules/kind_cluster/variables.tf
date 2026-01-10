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
